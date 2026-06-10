# -*- coding: utf-8 -*-
"""
ميزان MIZAN — geo/p2_mask.py  (P2)
قناع الريّ v1 بالقواعد — "أخضر في صيف بلا مطر = ضخّ جوفي، لا تفسير آخر":

  mean(NDVI, حزيران–آب) ≥ 0.35
  AND sum(CHIRPS, حزيران–آب) < 10مم
  AND WorldCover ∈ {tree cover, shrubland, cropland, bare}   (الفلتر الموسَّع — الزيتون)
  AND خارج JRC Global Surface Water
  AND خارج مضلع محمية الأزرق الرطبة (data/demo/exclusions.geojson — مراجعة #10)

بوابة H6: إن لم يلتقط القناع مزارع الأزرق المعروفة → --ndvi 0.30/0.40 أو --window jul-aug.
إصلاح قنبلة P7: خيار --national يشغّل القناع وطنياً بدقة 100م (job تصدير ليلي واحد).

أمثلة:
  python p2_mask.py --year 2025 --to drive
  python p2_mask.py --year 2025 --national --to drive
  python p2_mask.py --year 2025 --bbox 35.90,31.51,36.20,31.81   # mini-AOI حول موقع تحقّق
"""

import argparse
import json
import os

import ee

import config as C
from p1_composites import monthly_indices


def _load_exclusions():
    """يقرأ مضلعات الاستبعاد (محمية الأزرق الرطبة RAMSAR + الواحة) كـ ee.Geometry."""
    if not os.path.exists(C.EXCLUSIONS_GEOJSON):
        print(f"تحذير: {C.EXCLUSIONS_GEOJSON} غير موجود — يُتابع بلا استبعاد المحمية!")
        return None
    with open(C.EXCLUSIONS_GEOJSON, encoding="utf-8") as fh:
        gj = json.load(fh)
    geoms = [ee.Geometry(f["geometry"]) for f in gj.get("features", [])]
    if not geoms:
        return None
    merged = geoms[0]
    for g in geoms[1:]:
        merged = merged.union(g, maxError=10)
    return merged


def summer_ndvi_mean(aoi, year, months):
    """متوسط NDVI لأشهر الصيف من المركّبات الشهرية المقنّعة سحابياً."""
    imgs = [monthly_indices(aoi, year, m).select("NDVI") for m in months]
    return ee.ImageCollection(imgs).mean().rename("NDVI_summer")


def summer_chirps_sum(year, months):
    """مجموع CHIRPS اليومي لأشهر الصيف (شاهد النفي المطري)."""
    start = ee.Date.fromYMD(year, months[0], 1)
    end = ee.Date.fromYMD(year, months[-1], 1).advance(1, "month")
    return (ee.ImageCollection(C.CHIRPS_DAILY)
            .filterDate(start, end).sum().rename("rain_summer"))


def build_irrigation_mask(aoi, year,
                          ndvi_t=C.P2_NDVI_T,
                          rain_mm=C.P2_RAIN_MM,
                          months=None,
                          use_exclusions=True):
    """يبني قناع الريّ v1 الثنائي (1 = رقعة مروية مشبوهة) فوق aoi لسنة معينة."""
    months = months or C.P2_SUMMER_MONTHS

    ndvi = summer_ndvi_mean(aoi, year, months)
    rain = summer_chirps_sum(year, months)

    # WorldCover — الفلتر الموسَّع {10 شجري، 20 شجيري، 40 محاصيل، 60 جرداء}
    wc = ee.Image(ee.ImageCollection(C.WORLDCOVER).first()).select("Map")
    wc_ok = wc.remap(C.WORLDCOVER_KEEP, [1] * len(C.WORLDCOVER_KEEP), 0)

    # خارج أي امتداد مائي تاريخي (JRC)
    jrc = ee.Image(C.JRC_WATER).select(C.JRC_BAND)
    outside_water = jrc.unmask(0).eq(0)

    mask = (ndvi.gte(ndvi_t)
            .And(rain.lt(rain_mm))
            .And(wc_ok)
            .And(outside_water))

    # استبعاد محمية الأزرق الرطبة — نباتات phreatophytes طبيعية خضراء صيفاً
    if use_exclusions:
        excl = _load_exclusions()
        if excl is not None:
            outside_reserve = ee.Image.constant(1).clip(excl).unmask(0).Not()
            mask = mask.And(outside_reserve)

    return mask.rename("irrigation_mask").selfMask()


def export_mask(mask, aoi, scale, dest, name):
    """تصدير القناع (Asset أو Drive)."""
    if dest == "asset":
        task = ee.batch.Export.image.toAsset(
            image=mask.clip(aoi).toByte(), description=name,
            assetId=f"{C.ASSET_ROOT}/p2/{name}",
            region=aoi, scale=scale, maxPixels=1e13)
    else:
        task = ee.batch.Export.image.toDrive(
            image=mask.clip(aoi).toByte(), description=name,
            folder=C.DRIVE_FOLDER, fileNamePrefix=name,
            region=aoi, scale=scale, maxPixels=1e13)
    task.start()
    return task


def main():
    ap = argparse.ArgumentParser(description="P2 — قناع الريّ v1 بالقواعد")
    ap.add_argument("--year", type=int, default=C.P2_DEFAULT_YEAR)
    ap.add_argument("--ndvi", type=float, default=C.P2_NDVI_T,
                    help=f"عتبة NDVI (بوابة H6: بدائل {C.P2_NDVI_T_ALT})")
    ap.add_argument("--rain", type=float, default=C.P2_RAIN_MM)
    ap.add_argument("--window", choices=["jun-aug", "jul-aug"], default="jun-aug",
                    help="بوابة H6: نافذة تموز–آب فقط كبديل")
    ap.add_argument("--national", action="store_true",
                    help="تشغيل وطني بدقة 100م (إصلاح قنبلة P7)")
    ap.add_argument("--bbox", type=str, default=None,
                    help="bbox مخصص lon1,lat1,lon2,lat2 (mini-AOI حول مواقع التحقّق)")
    ap.add_argument("--no-exclusions", action="store_true")
    ap.add_argument("--to", choices=["asset", "drive"], default="drive")
    args = ap.parse_args()

    ee.Initialize(project=C.EE_PROJECT)

    if args.bbox:
        bbox = [float(x) for x in args.bbox.split(",")]
        scale, tag = C.P2_SCALE_AOI, "miniaoi"
    elif args.national:
        bbox, scale, tag = C.AOI_JORDAN_BBOX, C.P2_SCALE_NATIONAL, "national"
    else:
        bbox, scale, tag = C.AOI_AZRAQ_BBOX, C.P2_SCALE_AOI, "azraq"

    aoi = ee.Geometry.Rectangle(bbox)
    months = C.P2_SUMMER_ALT if args.window == "jul-aug" else C.P2_SUMMER_MONTHS

    mask = build_irrigation_mask(
        aoi, args.year, ndvi_t=args.ndvi, rain_mm=args.rain,
        months=months, use_exclusions=not args.no_exclusions)

    # تقدير سريع للمساحة الملتقطة (معيار H6 الرقمي المساند للفحص البصري)
    area_ha = mask.multiply(ee.Image.pixelArea()).reduceRegion(
        reducer=ee.Reducer.sum(), geometry=aoi, scale=max(scale, 30),
        maxPixels=1e13, bestEffort=True).get("irrigation_mask")
    try:
        print(f"مساحة القناع التقريبية: {ee.Number(area_ha).divide(10000).getInfo():.0f} هكتار")
    except Exception as exc:
        print(f"تعذّر حساب المساحة الفوري (سيُحسب في P3): {exc}")

    name = f"mizan_p2_mask_{tag}_{args.year}_ndvi{int(args.ndvi*100)}"
    export_mask(mask, aoi, scale, args.to, name)
    print(f"بدأ تصدير القناع '{name}' بدقة {scale}م إلى {args.to}.")
    print("بوابة H6: تحقق بصرياً أن القناع يلتقط مزارع الأزرق المعروفة — "
          f"وإلا جرّب --ndvi {C.P2_NDVI_T_ALT[0]}/{C.P2_NDVI_T_ALT[1]} أو --window jul-aug أو Landsat.")


if __name__ == "__main__":
    main()
