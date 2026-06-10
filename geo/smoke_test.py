# -*- coding: utf-8 -*-
"""
ميزان MIZAN — geo/smoke_test.py  (TM-03)
فحص الداتاستات الأربعة الحرجة فوق bbox الأزرق قبل أي بناء:
  1) GRACE MASCON  — باند lwe_thickness يرجع قيماً
  2) GLDAS-2.2 CLSM (المعرّف المصحَّح NASA/GLDAS/V022/CLSM/G025/DA1D) — باند GWS_tavg
  3) Sentinel-2 SR Harmonized — مشاهد متوفرة
  4) CHIRPS Daily — قيم مطرية
+ TM-10: CHIRPS sanity check — مجموع أمطار حزيران–آب فوق الأزرق لسنتين ≈ صفر
  (شاهد النفي المطري — أساس منطق P2 كله).

التشغيل:  python smoke_test.py            (يتطلب earthengine authenticate مسبقاً)
"""

import sys

import ee

import config as C

PASS, FAIL = "PASS [OK]", "FAIL [X]"


def _fmt(label, ok, detail):
    return f"  {PASS if ok else FAIL}  {label}: {detail}"


def check_mascon(aoi):
    """GRACE MASCON — متوسط lwe_thickness لآخر صورة فوق bbox الأزرق (قيمة إقليمية)."""
    col = ee.ImageCollection(C.GRACE_MASCON).select(C.GRACE_BAND)
    n = col.size().getInfo()
    img = ee.Image(col.sort("system:time_start", False).first())
    date = ee.Date(img.get("system:time_start")).format("YYYY-MM").getInfo()
    val = img.reduceRegion(
        reducer=ee.Reducer.mean(), geometry=aoi, scale=55000, bestEffort=True
    ).get(C.GRACE_BAND).getInfo()
    ok = (n > 0) and (val is not None)
    return ok, f"{n} صورة، آخرها {date}، lwe_thickness فوق الأزرق = {val} سم"


def check_gldas(aoi):
    """GLDAS CLSM — يتحقق من GWS_tavg ومن وجود باند رطوبة التربة المفترض للتفكيك."""
    col = ee.ImageCollection(C.GLDAS).filterDate("2024-01-01", "2024-02-01")
    n = col.size().getInfo()
    img = ee.Image(col.first())
    bands = img.bandNames().getInfo()
    has_gws = C.GLDAS_GWS_BAND in bands
    has_sm = C.GLDAS_SM_BAND in bands
    val = None
    if has_gws:
        val = img.select(C.GLDAS_GWS_BAND).reduceRegion(
            reducer=ee.Reducer.mean(), geometry=aoi, scale=27830, bestEffort=True
        ).get(C.GLDAS_GWS_BAND).getInfo()
    ok = (n > 0) and has_gws and (val is not None)
    sm_note = f"باند SM '{C.GLDAS_SM_BAND}' {'موجود' if has_sm else 'غير موجود — عدّل GLDAS_SM_BAND في config أو استخدم --sm-source era5 في p6'}"
    return ok, f"{n} صورة 1/2024، GWS_tavg = {val} مم · {sm_note}"


def check_s2(aoi):
    """Sentinel-2 SR — عدد مشاهد صيف 2025 فوق bbox الأزرق."""
    col = (ee.ImageCollection(C.S2_SR)
           .filterBounds(aoi)
           .filterDate("2025-06-01", "2025-09-01"))
    n = col.size().getInfo()
    return n > 0, f"{n} مشهداً صيف 2025"


def check_chirps(aoi):
    """CHIRPS — قيمة مطر يوم شتوي (يجب ألا تكون null)."""
    img = ee.Image(
        ee.ImageCollection(C.CHIRPS_DAILY).filterDate("2025-01-01", "2025-02-01").sum()
    )
    val = img.reduceRegion(
        reducer=ee.Reducer.mean(), geometry=aoi, scale=5566, bestEffort=True
    ).get("precipitation").getInfo()
    return val is not None, f"مجموع كانون2 2025 فوق الأزرق = {val} مم"


def chirps_summer_sanity(aoi, years=(2024, 2025)):
    """TM-10: مجموع أمطار حزيران–آب ≈ 0 — شاهد النفي المطري."""
    results, ok_all = [], True
    for y in years:
        total = ee.Image(
            ee.ImageCollection(C.CHIRPS_DAILY)
            .filterDate(f"{y}-06-01", f"{y}-09-01").sum()
        ).reduceRegion(
            reducer=ee.Reducer.mean(), geometry=aoi, scale=5566, bestEffort=True
        ).get("precipitation").getInfo()
        ok = (total is not None) and (total < C.P2_RAIN_MM)
        ok_all = ok_all and ok
        results.append(f"صيف {y}: {total} مم {'(< %.0f مم ✓)' % C.P2_RAIN_MM if ok else '(فوق العتبة!)'}")
    return ok_all, " · ".join(results)


def main():
    try:
        ee.Initialize(project=C.EE_PROJECT)
    except Exception:
        # محاولة بدون project (حسابات قديمة) ثم رسالة واضحة
        try:
            ee.Initialize()
        except Exception as exc:
            print("تعذّرت تهيئة Earth Engine — نفّذ أولاً: earthengine authenticate")
            print(f"التفاصيل: {exc}")
            sys.exit(2)

    aoi = ee.Geometry.Rectangle(C.AOI_AZRAQ_BBOX)
    print("=" * 72)
    print("ميزان MIZAN — TM-03 Smoke Test · الداتاستات الحرجة فوق bbox الأزرق")
    print(f"bbox: lon {C.AOI_AZRAQ_BBOX[0]}–{C.AOI_AZRAQ_BBOX[2]} · lat {C.AOI_AZRAQ_BBOX[1]}–{C.AOI_AZRAQ_BBOX[3]}")
    print("=" * 72)

    checks = [
        ("GRACE MASCON (lwe_thickness — إشارة إقليمية ~300كم)", check_mascon),
        (f"GLDAS-2.2 CLSM المصحَّح ({C.GLDAS})", check_gldas),
        ("Sentinel-2 SR Harmonized", check_s2),
        ("CHIRPS Daily", check_chirps),
        ("TM-10: شاهد النفي المطري (حزيران–آب ≈ 0)", chirps_summer_sanity),
    ]

    failures = 0
    for label, fn in checks:
        try:
            ok, detail = fn(aoi)
        except Exception as exc:
            ok, detail = False, f"استثناء: {exc}"
        if not ok:
            failures += 1
        print(_fmt(label, ok, detail))

    print("-" * 72)
    if failures == 0:
        print("النتيجة: كل الفحوص نجحت — Engine 1 وEngine 3 مثبتان قبل ساعة الصفر.")
    else:
        print(f"النتيجة: {failures} فحص/فحوص فشلت — عالجها قبل بدء P1 (كل مفاجأة هنا = 10 دقائق الآن بدل 4 ساعات داخل الحدث).")
    sys.exit(0 if failures == 0 else 1)


if __name__ == "__main__":
    main()
