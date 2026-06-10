# -*- coding: utf-8 -*-
"""
ميزان MIZAN — مولّد البيانات التجريبية (demo data generator)
==============================================================
يولّد بيانات موسومة `is_demo: true` مطابقة لعقود CONTRACTS.md حرفياً.
حتمي بالكامل (seed=42) — نفس المخرجات في كل تشغيل.

قاعدة ملزمة: لا mock كحقيقي أبداً — كل ما هنا "demo data" حتى يصل GeoJSON
الحقيقي من pipeline GEE (geo/)، وعندها تُستبدل الملفات بلا تغيير في العقد.

الأرقام الواقعية الوحيدة المضمّنة هي ثوابت ملحق أ في plan.md (مصادر MWI/IWMI
/Jordan Times...) — وتُمرَّر كما هي في impact constants وخصائص الأحواض.

تشغيل:  python tools/generate_demo_data.py
"""
import json
import math
import random
import os

random.seed(42)

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "demo")
GENERATED_AT = "2026-06-10T12:00:00+03:00"  # ثابت — لا Date.now (حتمية المولد)

# ---------------------------------------------------------------- AOI الأزرق
BBOX = {"lon_min": 36.45, "lon_max": 37.30, "lat_min": 31.55, "lat_max": 32.25}

# محمية الأزرق الرطبة (RAMSAR) + الواحة — مضلع استبعاد تقريبي (مراجعة #10)
WETLAND_CENTER = (36.826, 31.838)
WETLAND_R = 0.028  # ~3 كم

# عناقيد المزارع التقريبية حول الأزرق (شمالي/شرقي/جنوبي)
CLUSTERS = [
    {"c": (36.86, 32.02), "r": 0.10, "n": 46, "label": "north"},
    {"c": (37.05, 31.86), "r": 0.09, "n": 38, "label": "east"},
    {"c": (36.90, 31.72), "r": 0.08, "n": 30, "label": "south"},
    {"c": (36.62, 31.95), "r": 0.07, "n": 16, "label": "west"},
    {"c": (37.18, 32.05), "r": 0.06, "n": 10, "label": "northeast"},
]

MONTHS_36 = [f"{y}-{m:02d}" for y in (2023, 2024, 2025) for m in range(1, 13)]


def in_wetland(lon, lat):
    return math.hypot(lon - WETLAND_CENTER[0], lat - WETLAND_CENTER[1]) < WETLAND_R + 0.012


def rect_polygon(lon, lat, w_deg, h_deg, angle_deg):
    """مستطيل مُدار حول مركزه."""
    a = math.radians(angle_deg)
    ca, sa = math.cos(a), math.sin(a)
    pts = []
    for dx, dy in [(-1, -1), (1, -1), (1, 1), (-1, 1), (-1, -1)]:
        x = dx * w_deg / 2,
        px = lon + (dx * w_deg / 2) * ca - (dy * h_deg / 2) * sa
        py = lat + (dx * w_deg / 2) * sa + (dy * h_deg / 2) * ca
        pts.append([round(px, 6), round(py, 6)])
    return [pts]


def circle_polygon(lon, lat, r_deg, n=24):
    """دائرة محور ريّ مركزي."""
    pts = []
    for i in range(n + 1):
        t = 2 * math.pi * i / n
        pts.append([round(lon + r_deg * math.cos(t), 6),
                    round(lat + r_deg * math.sin(t) * 0.85, 6)])  # تصحيح خط العرض تقريبي
    return [pts]


def ha_to_deg(area_ha):
    """تحويل مساحة (هكتار) إلى أبعاد درجات تقريبية عند خط عرض 32."""
    side_m = math.sqrt(area_ha * 10_000)
    deg_lat = side_m / 111_000
    deg_lon = side_m / (111_000 * math.cos(math.radians(32)))
    return deg_lon, deg_lat


def norm(x, ref):
    return max(0.0, min(1.0, x / ref))


# ---------------------------------------------------------------- توليد الحقول
def gen_fields():
    features = []
    idx = 0
    areas = []
    raw = []
    for cl in CLUSTERS:
        for _ in range(cl["n"]):
            for _attempt in range(20):
                lon = cl["c"][0] + random.uniform(-cl["r"], cl["r"])
                lat = cl["c"][1] + random.uniform(-cl["r"], cl["r"]) * 0.8
                if not in_wetland(lon, lat):
                    break
            area_ha = round(random.choices(
                [random.uniform(2, 8), random.uniform(8, 20), random.uniform(20, 60)],
                weights=[5, 3, 2])[0], 1)
            areas.append(area_ha)
            raw.append((lon, lat, area_ha, cl["label"]))
            idx += 1

    p95_area = sorted(areas)[int(len(areas) * 0.95)]

    for i, (lon, lat, area_ha, cluster) in enumerate(raw):
        fid = f"AZQ-{i+1:04d}"
        is_pivot = random.random() < 0.30  # محاور مركزية
        if is_pivot:
            r_deg = math.sqrt(area_ha * 10_000 / math.pi) / 111_000
            geom = circle_polygon(lon, lat, r_deg)
        else:
            w, h = ha_to_deg(area_ha)
            stretch = random.uniform(0.6, 1.7)
            geom = rect_polygon(lon, lat, w * stretch, h / stretch, random.uniform(-30, 30))

        first_seen = random.choices(
            [2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
            weights=[34, 6, 7, 8, 9, 10, 11, 10, 5])[0]
        old_field = first_seen <= 2017
        # حقول قديمة مستقرة: كثير منها بلا توسّع وبنشاط موسمي قصير (زيتون/أعلاف شتوية)
        if old_field and random.random() < 0.55:
            expansion = 0.0
            persistence = random.choice([3, 3, 4, 4, 5])
        else:
            expansion = round(max(0.0, random.gauss(0.08 if old_field else 0.20, 0.14)), 2)
            persistence = random.choices(
                [3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
                weights=[5, 6, 6, 5, 4, 4, 4, 3, 2, 2] if old_field else [1, 2, 3, 4, 5, 5, 4, 3, 2, 2])[0]
        anti_phase = round(min(0.98, max(0.2, random.gauss(0.74, 0.15))), 2)

        new_after_closure = first_seen >= 2018
        flag = "EXPANDING" if expansion > 0.25 else ("NEW" if new_after_closure else "STABLE")

        # صيغة P4 المعتمدة (CONTRACTS §3) — بلا طبقة تراخيص
        b = {
            "inside_protected_basin": 35.0,
            "new_after_closure": 25.0 if new_after_closure else 0.0,
            "persistence": round(15.0 * persistence / 12, 1),
            "area": round(12.5 * norm(area_ha, p95_area), 1),
            "expansion": round(12.5 * norm(expansion, 0.5), 1),
        }
        score = round(sum(b.values()))
        tier = "red" if score >= 70 else ("orange" if score >= 40 else "green")

        # سيناريوهات الحالة: معظمها new + أمثلة لدورة عمل المفتّش
        status = "new"
        r = random.random()
        if r < 0.06:
            status = "inspected"
        elif r < 0.09:
            status = "confirmed"
        elif r < 0.12:
            status = "cleared"

        # سلسلة NDVI/CHIRPS — بصمة الريّ المضادة للموسم
        series = []
        for mi, month in enumerate(MONTHS_36):
            m = int(month.split("-")[1])
            rain = round(max(0.0, random.gauss(14, 6)) if m in (1, 2, 3, 11, 12) else
                         (max(0.0, random.gauss(4, 3)) if m in (4, 10) else 0.0), 1)
            year = int(month.split("-")[0])
            active = year >= first_seen
            if active:
                # مروي: NDVI يبلغ ذروته صيفاً (عكس المطر تماماً)
                summer = 1.0 if m in (6, 7, 8) else (0.7 if m in (5, 9) else 0.35)
                base = 0.18 + (0.55 * summer * anti_phase)
            else:
                base = 0.10 + (rain / 200.0)
            ndvi = round(min(0.85, max(0.05, random.gauss(base, 0.03))), 2)
            series.append({"month": month, "ndvi": ndvi, "chirps_mm": rain})

        sm_rootzone = [round(min(0.45, max(0.05,
                       0.10 + (0.18 if m in (5, 6, 7, 8, 9) else 0.02) + random.gauss(0, 0.015))), 3)
                       for m in range(1, 13)]

        features.append({
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": geom},
            "properties": {
                "id": fid, "basin_id": "azraq",
                "area_ha": area_ha, "first_seen_year": first_seen,
                "flag": flag, "expansion_rate": expansion,
                "persistence_months": persistence, "anti_phase_score": anti_phase,
                "score": score, "score_breakdown": b, "tier": tier,
                "est_m3_low": int(area_ha * 6000), "est_m3_high": int(area_ha * 9000),
                "status": status, "cluster": cluster,
                "centroid": [round(lon, 5), round(lat, 5)],
                "ndvi_series": series, "sm_rootzone": sm_rootzone,
                "is_demo": True,
            },
        })

    features.sort(key=lambda f: -f["properties"]["score"])
    for rank, f in enumerate(features, 1):
        f["properties"]["rank"] = rank
    return {"type": "FeatureCollection",
            "name": "mizan_suspect_fields_DEMO",
            "features": features}


# ---------------------------------------------------------------- الأحواض
def gen_basins():
    """مضلعات تقريبية مبسّطة (is_demo_geometry) — النسب الحقيقية للأزرق وعمّان-الزرقا فقط (ملحق أ)."""
    def poly(coords):
        return {"type": "Polygon", "coordinates": [[[round(x, 3), round(y, 3)] for x, y in coords]]}

    basins = [
        {
            "id": "azraq", "name_ar": "حوض الأزرق", "name_en": "Azraq Basin",
            "exploitation_pct": 215, "exploitation_source": "MWI 2009 عبر IWMI",
            "closure_year": 1992, "well_level_drop_m": -20, "status": "modeled",
            "geometry": poly([(36.30, 32.40), (37.05, 32.55), (37.60, 32.20), (37.55, 31.55),
                              (37.05, 31.35), (36.55, 31.45), (36.25, 31.90), (36.30, 32.40)]),
        },
        {
            "id": "amman_zarqa", "name_ar": "حوض عمّان-الزرقا", "name_en": "Amman-Zarqa Basin",
            "exploitation_pct": 176, "exploitation_source": "MWI 2009 عبر IWMI",
            "closure_year": None, "well_level_drop_m": -35, "status": "secondary",
            "geometry": poly([(35.75, 32.40), (36.30, 32.40), (36.25, 31.90), (35.95, 31.85),
                              (35.72, 32.05), (35.75, 32.40)]),
        },
        {
            "id": "yarmouk", "name_ar": "حوض اليرموك", "name_en": "Yarmouk Basin",
            "exploitation_pct": None, "exploitation_source": None,
            "closure_year": None, "well_level_drop_m": -31, "status": "context",
            "geometry": poly([(35.65, 32.75), (36.40, 32.70), (36.30, 32.42), (35.75, 32.42),
                              (35.65, 32.75)]),
        },
        {
            "id": "dead_sea", "name_ar": "حوض البحر الميت", "name_en": "Dead Sea Basin",
            "exploitation_pct": None, "exploitation_source": None,
            "closure_year": None, "well_level_drop_m": -30, "status": "context",
            "geometry": poly([(35.45, 31.95), (35.95, 31.85), (35.90, 31.15), (35.50, 31.10),
                              (35.45, 31.95)]),
        },
        {
            "id": "jafr", "name_ar": "حوض الجفر", "name_en": "Jafr Basin",
            "exploitation_pct": None, "exploitation_source": None,
            "closure_year": None, "well_level_drop_m": None, "status": "context",
            "geometry": poly([(35.95, 31.10), (36.90, 31.30), (37.00, 30.40), (36.10, 30.20),
                              (35.95, 31.10)]),
        },
        {
            "id": "disi", "name_ar": "حوض الديسي", "name_en": "Disi Basin",
            "exploitation_pct": None, "exploitation_source": None,
            "closure_year": None, "well_level_drop_m": None, "status": "context",
            "geometry": poly([(35.80, 30.15), (36.80, 30.30), (36.95, 29.40), (35.95, 29.20),
                              (35.80, 30.15)]),
        },
    ]
    features = []
    for b in basins:
        geom = b.pop("geometry")
        b["is_demo_geometry"] = True
        features.append({"type": "Feature", "geometry": geom, "properties": b})
    return {"type": "FeatureCollection", "name": "jordan_basins_APPROX_DEMO", "features": features}


# ---------------------------------------------------------------- GRACE TWS
def month_range(y0, m0, y1, m1):
    y, m = y0, m0
    while (y, m) <= (y1, m1):
        yield y, m
        m += 1
        if m > 12:
            m, y = 1, y + 1


def gen_tws():
    series = []
    t = 0
    for y, m in month_range(2002, 4, 2024, 9):
        month = f"{y}-{m:02d}"
        years_since = t / 12.0
        # اتجاه هابط يتسارع بعد 2008 → ~ −19سم عند 2024 (شكل توضيحي يطابق الاتجاه المنشور)
        trend = -0.45 * years_since - 0.022 * max(0.0, years_since - 6) ** 2
        seasonal = 2.6 * math.cos(2 * math.pi * (m - 2.5) / 12)
        noise = random.gauss(0, 0.55)
        tws = round(trend + seasonal + noise + 2.0, 2)
        # GWS = TWS − رطوبة تربة (موسمية أعلى) → منحنى أنعم وأشد هبوطاً
        sm_seasonal = 1.9 * math.cos(2 * math.pi * (m - 2.0) / 12)
        gws = round(tws - sm_seasonal - random.gauss(0, 0.25), 2)
        in_gap = ("2017-07" <= month <= "2018-05")
        series.append({"month": month,
                       "tws_cm": None if in_gap else tws,
                       "gws_cm": None if in_gap else gws})
        t += 1
    return {
        "scope": "regional_east_jordan",
        "label_ar": "منحنى GRACE للمنطقة الشرقية/الأردن",
        "label_en": "GRACE curve — East Jordan region",
        "unit": "cm",
        "resolution_note_ar": "إشارة إقليمية ~300كم — لا تُنسب لحوض مفرد",
        "gap": ["2017-07", "2018-05"],
        "ends_at": "2024-09",
        "series": series,
        "is_demo": True,
    }


def gen_forecast(tws):
    last = [p for p in tws["series"] if p["tws_cm"] is not None][-1]
    last_val = last["tws_cm"]
    fc = []
    i = 1
    for y, m in month_range(2024, 10, 2035, 12):
        years = i / 12.0
        yhat = round(last_val - 1.05 * years + 1.8 * math.cos(2 * math.pi * (m - 2.5) / 12) * 0.4, 2)
        band = round(0.6 + 1.1 * years / 11.0 * 4, 2)
        fc.append({"month": f"{y}-{m:02d}", "yhat": yhat,
                   "lo": round(yhat - band, 2), "hi": round(yhat + band, 2)})
        i += 1
    return {
        "basin_id": "azraq",
        "grace_forecast": {
            "label_ar": "تنبّؤ Prophet — إشارة إقليمية مساندة",
            "series": fc,
            "backtest_mae_cm": 1.3,
            "backtest_note_ar": "حجب آخر 24 شهراً وإعادة التنبؤ بها (توضيحي)",
        },
        "well_level": {
            "drop_2000_2017_m": -20,
            "rate_m_per_yr": -1.1,
            "critical_year_low": 2031,
            "critical_year_high": 2035,
            "threshold_note_ar": "عتبة توضيحية: عمق ضخ اقتصادي إضافي −15م من منسوب 2017",
            "threshold_note_en": "Illustrative threshold: additional −15m economic pumping depth from 2017 level",
            "source_note_ar": "المنسوب والاتجاه من قياسات آبار الوزارة (ملحق أ) — الاستقراء والنطاق demo",
        },
        "is_demo": True,
    }


# ---------------------------------------------------------------- P7 التحقّق
def gen_validation():
    sites = [
        {"id": "wadi_as_seer", "name_ar": "وادي السير", "name_en": "Wadi As-Seer",
         "lon": 35.817, "lat": 31.945, "date": "2025",
         "detail_ar": "بئر بعمق 15م بمضختين غاطستين >500 م³/يوم — بيان رسمي MWI",
         "detail_en": "15m-deep well, two submersible pumps, >500 m³/day — official MWI statement",
         "source": "MWI (بيان رسمي)", "scope": "out_of_methodology",
         "out_reason_ar": "غرب عمّان — منطقة مطرية/حضرية خارج منطق الصحراء",
         "out_reason_en": "West Amman — rainfed/urban zone outside desert logic",
         "hit": None},
        {"id": "kafrein_swaimeh", "name_ar": "الكفرين/سويمة — 8 آبار", "name_en": "Kafrein/Sweimeh — 8 wells",
         "lon": 35.62, "lat": 31.77, "date": "2025-11",
         "detail_ar": "8 آبار بقدرة 5,000 م³/ساعة + 3.8كم كهرباء (11/2025)",
         "detail_en": "8 wells at 5,000 m³/hr + 3.8km power lines (11/2025)",
         "source": "رؤيا نيوز (PDF محفوظ)", "scope": "out_of_methodology",
         "out_reason_ar": "غور مروي بقناة الملك عبدالله — مياه سطحية متاحة، منطق «أخضر+صفر مطر» لا ينطبق",
         "out_reason_en": "Irrigated Jordan Valley (King Abdullah Canal) — surface water available",
         "hit": None},
        {"id": "kafrein_17", "name_ar": "الكفرين — 17 بئراً", "name_en": "Kafrein — 17 wells",
         "lon": 35.61, "lat": 31.79, "date": "2025-05",
         "detail_ar": "ضبط 17 بئراً غير شرعي (5/2025)",
         "detail_en": "17 illegal wells sealed (5/2025)",
         "source": "وطنا نيوز (PDF محفوظ)", "scope": "out_of_methodology",
         "out_reason_ar": "غور مروي — مياه سطحية متاحة",
         "out_reason_en": "Irrigated valley — surface water available",
         "hit": None},
        {"id": "khan_zabib", "name_ar": "خان الزبيب", "name_en": "Khan Az-Zabib",
         "lon": 36.05, "lat": 31.66, "date": "2025-08",
         "detail_ar": "حملة إنفاذ موثّقة (8/2025) — بادية وسطى",
         "detail_en": "Documented enforcement campaign (8/2025) — central Badia",
         "source": "صراحة نيوز (PDF محفوظ)", "scope": "in_methodology", "hit": True},
        {"id": "jafr", "name_ar": "الجفر", "name_en": "Al-Jafr",
         "lon": 36.21, "lat": 30.30, "date": "2025",
         "detail_ar": "بئر بعمق 300م — صحراء الجفر",
         "detail_en": "300m-deep well — Jafr desert",
         "source": "أخبار محلية (PDF محفوظ)", "scope": "in_methodology", "hit": True},
        {"id": "zarqa", "name_ar": "الزرقاء", "name_en": "Zarqa",
         "lon": 36.09, "lat": 32.07, "date": "2026-02",
         "detail_ar": "حملة إنفاذ (2/2026)",
         "detail_en": "Enforcement campaign (2/2026)",
         "source": "رؤيا نيوز (PDF محفوظ)", "scope": "in_methodology", "hit": True},
    ]
    for s in sites:
        s["coords_note"] = "إحداثيات تقريبية لمركز المنطقة"
    return {
        "threshold_km": 5,
        "threshold_note_ar": "الموقع يُحتسب تطابقاً إذا وقع ضمن ≤5كم من مضلع 🔴 — عتبة معلَنة سلفاً",
        "threshold_note_en": "A site counts as a hit if within ≤5km of a red polygon — pre-declared threshold",
        "sites": sites,
        "stats": {
            "in_scope": 3, "hits": 3,
            "red_area_pct": 2.6,
            "lift": 38,
            "lift_note_ar": "(نسبة الالتقاط ÷ نسبة المساحة الحمراء) — null model ضد تهمة «لوّنتم كل الخريطة»",
            "precision_at_20": 0.70,
            "precision_note_ar": "توضيحي — يُستبدل بالرقم الفعلي من تشغيل P7 يوم الحدث",
            "framing_ar": "تطابق حالات (case-study concordance) — لا precision/recall إحصائي على عيّنة إخبارية منحازة",
            "framing_en": "Case-study concordance — not statistical precision/recall on a biased news sample",
            "mini_aoi_note_ar": "المواقع داخل المنهجية تُفحص بقناع mini-AOI حول كل موقع (تشغيل وطني بدقة مخفّضة كخيار أقوى)",
        },
        "is_demo": True,
    }


# ---------------------------------------------------------------- الأثر
def gen_impact(fields):
    props = [f["properties"] for f in fields["features"]]
    low = sum(p["est_m3_low"] for p in props)
    high = sum(p["est_m3_high"] for p in props)
    mid = (low + high) // 2
    return {
        "detected_fields": len(props),
        "detected_total_ha": round(sum(p["area_ha"] for p in props), 1),
        "detected_total_m3_low": low,
        "detected_total_m3_mid": mid,
        "detected_total_m3_high": high,
        "scenarios": {"conservative": 0.35, "expected": 0.55},
        "scenario_note_ar": "معدل تأكيد التفتيش — افتراض معلَن قابل للتحريك (مراجعة: نطاق لا رقم واحد)",
        "constants": {
            "people_per_mcm": 3730,
            "people_equation_note_ar": "معادلة الوزارة: 42.9 م.م³ ≈ 160 ألف شخص → 1 مليون م³ ≈ ~3,730 شخصاً لسنة",
            "desal_usd_low": 0.5, "desal_usd_high": 0.7,
            "carrier_mcm": 300, "carrier_cost_usd_bn": 6,
            "overdraft_mcm": 205,
            "overdraft_vs_carrier_pct": 68,
            "manual_2023_24": {"wells": 201, "mcm": 62, "usd_m_low": 31, "usd_m_high": 43},
            "wells_sealed_since_2013": 1593,
            "avg_sealed_well_m3": 308000,
            "avg_sealed_well_note_ar": "متوسط البئر المُغلَق في حملات الإغلاق 2023/24 — عيّنة منحازة للكبار، لا يُضرب ×1500",
            "scarcity_m3_capita": 61,
            "national_abstraction_pct": 150,
            "azraq_pct": 215, "amman_zarqa_pct": 176,
        },
        "is_demo": True,
    }


# ---------------------------------------------------------------- دفتر الميزان
def gen_ledger(impact):
    detected_mcm = round(impact["detected_total_m3_mid"] / 1e6, 1)
    grace_loss = 58.0   # توضيحي
    licensed = 24.0     # توضيحي
    recharge = 22.0     # توضيحي
    unknown = round(grace_loss + recharge - licensed - detected_mcm, 1)
    return {
        "basin_id": "azraq",
        "title_ar": "دفتر الميزان — Mass-Balance Audit",
        "title_en": "The Mizan Ledger — Mass-Balance Audit",
        "explain_ar": "الكفة الأولى: فقد الكتلة الإقليمي من GRACE. الكفة الثانية: ما نستطيع تفسيره (سحب موثّق + ET الحقول المكتشفة). الفجوة = «العجز المجهول» الذي يطارده ميزان — نفس منطق Gropius 2022 كشاشة حية.",
        "explain_en": "Scale 1: regional mass loss from GRACE. Scale 2: what we can explain (documented abstraction + detected-field ET). The gap is the 'unknown deficit' MIZAN hunts — Gropius 2022 logic as a live screen.",
        "left_scale": {
            "label_ar": "ما يقوله الميزان الفضائي (إقليمي)",
            "grace_regional_loss_mcm": grace_loss,
            "recharge_mcm": recharge,
            "total_demand_mcm": round(grace_loss + recharge, 1),
        },
        "right_scale": {
            "label_ar": "ما نستطيع تفسيره",
            "documented_abstraction_mcm": licensed,
            "detected_fields_et_mcm": detected_mcm,
        },
        "unknown_deficit_mcm": unknown,
        "method_note_ar": "كل أرقام هذا الدفتر توضيحية (demo) — البنية والمعادلة هما المنتج؛ تُملأ من GRACE وP5 يوم الحدث",
        "is_demo": True,
    }


# ---------------------------------------------------------------- آلة الزمن
def gen_timemachine(fields):
    years = {}
    for y in range(2016, 2027):
        vis = [f["properties"] for f in fields["features"] if f["properties"]["first_seen_year"] <= y]
        years[str(y)] = {
            "fields_visible": len(vis),
            "total_ha": round(sum(p["area_ha"] for p in vis), 1),
            "est_m3_mid": int(sum((p["est_m3_low"] + p["est_m3_high"]) / 2 for p in vis)),
        }
    return {
        "years": years,
        "note_ar": "إعادة عرض المتجهات حسب سنة الظهور الأول (S2 L2A من 2017؛ سنة 2016 من TOA/Landsat في النسخة الحقيقية)",
        "is_demo": True,
    }


# ---------------------------------------------------------------- exclusions
def gen_exclusions():
    pts = []
    for i in range(33):
        t = 2 * math.pi * i / 32
        pts.append([round(WETLAND_CENTER[0] + WETLAND_R * math.cos(t), 5),
                    round(WETLAND_CENTER[1] + WETLAND_R * math.sin(t) * 0.85, 5)])
    return {
        "type": "FeatureCollection",
        "name": "exclusion_masks_DEMO",
        "features": [{
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [pts]},
            "properties": {
                "id": "azraq_wetland_ramsar",
                "name_ar": "محمية الأزرق الرطبة (RAMSAR) + الواحة",
                "name_en": "Azraq Wetland Reserve (RAMSAR) + oasis",
                "reason_ar": "نباتات phreatophytes طبيعية خضراء صيفاً بمياه جوفية ضحلة — تُستبعد من P2 (مراجعة)",
                "is_demo": True,
            },
        }],
    }


# ---------------------------------------------------------------- main
def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    fields = gen_fields()
    basins = gen_basins()
    tws = gen_tws()
    forecast = gen_forecast(tws)
    validation = gen_validation()
    impact = gen_impact(fields)
    ledger = gen_ledger(impact)
    timemachine = gen_timemachine(fields)
    exclusions = gen_exclusions()

    alerts = {
        "alerts": [
            {k: f["properties"][k] for k in
             ("id", "rank", "score", "tier", "area_ha", "first_seen_year", "flag",
              "est_m3_low", "est_m3_high", "status", "centroid")}
            for f in fields["features"][:20]
        ],
        "is_demo": True,
    }

    meta = {
        "data_mode": "demo",
        "generated_at": GENERATED_AT,
        "generator_version": "1.0.0",
        "note_ar": "بيانات تجريبية موسومة — تُستبدل بمخرجات pipeline GEE الحقيقية بلا تغيير في العقد",
        "note_en": "Labeled demo data — replaced by real GEE pipeline outputs with no contract change",
    }

    out = {
        "fields.geojson": fields,
        "basins.geojson": basins,
        "tws_series.json": tws,
        "forecast.json": forecast,
        "validation.json": validation,
        "impact.json": impact,
        "ledger.json": ledger,
        "timemachine.json": timemachine,
        "exclusions.geojson": exclusions,
        "alerts.json": alerts,
        "meta.json": meta,
    }
    for name, obj in out.items():
        path = os.path.join(OUT_DIR, name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
        size_kb = os.path.getsize(path) / 1024
        print(f"  wrote {name:24s} {size_kb:8.1f} KB")

    n = len(fields["features"])
    reds = sum(1 for f in fields["features"] if f["properties"]["tier"] == "red")
    oranges = sum(1 for f in fields["features"] if f["properties"]["tier"] == "orange")
    print(f"\n  fields: {n} (red {reds} / orange {oranges} / green {n-reds-oranges})")
    print(f"  total detected: {impact['detected_total_ha']} ha, "
          f"{impact['detected_total_m3_mid']/1e6:.1f} MCM/yr (mid)")


if __name__ == "__main__":
    main()
