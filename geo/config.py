# -*- coding: utf-8 -*-
"""
ميزان MIZAN — geo/config.py
كل الثوابت المشتركة لخط أنابيب GEE‏ (P1–P7).
المرجع الملزم: CONTRACTS.md §6 (معرّفات الداتاستات المصحَّحة) + §3 (أوزان P4) + plan.md ملحق أ.
لا يستورد earthengine — ثوابت فقط، آمن للاستيراد محلياً.
"""

import os

# ---------------------------------------------------------------------------
# مشروع GEE — يُضبط عبر متغير البيئة EE_PROJECT أو يُعدَّل هنا بعد earthengine authenticate
# ---------------------------------------------------------------------------
EE_PROJECT = os.environ.get("EE_PROJECT", "mizan-vcoders")
ASSET_ROOT = f"projects/{EE_PROJECT}/assets/mizan"   # جذر الـ Assets للتصدير

# ---------------------------------------------------------------------------
# مناطق الاهتمام (WGS84: lon, lat)
# ---------------------------------------------------------------------------
# bbox حوض الأزرق — المعتمد في CONTRACTS §6
AOI_AZRAQ_BBOX = [36.45, 31.55, 37.30, 32.25]          # lon_min, lat_min, lon_max, lat_max

# bbox وطني تقريبي للأردن — للتشغيل الوطني (إصلاح قنبلة P7، خيار --national)
AOI_JORDAN_BBOX = [34.88, 29.18, 39.30, 33.38]

# منطقة GRACE الإقليمية (شرق الأردن + الجوار) — إشارة إقليمية ~300كم، **ليست حوضية**
GRACE_REGION_BBOX = [35.50, 29.50, 39.30, 33.40]
GRACE_SCOPE = "regional_east_jordan"
GRACE_LABEL_AR = "منحنى GRACE للمنطقة الشرقية/الأردن"
GRACE_LABEL_EN = "GRACE curve — East Jordan region"
GRACE_RESOLUTION_NOTE_AR = "إشارة إقليمية ~300كم — لا تُنسب لحوض مفرد"

# ---------------------------------------------------------------------------
# معرّفات الداتاستات — المصحَّحة (CONTRACTS §6)
# ---------------------------------------------------------------------------
S2_SR        = "COPERNICUS/S2_SR_HARMONIZED"           # Sentinel-2 L2A (من ~2017/2018 فوق الأردن)
S2_CLOUDPROB = "COPERNICUS/S2_CLOUD_PROBABILITY"       # s2cloudless
S2_TOA       = "COPERNICUS/S2_HARMONIZED"              # L1C TOA — لسنة 2016 (آلة الزمن)
LANDSAT8_SR  = "LANDSAT/LC08/C02/T1_L2"                # بديل 2016 (آلة الزمن)
CHIRPS_DAILY = "UCSB-CHG/CHIRPS/DAILY"

# GRACE/GRACE-FO mascon — السلسلة تنتهي 9/2024 (تُقطع بشفافية)
GRACE_MASCON      = "NASA/GRACE/MASS_GRIDS_V04/MASCON"
GRACE_BAND        = "lwe_thickness"                     # سم
GRACE_ENDS_AT     = "2024-09"
GRACE_GAP         = ["2017-07", "2018-05"]              # فجوة GRACE→GRACE-FO
GRACE_BASELINE    = ["2004-01-01", "2010-01-01"]        # baseline anomalies الرسمي 2004.0–2009.999

# GLDAS-2.2 CLSM (المصحَّح — لا GRACE_DA):
GLDAS         = "NASA/GLDAS/V022/CLSM/G025/DA1D"
GLDAS_GWS_BAND = "GWS_tavg"                             # مخزون جوفي، مم، ~27.8كم
GLDAS_SM_BAND  = "SoilMoist_P_tavg"                     # رطوبة تربة (profile) مم — للتفكيك TWS−SM=GWS
                                                        # (يُتحقق من اسم الباند في smoke_test؛ البديل ERA5)

# MODIS ET — فخ التغطية الزمنية (H4): النسخة الروتينية MOD16A2 (061) تبدأ فعلياً 2021،
# لذا 2018–2020 من النسخة المعبّأة الفجوات MOD16A2GF.
MOD16_GF      = "MODIS/061/MOD16A2GF"                   # 2018–2020
MOD16_ROUTINE = "MODIS/061/MOD16A2"                     # من 2021
MOD16_BAND    = "ET"                                    # kg/m²/8days × 0.1
MOD16_SCALE_FACTOR = 0.1
MOD16_SPLIT_YEAR   = 2021                               # < 2021 → GF، >= 2021 → routine

# ERA5-Land الشهري — ET0 لطريقة FAO-56 (Method C)
ERA5_LAND_MONTHLY = "ECMWF/ERA5_LAND/MONTHLY_AGGR"
ERA5_PET_BAND     = "potential_evaporation_sum"         # متر، اصطلاح ECMWF سالب → ×(−1000) = مم

# أغطية الأرض والمياه
WORLDCOVER  = "ESA/WorldCover/v200"
# الفلتر الموسَّع (مراجعة #11 — لالتقاط الزيتون): cropland + bare + tree cover + shrubland
WORLDCOVER_KEEP = [10, 20, 40, 60]                      # 10 شجري · 20 شجيري · 40 محاصيل · 60 جرداء
JRC_WATER   = "JRC/GSW1_4/GlobalSurfaceWater"
JRC_BAND    = "max_extent"                              # خارج أي امتداد مائي تاريخي

# HLS v2 — سلسلة first_seen (يجعل ذكر HLS في وثيقة التقديم صادقاً + يغطي 2016 قبل S2 SR)
HLS_L30 = "NASA/HLS/HLSL30/v002"                        # Landsat: NIR=B5, Red=B4
HLS_S30 = "NASA/HLS/HLSS30/v002"                        # Sentinel-2: NIR=B8A, Red=B4

# SMAP L4 — توكيد مستقل (رطوبة جذور) في بانل الدليل
SMAP      = "NASA/SMAP/SPL4SMGP/008"
SMAP_BAND = "sm_rootzone"                               # m³/m³

# ---------------------------------------------------------------------------
# P1 — المركّبات الشهرية
# ---------------------------------------------------------------------------
P1_START_YEAR = 2017
P1_END_YEAR   = 2026
S2_MAX_CLOUD_PROB = 40                                  # عتبة s2cloudless
TIMEMACHINE_YEARS = list(range(2016, 2027))             # 2016 من TOA/Landsat (لا L2A)

# ---------------------------------------------------------------------------
# P2 — قناع الريّ v1 بالقواعد
# ---------------------------------------------------------------------------
P2_NDVI_T          = 0.35                               # العتبة الأساسية
P2_NDVI_T_ALT      = [0.30, 0.40]                       # بدائل بوابة H6
P2_RAIN_MM         = 10.0                               # sum(CHIRPS, حزيران–آب) < 10مم
P2_SUMMER_MONTHS   = [6, 7, 8]                          # حزيران–آب (شاهد النفي المطري)
P2_SUMMER_ALT      = [7, 8]                             # بديل H6: تموز–آب فقط
P2_SCALE_AOI       = 10                                 # متر — تشغيل الأزرق
P2_SCALE_NATIONAL  = 100                                # متر — التشغيل الوطني (إصلاح قنبلة P7)
P2_DEFAULT_YEAR    = 2025

# ---------------------------------------------------------------------------
# P3 — كشف التغيّر والمضلعات
# ---------------------------------------------------------------------------
P3_MIN_POLY_HA       = 1.0                              # أصغر مضلع يُحتفظ به
P3_MIN_ACTIVE_HA     = 0.5                              # أصغر مساحة نشطة تُحتسب "سنة نشاط"
P3_HLS_NDVI_T        = 0.32                             # عتبة نشاط HLS (أخشن من S2)
P3_CONSECUTIVE_YEARS = 2                                # شرط استمرارية سنتين متتاليتين (ضد أخطاء البور)
P3_YEARS             = list(range(2016, 2027))          # نافذة سلسلة first_seen
FLAG_NEW_YEAR        = 2018                             # NEW: أول ظهور ≥ 2018 (بعد الإغلاق)
FLAG_EXPANDING_RATE  = 0.25                             # EXPANDING: > 25%/سنة
AZRAQ_CLOSURE_YEAR   = 1992                             # الإغلاق القانوني — منطق Tier B

# ---------------------------------------------------------------------------
# P4 — درجة الاشتباه (الصيغة المعتمدة CONTRACTS §3 — بلا طبقة تراخيص)
# score = 35·inside_protected_basin + 25·is_new_after_closure
#       + 15·(persistence_months/12) + 12.5·norm(area_ha) + 12.5·norm(expansion_rate)
# ---------------------------------------------------------------------------
P4_W_BASIN       = 35.0
P4_W_NEW         = 25.0
P4_W_PERSISTENCE = 15.0
P4_W_AREA        = 12.5
P4_W_EXPANSION   = 12.5
P4_AREA_NORM     = "p95"                                # norm(area) = clip(area/p95, 0, 1)
P4_EXP_NORM_CAP  = 0.5                                  # norm(exp)  = clip(exp/0.5, 0, 1)
TIER_RED         = 70                                   # 🔴 ≥70
TIER_ORANGE      = 40                                   # 🟠 40–69 · 🟢 <40
PERSIST_NDVI_T   = 0.30                                 # عتبة "شهر نشط" لحساب persistence_months
NDVI_SERIES_START = "2023-01"                           # سلسلة 36 شهراً (مخطط fields.geojson)
NDVI_SERIES_MONTHS = 36
SMAP_MONTHS       = 12                                  # 12 قيمة شهرية sm_rootzone

# ---------------------------------------------------------------------------
# P5 — تقدير الحجم (نطاق، لا رقم واحد)
# ---------------------------------------------------------------------------
METHOD_A_M3_PER_HA = (6000, 9000)                       # م³/هكتار/سنة (= 600–900مم، افتراض معلَن)
IRRIGATION_EFF     = (0.60, 0.85)                       # كفاءة الريّ — Method C
KC_NDVI_A, KC_NDVI_B = 1.457, -0.1725                   # Kc = a·NDVI + b (Kamble et al. 2013)
KC_CLAMP           = (0.15, 1.20)
EFFECTIVE_RAIN_COEF = 0.7                               # المطر الفعّال = 0.7 × CHIRPS

# ---------------------------------------------------------------------------
# P6 — التنبّؤ
# ---------------------------------------------------------------------------
FORECAST_HORIZON_MONTHS = 36
BACKTEST_HOLDOUT_MONTHS = 24                            # حجب آخر 24 شهراً → MAE
WELL_DROP_2000_2017_M   = -20.0                         # الأزرق — قياسات آبار الوزارة (ملحق أ)
WELL_RATE_M_PER_YR      = -1.1                          # ~1م/سنة (ملحق أ)
WELL_RATE_UNCERT        = 0.2                           # ± على المعدل → نطاق سنوات لا نقطة
WELL_THRESHOLD_EXTRA_M  = -15.0                         # عتبة توضيحية: عمق ضخ اقتصادي إضافي من منسوب 2017
WELL_BASE_YEAR          = 2017

# ---------------------------------------------------------------------------
# P7 — التحقّق
# ---------------------------------------------------------------------------
P7_THRESHOLD_KM   = 5.0                                 # عتبة معلَنة سلفاً: ≤5كم من مضلع 🔴
P7_MINI_AOI_DEG   = 0.15                                # نصف عرض mini-AOI حول كل موقع داخل المنهجية
P7_TOP_K          = 20                                  # precision@20 للطابور

# ---------------------------------------------------------------------------
# مسارات محلية (نسبية لجذر المشروع)
# ---------------------------------------------------------------------------
_GEO_DIR     = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(_GEO_DIR)
DATA_DEMO    = os.path.join(PROJECT_ROOT, "data", "demo")
EXCLUSIONS_GEOJSON = os.path.join(DATA_DEMO, "exclusions.geojson")   # محمية الأزرق الرطبة RAMSAR
BASINS_GEOJSON     = os.path.join(DATA_DEMO, "basins.geojson")
VALIDATION_JSON    = os.path.join(DATA_DEMO, "validation.json")
DEMO_TWS_JSON      = os.path.join(DATA_DEMO, "tws_series.json")
DEMO_FIELDS_GEOJSON = os.path.join(DATA_DEMO, "fields.geojson")

OUT_DIR      = os.path.join(_GEO_DIR, "outputs")        # مخرجات حقيقية (تستبدل ملفات demo)
THUMBS_DIR   = os.path.join(OUT_DIR, "thumbs")
OUT_FIELDS   = os.path.join(OUT_DIR, "fields.geojson")
OUT_TWS_CSV  = os.path.join(OUT_DIR, "tws_series.csv")
OUT_TWS_JSON = os.path.join(OUT_DIR, "tws_series.json")
OUT_FORECAST = os.path.join(OUT_DIR, "forecast.json")
OUT_VALIDATION = os.path.join(OUT_DIR, "validation.json")
OUT_VOLUME   = os.path.join(OUT_DIR, "volume_estimate.json")
OUT_MINI_AOIS = os.path.join(OUT_DIR, "mini_aois.json")
OUT_THUMBS_MANIFEST = os.path.join(THUMBS_DIR, "thumbs_manifest.json")

DRIVE_FOLDER = "mizan_exports"                          # مجلد Drive للتصديرات (تأمين quota يوم 0)


def ensure_out_dirs():
    """ينشئ مجلدات الإخراج عند الحاجة."""
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(THUMBS_DIR, exist_ok=True)
