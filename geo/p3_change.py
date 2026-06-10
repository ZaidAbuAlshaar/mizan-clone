# -*- coding: utf-8 -*-
"""
ميزان MIZAN — geo/p3_change.py  (P3)
كشف التغيّر: قناع P2 → reduceToVectors → مضلعات حقول بحقول:
  area_ha · first_seen_year · area_trajectory (هكتار/سنة) · flag (NEW/EXPANDING/STABLE) · expansion_rate

سلسلة first_seen من HLS v2 (HLSL30 + HLSS30) — تغطي 2016 قبل توفر S2 SR فوق الأردن،
وتجعل ذكر HLS في وثيقة التقديم صادقاً (متطلب Data explanation).

شرط الاستمرارية: سنة الظهور الأول = أول سنة تبدأ سلسلة نشاط **سنتين متتاليتين**
(ضد أخطاء البور/التذبذب — مراجعة).

التصنيف: NEW = first_seen ≥ 2018 (بعد الإغلاق القانوني 1992 وضمن حقبة الرصد) ·
EXPANDING = معدل توسّع > 25%/سنة · STABLE = الباقي.

أمثلة:
  python p3_change.py --year 2025 --to drive
  python p3_change.py --year 2025 --mask-asset projects/.../p2/mizan_p2_mask_azraq_2025_ndvi35
"""

import argparse

import ee

import config as C
from p2_mask import build_irrigation_mask


# ---------------------------------------------------------------------------
# HLS — NDVI صيفي سنوي (سلسلة first_seen)
# ---------------------------------------------------------------------------

def _hls_mask(img):
    """قناع سحب/ظلال من باند Fmask (بت1 سحابة، بت3 ظل)."""
    fmask = img.select("Fmask")
    good = fmask.bitwiseAnd(1 << 1).eq(0).And(fmask.bitwiseAnd(1 << 3).eq(0))
    return img.updateMask(good)


def hls_summer_ndvi(aoi, year):
    """متوسط NDVI حزيران–آب من HLSL30 (NIR=B5) + HLSS30 (NIR=B8A) مدمجين."""
    start, end = f"{year}-06-01", f"{year}-09-01"

    l30 = (ee.ImageCollection(C.HLS_L30)
           .filterBounds(aoi).filterDate(start, end).map(_hls_mask)
           .map(lambda i: i.normalizedDifference(["B5", "B4"]).rename("NDVI")))
    s30 = (ee.ImageCollection(C.HLS_S30)
           .filterBounds(aoi).filterDate(start, end).map(_hls_mask)
           .map(lambda i: i.normalizedDifference(["B8A", "B4"]).rename("NDVI")))

    return l30.merge(s30).mean().rename("NDVI").set({"year": year})


def yearly_active_area_images(aoi, years, ndvi_t=C.P3_HLS_NDVI_T):
    """لكل سنة: صورة مساحة النشاط (م²/بكسل حيث NDVI الصيفي ≥ العتبة)."""
    out = {}
    for y in years:
        active = hls_summer_ndvi(aoi, y).gte(ndvi_t)
        out[y] = active.multiply(ee.Image.pixelArea()).rename(f"a{y}")
    return out


# ---------------------------------------------------------------------------
# المضلعات + الحقول
# ---------------------------------------------------------------------------

def vectorize_mask(mask, aoi, scale):
    """reduceToVectors على القناع الثنائي → مضلعات متصلة (8-اتجاهات)."""
    fc = mask.reduceToVectors(
        geometry=aoi, scale=scale, geometryType="polygon",
        eightConnected=True, labelProperty="zone",
        bestEffort=False, maxPixels=1e13)

    def _area(f):
        ha = f.geometry().area(maxError=1).divide(10000)
        return f.set("area_ha", ha)

    fc = fc.map(_area).filter(ee.Filter.gte("area_ha", C.P3_MIN_POLY_HA))
    return fc


def annotate_trajectory(fc, area_images, years, scale=30):
    """يضيف لكل مضلع خصائص active_ha_YYYY (مساحة النشاط HLS بالسنين) دفعة واحدة."""
    stacked = ee.Image.cat([area_images[y] for y in years])
    sums = stacked.reduceRegions(
        collection=fc, reducer=ee.Reducer.sum(), scale=scale)

    def _to_ha(f):
        props = {}
        for y in years:
            props[f"active_ha_{y}"] = ee.Number(f.get(f"a{y}")).divide(10000)
        return f.set(props)

    return sums.map(_to_ha)


def annotate_flags(fc, years):
    """يحسب server-side: first_seen_year (بشرط سنتين متتاليتين) + expansion_rate + flag."""
    years_list = ee.List(years)
    n = len(years)

    def _per_feature(f):
        areas = ee.List([f.get(f"active_ha_{y}") for y in years])
        active = areas.map(lambda a: ee.Number(a).gte(C.P3_MIN_ACTIVE_HA))

        # أول سنة تبدأ سلسلة نشاط سنتين متتاليتين (شرط الاستمرارية ضد البور)
        idx = ee.List.sequence(0, n - 2)
        starts = idx.map(lambda i: ee.Algorithms.If(
            ee.Number(active.get(i)).multiply(
                ee.Number(active.get(ee.Number(i).add(1)))).eq(1),
            years_list.get(i), 9999))
        first_seen = ee.Number(starts.reduce(ee.Reducer.min()))
        # إن لم توجد سلسلة متتالية: نأخذ أول سنة نشاط مفردة (ونعلّمها)
        single_starts = ee.List.sequence(0, n - 1).map(lambda i: ee.Algorithms.If(
            ee.Number(active.get(i)).eq(1), years_list.get(i), 9999))
        first_single = ee.Number(single_starts.reduce(ee.Reducer.min()))
        persistent = first_seen.lt(9999)
        first_seen = ee.Number(ee.Algorithms.If(persistent, first_seen, first_single))

        # معدل التوسّع: نمو نسبي/سنة بين آخر سنتين نشطتين بقيمة معتبرة
        a_prev = ee.Number(areas.get(n - 2)).max(0.01)
        a_last = ee.Number(areas.get(n - 1))
        expansion = a_last.subtract(a_prev).divide(a_prev).max(0)

        flag = ee.Algorithms.If(
            first_seen.gte(C.FLAG_NEW_YEAR), "NEW",
            ee.Algorithms.If(expansion.gt(C.FLAG_EXPANDING_RATE), "EXPANDING", "STABLE"))

        trajectory = areas.map(lambda a: ee.Number(a).multiply(100).round().divide(100))

        return f.set({
            "first_seen_year": first_seen,
            "first_seen_persistent": persistent,   # False = ظهور مفرد بلا سنتين متتاليتين
            "expansion_rate": expansion.multiply(1000).round().divide(1000),
            "flag": flag,
            "area_trajectory": trajectory,
            "trajectory_years": years_list,
        })

    return fc.map(_per_feature)


def build_change_polygons(aoi, year, scale, ndvi_t=C.P2_NDVI_T, mask_asset=None):
    """التدفق الكامل: قناع → مضلعات → مسار سنوي HLS → أعلام."""
    if mask_asset:
        mask = ee.Image(mask_asset).selfMask()
    else:
        mask = build_irrigation_mask(aoi, year, ndvi_t=ndvi_t)

    fc = vectorize_mask(mask, aoi, scale)
    area_imgs = yearly_active_area_images(aoi, C.P3_YEARS)
    fc = annotate_trajectory(fc, area_imgs, C.P3_YEARS)
    fc = annotate_flags(fc, C.P3_YEARS)
    return fc


def main():
    ap = argparse.ArgumentParser(description="P3 — كشف التغيّر والمضلعات")
    ap.add_argument("--year", type=int, default=C.P2_DEFAULT_YEAR)
    ap.add_argument("--ndvi", type=float, default=C.P2_NDVI_T)
    ap.add_argument("--scale", type=int, default=C.P2_SCALE_AOI)
    ap.add_argument("--national", action="store_true")
    ap.add_argument("--mask-asset", type=str, default=None,
                    help="Asset قناع P2 مُصدَّر مسبقاً (يوفّر إعادة الحساب)")
    ap.add_argument("--to", choices=["asset", "drive"], default="drive")
    args = ap.parse_args()

    ee.Initialize(project=C.EE_PROJECT)
    bbox = C.AOI_JORDAN_BBOX if args.national else C.AOI_AZRAQ_BBOX
    scale = C.P2_SCALE_NATIONAL if args.national else args.scale
    aoi = ee.Geometry.Rectangle(bbox)

    fc = build_change_polygons(aoi, args.year, scale,
                               ndvi_t=args.ndvi, mask_asset=args.mask_asset)

    name = f"mizan_p3_fields_{'national' if args.national else 'azraq'}_{args.year}"
    if args.to == "asset":
        task = ee.batch.Export.table.toAsset(
            collection=fc, description=name, assetId=f"{C.ASSET_ROOT}/p3/{name}")
    else:
        task = ee.batch.Export.table.toDrive(
            collection=fc, description=name,
            folder=C.DRIVE_FOLDER, fileNamePrefix=name, fileFormat="GeoJSON")
    task.start()
    print(f"بدأ تصدير المضلعات '{name}' إلى {args.to} (GeoJSON).")
    print("التالي: p4_score.py يقرأ هذا الناتج (Asset أو ملف GeoJSON منزَّل من Drive).")


if __name__ == "__main__":
    main()
