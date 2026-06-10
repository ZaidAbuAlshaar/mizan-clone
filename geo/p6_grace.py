# -*- coding: utf-8 -*-
"""
ميزان MIZAN — geo/p6_grace.py  (P6 — الاستخراج)
استخراج TWS الشهري من GRACE MASCON فوق **المنطقة الشرقية/الأردن** —
إشارة إقليمية ~300كم، لا تُنسب لحوض مفرد (قاعدة صياغة GRACE الملزمة).

التفكيك (مراجعة): GWS = TWS − SM
  • TWS: lwe_thickness (سم، anomaly مقابل baseline 2004–2009، ينتهي 9/2024 — يُقطع بشفافية)
  • SM: رطوبة التربة (profile) من GLDAS-2.2 CLSM (المعرّف المصحَّح) كـ anomaly بنفس الـ baseline
  • + عمود توكيد مستقل gws_gldas_cm من باند GWS_tavg مباشرة
فجوة GRACE→GRACE-FO‏ (2017-07→2018-05) تبقى ظاهرة في السلسلة (أشهر غائبة).

الإخراج: CSV + JSON مطابق لبنية data/demo/tws_series.json.

أمثلة:
  python p6_grace.py --export             # تصدير CSV إلى Drive (الأمتن)
  python p6_grace.py --local              # getInfo مباشر وكتابة CSV+JSON محلياً
  python p6_grace.py --from-csv downloads/mizan_p6_tws.csv   # بناء JSON من CSV منزَّل
  python p6_grace.py --gws-layer          # طبقة GWS_tavg (خريطة جوفية مشتقة من الجاذبية)
"""

import argparse
import csv
import json

import ee

import config as C


def _series_fc(region, sm_source="gldas"):
    """FeatureCollection شهري: month, tws_cm, sm_anom_cm, gws_cm, gws_gldas_cm."""
    mascon = ee.ImageCollection(C.GRACE_MASCON).select(C.GRACE_BAND)
    gldas = ee.ImageCollection(C.GLDAS)

    base_start, base_end = C.GRACE_BASELINE
    sm_band, gws_band = C.GLDAS_SM_BAND, C.GLDAS_GWS_BAND

    if sm_source == "era5":
        # بديل: رطوبة ERA5-Land (حجمية ×عمق الطبقات ≈ مم) — يُستخدم إن غاب باند GLDAS
        era5 = ee.ImageCollection(C.ERA5_LAND_MONTHLY)
        layers = ["volumetric_soil_water_layer_1", "volumetric_soil_water_layer_2",
                  "volumetric_soil_water_layer_3", "volumetric_soil_water_layer_4"]
        depths = [70, 210, 720, 1890]   # أعماق الطبقات بالمم

        def _era5_sm_mm(img):
            total = ee.Image.constant(0)
            for band, d in zip(layers, depths):
                total = total.add(ee.Image(img).select(band).multiply(d))
            return total.rename("sm_mm")
        sm_col = era5.map(_era5_sm_mm)
        sm_base = sm_col.filterDate(base_start, base_end).mean()
    else:
        sm_col = gldas.select(sm_band).map(lambda i: ee.Image(i).rename("sm_mm"))
        sm_base = sm_col.filterDate(base_start, base_end).mean()

    gws_base = gldas.select(gws_band).filterDate(base_start, base_end).mean()

    def _reduce(img, band, scale):
        return ee.Image(img).reduceRegion(
            reducer=ee.Reducer.mean(), geometry=region,
            scale=scale, bestEffort=True).get(band)

    def per_image(img):
        img = ee.Image(img)
        date = ee.Date(img.get("system:time_start"))
        m_start = ee.Date.fromYMD(date.get("year"), date.get("month"), 1)
        m_end = m_start.advance(1, "month")

        tws_cm = ee.Number(_reduce(img, C.GRACE_BAND, 55000))

        sm_month = sm_col.filterDate(m_start, m_end)
        sm_anom_cm = ee.Algorithms.If(
            sm_month.size().gt(0),
            ee.Number(_reduce(sm_month.mean().subtract(sm_base), "sm_mm", 27830))
            .divide(10),                       # مم → سم
            None)
        gws_cm = ee.Algorithms.If(
            ee.Algorithms.IsEqual(sm_anom_cm, None), None,
            tws_cm.subtract(ee.Number(sm_anom_cm)))

        gws_month = gldas.select(gws_band).filterDate(m_start, m_end)
        gws_gldas_cm = ee.Algorithms.If(
            gws_month.size().gt(0),
            ee.Number(_reduce(gws_month.mean().subtract(gws_base), gws_band, 27830))
            .divide(10),
            None)

        return ee.Feature(None, {
            "month": date.format("YYYY-MM"),
            "tws_cm": tws_cm,
            "sm_anom_cm": sm_anom_cm,
            "gws_cm": gws_cm,             # التفكيك TWS−SM (مراجعة)
            "gws_gldas_cm": gws_gldas_cm, # توكيد مستقل من GWS_tavg
        })

    return ee.FeatureCollection(mascon.map(per_image))


def rows_to_json(rows, out_json):
    """يحوّل صفوف CSV/getInfo إلى JSON مطابق لبنية tws_series.json."""
    series = []
    for r in sorted(rows, key=lambda x: x["month"]):
        if r["month"] > C.GRACE_ENDS_AT:   # قطع شفاف عند نهاية MASCON
            continue
        tws = r.get("tws_cm")
        gws = r.get("gws_cm")
        if tws is None or tws == "":
            continue
        item = {"month": r["month"], "tws_cm": round(float(tws), 2)}
        item["gws_cm"] = round(float(gws), 2) if gws not in (None, "") else None
        series.append(item)

    doc = {
        "scope": C.GRACE_SCOPE,
        "label_ar": C.GRACE_LABEL_AR,
        "label_en": C.GRACE_LABEL_EN,
        "unit": "cm",
        "resolution_note_ar": C.GRACE_RESOLUTION_NOTE_AR,
        "gap": C.GRACE_GAP,
        "ends_at": C.GRACE_ENDS_AT,
        "series": series,
        "is_demo": False,
    }
    with open(out_json, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False)
    print(f"كُتب {out_json} ({len(series)} شهراً، حتى {C.GRACE_ENDS_AT}).")


def export_gws_layer(region):
    """طبقة 'مياه جوفية مشتقة من الجاذبية' — متوسط GWS_tavg لآخر 12 شهراً."""
    last = (ee.ImageCollection(C.GLDAS).select(C.GLDAS_GWS_BAND)
            .filterDate("2025-06-01", "2026-06-01").mean())
    task = ee.batch.Export.image.toDrive(
        image=last.clip(region), description="mizan_p6_gws_layer",
        folder=C.DRIVE_FOLDER, fileNamePrefix="mizan_p6_gws_layer",
        region=region, scale=27830, maxPixels=1e10)
    task.start()
    print("بدأ تصدير طبقة GWS_tavg (لشاشة تفاصيل الحوض، بجانب المنحنى لا بديلاً عنه).")


def main():
    ap = argparse.ArgumentParser(description="P6 — استخراج GRACE/GLDAS (إقليمي)")
    ap.add_argument("--export", action="store_true", help="تصدير CSV إلى Drive")
    ap.add_argument("--local", action="store_true", help="getInfo مباشر (قد يكون بطيئاً)")
    ap.add_argument("--from-csv", type=str, default=None, help="بناء JSON من CSV منزَّل")
    ap.add_argument("--gws-layer", action="store_true")
    ap.add_argument("--sm-source", choices=["gldas", "era5"], default="gldas",
                    help="مصدر رطوبة التربة للتفكيك (era5 إن غاب باند GLDAS)")
    args = ap.parse_args()

    C.ensure_out_dirs()

    # وضع بلا GEE: بناء JSON من CSV منزَّل مسبقاً
    if args.from_csv:
        with open(args.from_csv, encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        rows_to_json(rows, C.OUT_TWS_JSON)
        return

    ee.Initialize(project=C.EE_PROJECT)
    region = ee.Geometry.Rectangle(C.GRACE_REGION_BBOX)

    if args.gws_layer:
        export_gws_layer(region)
        return

    fc = _series_fc(region, sm_source=args.sm_source)

    if args.export or not args.local:
        task = ee.batch.Export.table.toDrive(
            collection=fc, description="mizan_p6_tws",
            folder=C.DRIVE_FOLDER, fileNamePrefix="mizan_p6_tws",
            fileFormat="CSV",
            selectors=["month", "tws_cm", "sm_anom_cm", "gws_cm", "gws_gldas_cm"])
        task.start()
        print("بدأ تصدير سلسلة TWS/GWS إلى Drive — بعد التنزيل: python p6_grace.py --from-csv <الملف>")
        return

    # وضع محلي مباشر
    info = fc.getInfo()
    rows = [f["properties"] for f in info["features"]]
    with open(C.OUT_TWS_CSV, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["month", "tws_cm", "sm_anom_cm",
                                           "gws_cm", "gws_gldas_cm"])
        w.writeheader()
        for r in sorted(rows, key=lambda x: x["month"]):
            w.writerow(r)
    print(f"كُتب {C.OUT_TWS_CSV}")
    rows_to_json(rows, C.OUT_TWS_JSON)


if __name__ == "__main__":
    main()
