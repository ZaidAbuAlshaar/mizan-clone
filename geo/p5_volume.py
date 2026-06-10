# -*- coding: utf-8 -*-
"""
ميزان MIZAN — geo/p5_volume.py  (P5)
تقدير الحجم المسحوب — **الإخراج نطاق لا رقم واحد** (مراجعة):

  Method A (الأرضية): area_ha × 6,000–9,000 م³/هكتار/سنة (= 600–900مم، افتراض معلَن).
  Method B (MODIS ET): MOD16A2GF للفترة 2018–2020 + MOD16A2 من 2021 (فخ التغطية
           الزمنية — فحص H4 مدمج: عدد الصور + نسبة البكسلات الصالحة فوق القناع).
  Method C (FAO-56): Kc(NDVI) × ET0(ERA5-Land) − مطر فعّال، ÷ كفاءة ريّ 0.6–0.85.

أمثلة:
  python p5_volume.py --fields-geojson outputs/fields.geojson --year 2025
  python p5_volume.py --fields-geojson outputs/fields.geojson --h4-only   # فحص بوابة H4 فقط
"""

import argparse
import json

import ee

import config as C
from p1_composites import monthly_indices


# ---------------------------------------------------------------------------
# Method A — محلي بالكامل
# ---------------------------------------------------------------------------

def method_a(features):
    """نطاق Method A من مساحات المضلعات."""
    total_ha = sum(f["properties"].get("area_ha") or 0.0 for f in features)
    lo = total_ha * C.METHOD_A_M3_PER_HA[0]
    hi = total_ha * C.METHOD_A_M3_PER_HA[1]
    return {
        "method": "A",
        "assumption_ar": f"{C.METHOD_A_M3_PER_HA[0]:,}–{C.METHOD_A_M3_PER_HA[1]:,} م³/هكتار/سنة (= 600–900مم) — افتراض معلَن",
        "total_ha": round(total_ha, 1),
        "m3_low": int(lo), "m3_high": int(hi),
    }


# ---------------------------------------------------------------------------
# Method B — MODIS ET + فحص H4
# ---------------------------------------------------------------------------

def _mod16_collection(year):
    """المجموعة الصحيحة حسب السنة: GF قبل 2021، الروتينية بعدها (فخ التغطية)."""
    ds = C.MOD16_GF if year < C.MOD16_SPLIT_YEAR else C.MOD16_ROUTINE
    return ee.ImageCollection(ds).select(C.MOD16_BAND) \
        .filterDate(f"{year}-01-01", f"{year+1}-01-01"), ds


def h4_coverage_check(mask_geom, years=(2018, 2019, 2020, 2021, 2024, 2025)):
    """بوابة H4: تغطية MOD16 الزمنية والمكانية فوق مزارع الأزرق."""
    report = []
    for y in years:
        col, ds = _mod16_collection(y)
        n = col.size().getInfo()
        valid_pct = None
        if n > 0:
            # نسبة البكسلات الصالحة فوق منطقة القناع لصورة صيفية
            img = ee.Image(col.filterDate(f"{y}-06-01", f"{y}-09-01").first())
            stats = ee.Image(img).mask().reduceRegion(
                reducer=ee.Reducer.mean(), geometry=mask_geom,
                scale=500, bestEffort=True).get(C.MOD16_BAND)
            v = stats.getInfo()
            valid_pct = round(v * 100, 1) if v is not None else None
        report.append({"year": y, "dataset": ds, "images": n,
                       "valid_px_pct_summer": valid_pct})
    return report


def method_b(features, year):
    """مجموع ET السنوي فوق المضلعات → م³ (8 أيام × 0.1 كغ/م²)."""
    col, ds = _mod16_collection(year)
    et_annual = col.sum().multiply(C.MOD16_SCALE_FACTOR)  # مم/سنة
    fc = ee.FeatureCollection([
        ee.Feature(ee.Geometry(f["geometry"]), {"fid": i})
        for i, f in enumerate(features)])
    rr = et_annual.reduceRegions(collection=fc, reducer=ee.Reducer.mean(), scale=500)
    info = rr.getInfo()

    total_m3 = 0.0
    misses = 0
    for feat in info["features"]:
        et_mm = feat["properties"].get(C.MOD16_BAND)
        fid = feat["properties"]["fid"]
        ha = features[fid]["properties"].get("area_ha") or 0.0
        if et_mm is None:
            misses += 1
            continue
        total_m3 += et_mm * 10.0 * ha     # مم × 10 = م³/هكتار
    return {
        "method": "B",
        "dataset": ds, "year": year,
        "note_ar": "ET فعلي من MODIS (~500م) — خشن نسبياً على حقول صغيرة، وفحص H4 يحكم اعتماده",
        "polygons_without_coverage": misses,
        "m3_total": int(total_m3),
    }


# ---------------------------------------------------------------------------
# Method C — FAO-56: Kc(NDVI) × ET0 − مطر فعّال، ÷ كفاءة ريّ
# ---------------------------------------------------------------------------

def method_c(features, aoi, year):
    """صافي/إجمالي احتياج الريّ الشهري المجموع سنوياً لكل مضلع → نطاق بالكفاءة."""
    fc = ee.FeatureCollection([
        ee.Feature(ee.Geometry(f["geometry"]), {"fid": i})
        for i, f in enumerate(features)])

    net_mm = {i: 0.0 for i in range(len(features))}   # صافي مم/سنة لكل مضلع
    for month in range(1, 13):
        start = ee.Date.fromYMD(year, month, 1)
        end = start.advance(1, "month")

        ndvi = monthly_indices(aoi, year, month).select("NDVI")
        # Kc خطي من NDVI (Kamble et al. 2013) مقصوص 0.15–1.20
        kc = (ndvi.multiply(C.KC_NDVI_A).add(C.KC_NDVI_B)
              .clamp(C.KC_CLAMP[0], C.KC_CLAMP[1]).rename("kc"))
        # ET0 من ERA5-Land (متر، سالب بالاصطلاح) → مم موجبة
        et0 = (ee.ImageCollection(C.ERA5_LAND_MONTHLY)
               .filterDate(start, end).first()
               .select(C.ERA5_PET_BAND).multiply(-1000).max(0).rename("et0"))
        rain = (ee.ImageCollection(C.CHIRPS_DAILY)
                .filterDate(start, end).sum()
                .multiply(C.EFFECTIVE_RAIN_COEF).rename("eff_rain"))
        # صافي الاحتياج = max(Kc·ET0 − مطر فعّال، 0)
        etc = kc.multiply(et0)
        net = etc.subtract(rain).max(0).rename("net_mm")

        rr = net.reduceRegions(collection=fc, reducer=ee.Reducer.mean(), scale=100)
        for feat in rr.getInfo()["features"]:
            v = feat["properties"].get("net_mm")
            if v is not None:
                net_mm[feat["properties"]["fid"]] += v
        print(f"  Method C: شهر {year}-{month:02d} تم")

    total_net_m3 = sum(
        net_mm[i] * 10.0 * (features[i]["properties"].get("area_ha") or 0.0)
        for i in range(len(features)))
    # الإجمالي المسحوب = الصافي ÷ كفاءة الريّ (0.6–0.85) — نطاق
    lo = total_net_m3 / C.IRRIGATION_EFF[1]
    hi = total_net_m3 / C.IRRIGATION_EFF[0]
    return {
        "method": "C",
        "year": year,
        "assumption_ar": (f"FAO-56: Kc = {C.KC_NDVI_A}·NDVI{C.KC_NDVI_B:+} · "
                          f"ET0 من ERA5-Land · مطر فعّال {C.EFFECTIVE_RAIN_COEF} · "
                          f"كفاءة ريّ {C.IRRIGATION_EFF[0]}–{C.IRRIGATION_EFF[1]}"),
        "net_m3": int(total_net_m3),
        "m3_low": int(lo), "m3_high": int(hi),
    }


def main():
    ap = argparse.ArgumentParser(description="P5 — تقدير الحجم (نطاق ثلاثي الطرق)")
    ap.add_argument("--fields-geojson", type=str, default=C.OUT_FIELDS)
    ap.add_argument("--year", type=int, default=C.P2_DEFAULT_YEAR)
    ap.add_argument("--national", action="store_true")
    ap.add_argument("--h4-only", action="store_true", help="فحص بوابة H4 فقط ثم خروج")
    ap.add_argument("--skip-b", action="store_true")
    ap.add_argument("--skip-c", action="store_true")
    ap.add_argument("--out", type=str, default=C.OUT_VOLUME)
    args = ap.parse_args()

    ee.Initialize(project=C.EE_PROJECT)
    C.ensure_out_dirs()

    with open(args.fields_geojson, encoding="utf-8") as fh:
        features = json.load(fh)["features"]
    bbox = C.AOI_JORDAN_BBOX if args.national else C.AOI_AZRAQ_BBOX
    aoi = ee.Geometry.Rectangle(bbox)

    if args.h4_only:
        print("بوابة H4 — تغطية MODIS ET فوق مزارع الأزرق:")
        for row in h4_coverage_check(aoi):
            print(f"  {row['year']} · {row['dataset']}: {row['images']} صورة، "
                  f"بكسلات صالحة صيفاً: {row['valid_px_pct_summer']}%")
        print("القرار المكتوب سلفاً: تغطية جيدة ✅→Method B لاحقاً · ❌→Method A نهائياً، لا نعود للموضوع.")
        return

    result = {
        "year": args.year,
        "methods": [method_a(features)],
        "is_demo": False,
    }
    if not args.skip_b:
        result["h4_coverage"] = h4_coverage_check(aoi)
        result["methods"].append(method_b(features, args.year))
    if not args.skip_c:
        result["methods"].append(method_c(features, aoi, args.year))

    # النطاق الموحَّد المعروض: من أدنى method A/C إلى أعلاهما (B توكيد لا حدّ)
    lows = [m["m3_low"] for m in result["methods"] if "m3_low" in m]
    highs = [m["m3_high"] for m in result["methods"] if "m3_high" in m]
    result["combined_range_m3"] = {"low": int(min(lows)), "high": int(max(highs))}
    result["framing_ar"] = "تقدير بنطاق معلَن الافتراضات — لا رقم واحد (قاعدة الشفافية)"

    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)
    print(f"كُتب {args.out}")
    rng = result["combined_range_m3"]
    print(f"النطاق الموحّد: {rng['low']:,} – {rng['high']:,} م³/سنة")


if __name__ == "__main__":
    main()
