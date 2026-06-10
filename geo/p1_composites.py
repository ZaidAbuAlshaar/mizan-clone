# -*- coding: utf-8 -*-
"""
ميزان MIZAN — geo/p1_composites.py  (P1)
مركّبات NDVI/NDWI شهرية مقنّعة سحابياً من Sentinel-2 SR Harmonized + S2 Cloud Probability
للفترة 2017→2026، مع تصدير إلى Assets أو Drive (تأمين GEE quota — يُشغَّل يوم 0).

آلة الزمن (سنة 2016): S2 L2A غير متاح فوق الأردن قبل ~2017/2018 —
خيار --toa2016 يبني مركّب 2016 من S2 L1C (TOA) أو Landsat 8 (TOA NDVI كافٍ للعرض البصري).

أمثلة:
  python p1_composites.py --to drive --start-year 2017 --end-year 2026
  python p1_composites.py --to asset --start-year 2024 --end-year 2025
  python p1_composites.py --toa2016 --source s2   # مركّب 2016 لآلة الزمن
"""

import argparse

import ee

import config as C

# الباندات المطلوبة بعد القصّ (انعكاسية ÷10000)
_S2_BANDS = ["B2", "B3", "B4", "B8", "B11"]


def s2_cloudmasked(aoi, start, end, max_cloud_prob=C.S2_MAX_CLOUD_PROB):
    """مجموعة S2 SR مقنّعة سحابياً عبر ربط S2_CLOUD_PROBABILITY + تصفية SCL.

    يرجع ImageCollection بانعكاسية 0..1 وبالباندات _S2_BANDS.
    """
    s2 = (ee.ImageCollection(C.S2_SR)
          .filterBounds(aoi).filterDate(start, end))
    prob = (ee.ImageCollection(C.S2_CLOUDPROB)
            .filterBounds(aoi).filterDate(start, end))
    joined = ee.Join.saveFirst("cloud_prob").apply(
        primary=s2, secondary=prob,
        condition=ee.Filter.equals(leftField="system:index", rightField="system:index"))

    def _mask(img):
        img = ee.Image(img)
        cp = ee.Image(img.get("cloud_prob")).select("probability")
        scl = img.select("SCL")
        # استبعاد: ظل سحابة(3)، سحب(8,9)، سيروس(10) + احتمال سحابة فوق العتبة
        good = (cp.lt(max_cloud_prob)
                .And(scl.neq(3)).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10)))
        return (img.select(_S2_BANDS).divide(10000)
                .updateMask(good)
                .copyProperties(img, ["system:time_start"]))

    return ee.ImageCollection(joined).map(_mask)


def monthly_indices(aoi, year, month):
    """مركّب وسيط شهري: NDVI + NDWI (Gao — محتوى ماء النبات، B8/B11)."""
    start = ee.Date.fromYMD(year, month, 1)
    end = start.advance(1, "month")
    med = s2_cloudmasked(aoi, start, end).median()
    ndvi = med.normalizedDifference(["B8", "B4"]).rename("NDVI")
    ndwi = med.normalizedDifference(["B8", "B11"]).rename("NDWI")
    return (ndvi.addBands(ndwi)
            .set({"year": year, "month": month,
                  "system:time_start": start.millis(),
                  "mizan_product": "p1_monthly_indices"}))


def monthly_ndvi_collection(aoi, start_ym, n_months):
    """سلسلة NDVI شهرية بطول n_months ابتداءً من 'YYYY-MM' — تستخدمها P4."""
    y0, m0 = int(start_ym[:4]), int(start_ym[5:7])
    images = []
    for i in range(n_months):
        y, m = y0 + (m0 - 1 + i) // 12, (m0 - 1 + i) % 12 + 1
        images.append(monthly_indices(aoi, y, m))
    return ee.ImageCollection(images)


def toa_2016_composite(aoi, source="s2"):
    """مركّب صيف 2016 لآلة الزمن — TOA (لا L2A قبل 2017 فوق الأردن)."""
    if source == "s2":
        col = (ee.ImageCollection(C.S2_TOA)
               .filterBounds(aoi).filterDate("2016-06-01", "2016-09-01")
               .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20)))
        med = col.median().divide(10000)
        ndvi = med.normalizedDifference(["B8", "B4"]).rename("NDVI")
        rgb = med.select(["B4", "B3", "B2"])
    else:  # landsat 8 — SR Collection 2
        def _l8mask(img):
            qa = img.select("QA_PIXEL")
            good = qa.bitwiseAnd(0b11000).eq(0)  # سحب + ظلال
            sr = img.select("SR_B.").multiply(0.0000275).add(-0.2)
            return sr.updateMask(good)
        col = (ee.ImageCollection(C.LANDSAT8_SR)
               .filterBounds(aoi).filterDate("2016-06-01", "2016-09-01")
               .map(_l8mask))
        med = col.median()
        ndvi = med.normalizedDifference(["SR_B5", "SR_B4"]).rename("NDVI")
        rgb = med.select(["SR_B4", "SR_B3", "SR_B2"])
    return ndvi.addBands(rgb).set({"year": 2016, "mizan_product": "p1_timemachine_2016"})


def export_month(img, year, month, dest, aoi):
    """يبدأ مهمة تصدير لمركّب شهر واحد (Asset أو Drive)."""
    name = f"mizan_p1_{year}_{month:02d}"
    if dest == "asset":
        task = ee.batch.Export.image.toAsset(
            image=img.clip(aoi), description=name,
            assetId=f"{C.ASSET_ROOT}/p1/{name}",
            region=aoi, scale=10, maxPixels=1e13)
    else:
        task = ee.batch.Export.image.toDrive(
            image=img.clip(aoi), description=name,
            folder=C.DRIVE_FOLDER, fileNamePrefix=name,
            region=aoi, scale=10, maxPixels=1e13)
    task.start()
    return task


def main():
    ap = argparse.ArgumentParser(description="P1 — مركّبات NDVI/NDWI شهرية")
    ap.add_argument("--to", choices=["asset", "drive"], default="drive",
                    help="وجهة التصدير (تأمين quota يوم 0)")
    ap.add_argument("--start-year", type=int, default=C.P1_START_YEAR)
    ap.add_argument("--end-year", type=int, default=C.P1_END_YEAR)
    ap.add_argument("--national", action="store_true", help="bbox وطني بدل الأزرق")
    ap.add_argument("--toa2016", action="store_true",
                    help="تصدير مركّب 2016 (آلة الزمن) من TOA")
    ap.add_argument("--source", choices=["s2", "landsat8"], default="s2",
                    help="مصدر مركّب 2016")
    args = ap.parse_args()

    ee.Initialize(project=C.EE_PROJECT)
    bbox = C.AOI_JORDAN_BBOX if args.national else C.AOI_AZRAQ_BBOX
    aoi = ee.Geometry.Rectangle(bbox)

    if args.toa2016:
        img = toa_2016_composite(aoi, args.source)
        export_month(img, 2016, 0, args.to, aoi)
        print(f"بدأ تصدير مركّب 2016 ({args.source}, TOA) إلى {args.to} — تابع عبر ee.batch.Task.list()")
        return

    started = 0
    for year in range(args.start_year, args.end_year + 1):
        for month in range(1, 13):
            export_month(monthly_indices(aoi, year, month), year, month, args.to, aoi)
            started += 1
    print(f"بدأت {started} مهمة تصدير ({args.start_year}–{args.end_year}) إلى {args.to}.")
    print("ملاحظة quota: إن تجاوز أي تصدير 45 دقيقة → صغّر الدقة لـ20م أو قسّم الـ AOI (سجل المخاطر).")


if __name__ == "__main__":
    main()
