# -*- coding: utf-8 -*-
"""
ميزان MIZAN — جالب مخزون المياه الجوفية GLDAS عبر Google Earth Engine
=====================================================================
يسحب سلسلة GWS_tavg الشهرية (GLDAS-2.2 CLSM — مخزون جوفي، مم) فوق منطقة
GRACE الإقليمية (شرق الأردن) → data/real/gws_series.json (is_real=true).

طبقة مستقلة عن GRACE: توكيد ثانٍ لنزيف الخزان من نموذج أرضي مدمج بالجاذبية.
يتطلب: earthengine authenticate ناجح + مشروع Cloud (EE_PROJECT).

تشغيل:  python geo/fetch_gldas_gws.py
"""
import json
import os
import sys

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass

import ee

from config import GLDAS, GLDAS_GWS_BAND, GRACE_REGION_BBOX, GRACE_LABEL_AR

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "data", "real", "gws_series.json")

START = "2003-02-01"          # بداية GLDAS-2.2 CLSM DA
SCALE_M = 27830               # ~0.25° — دقة GLDAS الأصلية


def init_ee():
    """تهيئة EE — يجرّب EE_PROJECT ثم أسماء المشاريع التلقائية الشائعة."""
    candidates = [p for p in [os.environ.get("EE_PROJECT")] if p]
    candidates += ["ee-abualshaarzaid", "mizan-vcoders"]
    last = None
    for proj in candidates:
        try:
            ee.Initialize(project=proj)
            print(f"  ✅ EE جاهز — مشروع: {proj}")
            return proj
        except Exception as e:
            last = e
    raise SystemExit(f"✗ تعذّرت تهيئة EE بأي مشروع ({candidates}): {last}")


def main():
    proj = init_ee()
    region = ee.Geometry.Rectangle(GRACE_REGION_BBOX)
    col = ee.ImageCollection(GLDAS).select(GLDAS_GWS_BAND).filterDate(START, "2026-12-31")

    # متوسط شهري إقليمي — حُسب كله على سيرفرات Google (استدعاء getInfo واحد)
    def month_feature(ym_start):
        start = ee.Date(ym_start)
        end = start.advance(1, "month")
        img = col.filterDate(start, end).mean()
        # -99999 قيمة حارسة للأشهر الفارغة (ذيل السلسلة قبل وصول بيانات GLDAS الجديدة)
        val = ee.Dictionary(img.reduceRegion(ee.Reducer.mean(), region, SCALE_M)) \
            .get(GLDAS_GWS_BAND, -99999)
        return ee.Feature(None, {"month": start.format("YYYY-MM"), "gws_mm": val})

    n_months = ee.Date("2026-06-01").difference(ee.Date(START), "month").floor()
    months = ee.List.sequence(0, n_months).map(
        lambda i: ee.Date(START).advance(i, "month").format("YYYY-MM-dd"))
    print(f"  جلب GWS الشهري من {GLDAS} فوق شرق الأردن ...", flush=True)
    feats = ee.FeatureCollection(months.map(month_feature)).getInfo()["features"]

    series = [
        {"month": f["properties"]["month"], "gws_mm": round(float(f["properties"]["gws_mm"]), 2)}
        for f in feats
        if f["properties"].get("gws_mm") is not None and f["properties"]["gws_mm"] > -90000
    ]
    if len(series) < 24:
        raise SystemExit(f"✗ سلسلة قصيرة بشكل مريب ({len(series)} شهراً) — لا كتابة")

    # اتجاه خطي (مم/سنة) بلا مكتبات — انحدار بسيط
    xs = list(range(len(series)))
    ys = [p["gws_mm"] for p in series]
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    trend_yr = round(slope * 12, 2)

    out = {
        "label_ar": "مخزون المياه الجوفية GLDAS (نموذج CLSM مدمج بـ GRACE)",
        "label_en": "GLDAS groundwater storage (CLSM, GRACE-DA)",
        "region_note_ar": GRACE_LABEL_AR,
        "unit": "mm",
        "series": series,
        "trend_mm_per_yr": trend_yr,
        "months": len(series),
        "source": f"{GLDAS} ({GLDAS_GWS_BAND}) via Google Earth Engine — project {proj}",
        "is_real": True,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print(f"  ✅ كُتب data/real/gws_series.json — {len(series)} شهراً · اتجاه {trend_yr:+.1f} مم/سنة")


if __name__ == "__main__":
    main()
