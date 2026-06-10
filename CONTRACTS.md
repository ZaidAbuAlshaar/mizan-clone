# ميزان MIZAN — العقود المشتركة (Contracts)

> **هذا الملف ملزم لكل الوحدات.** أي كود في `geo/` أو `backend/` أو `web/` يلتزم بالمخططات والمسارات هنا حرفياً.
> القرارات أدناه تدمج إصلاحات لجنة المراجعة (`review.md`): صيغة P4 البديلة بلا طبقة تراخيص، إصلاح قنبلة P7 (عتبة 5كم + lift + mini-AOIs)، معرّف GLDAS الصحيح، العتبة الحرجة على مناسيب الآبار، دفتر الميزان (Mass-Balance)، بصمة الريّ الزمنية (anti-phase).

---

## 0) قواعد غير قابلة للكسر

1. **لا mock كحقيقي أبداً** — كل بيانات مولّدة تحمل `"is_demo": true` وتظهر في الواجهة بشارة «بيانات تجريبية · demo data».
2. **انضباط الأرقام:** أي رقم واقعي معروض كحقيقة يتتبّع لملحق أ في `plan.md` حصراً (61 م³/فرد · 205 م.م³ · 215% الأزرق · 176% عمّان-الزرقا · 201 بئر/62 م.م³ · 1593 بئراً · 6 مليارات/300 م.م³ · 0.5–0.7$/م³ · 1 مليون م³ ≈ 3,730 شخصاً · الأزرق −20م، ~1م/سنة وطنياً · ~308 آلاف م³ بصياغته الآمنة).
3. **قاعدة صياغة GRACE:** السلسلة الزمنية تُسمّى دائماً *«منحنى GRACE للمنطقة الشرقية/الأردن»* (إشارة إقليمية ~300كم)، هبوط الحوض من *«قياسات آبار الوزارة (−20م)»*، وتحديد الحقول من *«Sentinel-2»* حصراً. شارة «إشارة إقليمية ~300كم» إلزامية بجانب منحنى GRACE.
4. **صياغتا الأمان:** 308 آلاف م³ = «متوسط البئر المُغلَق في حملات 2023/24» (لا يُضرب ×1500) · 70% = «من عدد الآبار» (الحجم ~42%).
5. كل visualization **ثنائي اللغة** (ar/en).

---

## 1) ملكية المجلدات

| المجلد | المالك | المحتوى |
|---|---|---|
| `data/` + `tools/` | المنسّق | البيانات التجريبية المولّدة + مولّدها |
| `geo/` | وكيل Geo | سكربتات GEE Python‏ P1–P7 + GEE App |
| `backend/` | وكيل Backend | FastAPI + SQLite (محلي) + SQL لـ PostGIS/Supabase |
| `web/` | المنسّق | Next.js 14 dashboard |
| `pitch/` + جذر الوثائق | وكيل Pitch | نص الديمو 8 لقطات، بطاقات الحكّام الـ12، وثيقة التقديم، CLAUDE.md |

---

## 2) ملفات البيانات (`data/demo/`)

كل الملفات UTF-8، إحداثيات WGS84 (lon, lat).

### 2.1 `fields.geojson` — FeatureCollection

خصائص كل Feature (مضلع حقل مشبوه):

```jsonc
{
  "id": "AZQ-0042",            // معرف ثابت
  "basin_id": "azraq",
  "area_ha": 12.4,
  "first_seen_year": 2019,      // من سلسلة HLS/S2
  "flag": "NEW",                // NEW (≥2018 بعد الإغلاق) | EXPANDING (>25%/سنة) | STABLE
  "expansion_rate": 0.31,       // نسبة سنوية
  "persistence_months": 9,      // أشهر النشاط بالسنة (يستبدل active_in_zero_rain — مراجعة)
  "anti_phase_score": 0.82,     // بصمة الريّ الزمنية NDVI×CHIRPS ضد الموسم 0..1
  "score": 78,                  // 0..100 — الصيغة §3
  "score_breakdown": {
    "inside_protected_basin": 35.0,
    "new_after_closure": 25.0,
    "persistence": 11.3,
    "area": 4.1,
    "expansion": 6.2
  },
  "tier": "red",                // red ≥70 · orange 40–69 · green <40
  "est_m3_low": 74400,          // area_ha × 6000  (Method A)
  "est_m3_high": 111600,        // area_ha × 9000
  "status": "new",              // new → inspected → confirmed | cleared
  "centroid": [36.91, 31.93],
  "ndvi_series": [              // 36 شهراً: 2023-01 → 2025-12
    {"month": "2023-01", "ndvi": 0.18, "chirps_mm": 22.0}
  ],
  "sm_rootzone": [0.12, ...],   // 12 قيمة شهرية SMAP rootzone (توكيد مستقل — مراجعة)
  "is_demo": true
}
```

### 2.2 `basins.geojson` — أحواض بمضلعات تقريبية

```jsonc
{
  "id": "azraq",
  "name_ar": "حوض الأزرق", "name_en": "Azraq Basin",
  "exploitation_pct": 215,       // ملحق أ (MWI 2009 عبر IWMI) — للأزرق وعمّان-الزرقا فقط
  "exploitation_source": "MWI 2009 عبر IWMI",
  "closure_year": 1992,          // إغلاق قانوني — منطق Tier B
  "well_level_drop_m": -20,      // 2000–2017، ملحق أ
  "status": "modeled" | "context", // context = خارج النموذج التجريبي (يُعرض رمادياً)
  "is_demo_geometry": true       // الحدود تقريبية
}
```

الأحواض: `azraq` (215%، modeled) · `amman_zarqa` (176%، modeled-secondary) · `yarmouk`، `dead_sea`، `disi`، `jafr` (context، بلا نسب مخترعة).

### 2.3 `tws_series.json`

```jsonc
{
  "scope": "regional_east_jordan",   // إقليمي — ليس حوضياً (قاعدة GRACE)
  "label_ar": "منحنى GRACE للمنطقة الشرقية/الأردن",
  "unit": "cm",
  "gap": ["2017-07", "2018-05"],     // فجوة GRACE→GRACE-FO تُعرض بشفافية
  "series": [{"month": "2002-04", "tws_cm": 2.1, "gws_cm": 1.4}],  // gws = tws − soil moisture (GLDAS)
  "ends_at": "2024-09",              // MASCON ينتهي 9/2024 — يُقطع بشفافية
  "is_demo": true
}
```

### 2.4 `forecast.json`

```jsonc
{
  "basin_id": "azraq",
  "grace_forecast": {                 // Prophet على الإشارة الإقليمية — مؤشر مساند
    "series": [{"month": "2024-10", "yhat": -19.2, "lo": -20.1, "hi": -18.3}],
    "backtest_mae_cm": 1.3
  },
  "well_level": {                     // العتبة الحرجة الفعلية — على مناسيب الآبار (مراجعة)
    "drop_2000_2017_m": -20,          // ملحق أ
    "rate_m_per_yr": -1.1,            // ملحق أ (~1م/سنة)
    "critical_year_low": 2031, "critical_year_high": 2035,
    "threshold_note_ar": "عتبة توضيحية: عمق ضخ اقتصادي إضافي −15م"
  },
  "is_demo": true
}
```

### 2.5 `validation.json` — P7 (الإصلاح الكامل)

```jsonc
{
  "threshold_km": 5,                 // معلَنة سلفاً على شريحة/شاشة التحقق
  "sites": [{
    "id": "khan_zabib", "name_ar": "خان الزبيب", "name_en": "Khan Az-Zabib",
    "lon": 36.05, "lat": 31.66, "date": "2025-08",
    "detail_ar": "حملة إنفاذ موثّقة 8/2025", "source": "صراحة نيوز (PDF محفوظ)",
    "coords_note": "إحداثيات تقريبية لمركز المنطقة",
    "scope": "in_methodology",        // in_methodology (منطق صحراوي، mini-AOI) | out_of_methodology
    "out_reason_ar": null,            // للكفرين: "غور مروي بقناة الملك عبدالله — مياه سطحية متاحة"
    "hit": true                       // داخل ≤5كم من مضلع 🔴 (mini-AOI)
  }],
  "stats": {
    "in_scope": 3, "hits": 3,
    "red_area_pct": 2.6,             // نسبة المساحة الحمراء من AOI
    "lift": 38,                      // (hits/in_scope) ÷ red_area_pct — null model
    "precision_at_20": 0.70,         // demo — يُستبدل برقم يوم الحدث
    "framing_ar": "تطابق حالات (case-study concordance) — لا precision/recall على عيّنة إخبارية"
  },
  "is_demo": true
}
```

المواقع الستة: وادي السير (out: غرب عمّان مطري) · الكفرين/سويمة 8 آبار 5,000م³/س 11/2025 (out: مياه سطحية) · الكفرين 17 بئراً 5/2025 (out) · خان الزبيب 8/2025 (in) · الجفر بئر 300م (in) · الزرقاء 2/2026 (in).

### 2.6 `impact.json`

```jsonc
{
  "detected_total_m3_low": ..., "detected_total_m3_mid": ..., "detected_total_m3_high": ...,
  "scenarios": {"conservative": 0.35, "expected": 0.55},   // معدل تأكيد التفتيش — سحّاب في الواجهة
  "constants": {                                            // ملحق أ — حقيقية
    "people_per_mcm": 3730, "desal_usd_low": 0.5, "desal_usd_high": 0.7,
    "carrier_mcm": 300, "carrier_cost_usd_bn": 6,
    "overdraft_mcm": 205, "manual_2023_24": {"wells": 201, "mcm": 62}
  },
  "is_demo": true
}
```

### 2.7 ملفات إضافية

- `exclusions.geojson` — محمية الأزرق الرطبة (RAMSAR) + الواحة، مستبعدة من P2 (مراجعة #10).
- `ledger.json` — دفتر الميزان: كفة GRACE الإقليمية مقابل (مرخّص + تغذية + ET المكتشف) → «العجز المجهول». كله `is_demo` بصيغ معلنة.
- `timemachine.json` — لكل سنة 2016–2026: عدد الحقول الظاهرة + الهكتارات (آلة الزمن vector-replay).
- `alerts.json` — أعلى 20 تنبيهاً (مشتق من fields).
- `meta.json` — `{generated_at, data_mode: "demo", generator_version}`.

---

## 3) صيغة درجة الاشتباه P4 — النسخة المعتمدة (بلا طبقة تراخيص)

> صيغة الدستور الأصلية تخصص 15 نقطة لـ`distance_to_licensed_well` وطبقة التراخيص غير متاحة (Tier B). **المعتمد** (مراجعة، معاد توزينها + persistence بدل العتبة الثنائية):

```
score = 35·inside_protected_basin
      + 25·is_new_after_closure
      + 15·(persistence_months / 12)
      + 12.5·norm(area_ha)            // norm = clip(x / p95, 0, 1)
      + 12.5·norm(expansion_rate)     // norm = clip(x / 0.5, 0, 1)
```

🔴 ≥70 · 🟠 40–69 · 🟢 <40. تُوثَّق في model card (شاشة المنهجية) مع ملاحظة المعايرة على validation_sites (precision@20) يوم الحدث.

---

## 4) عقد الـ API (Backend FastAPI)

Base URL محلي: `http://localhost:8000`. كل الردود JSON. CORS مفتوح لـ `localhost:3000` + دومين Vercel.

| Method | Path | المعاملات | يرجع |
|---|---|---|---|
| GET | `/fields` | `basin, min_score, status, flag, limit` | GeoJSON FeatureCollection |
| GET | `/fields/{id}` | — | Feature |
| GET | `/fields/{id}/ndvi` | — | `{id, series: [...]}` |
| PATCH | `/fields/{id}/status` | body `{"status": "...", "note": "..."}` | Feature محدَّث (يثبت في SQLite) |
| GET | `/alerts` | `limit=20` | أعلى الحقول درجة (🔴) |
| GET | `/basins` | — | GeoJSON بأحواض وخصائص الصحة |
| GET | `/basins/{id}/health` | — | خصائص الحوض + مؤشرات |
| GET | `/basins/{id}/forecast` | — | محتوى `forecast.json` |
| GET | `/basins/{id}/ledger` | — | دفتر الميزان |
| GET | `/validation` | — | `validation.json` |
| GET | `/impact` | `rate` (0.1–0.9 اختياري) | impact محسوب بالسيناريو |
| GET | `/timemachine` | — | `timemachine.json` |
| GET | `/meta` | — | `{data_mode, generated_at, version}` |

دورة الحالة: `new → inspected → confirmed | cleared` (أي انتقال آخر = 422).

**الواجهة تقرأ عبر طبقة بيانات بنمط fallback:** تجرّب `NEXT_PUBLIC_API_URL` ثم تسقط على `web/public/data/*.json` (نسخة من `data/demo/`) — الديمو لا يسقط أبداً (فلسفة سلّم الخروج).

---

## 5) هوية التصميم (web)

- **الثيم:** غرفة تحكّم فضائية. خلفية `#060B14`، أسطح `#0B1422/#0E1A2B`، حدود `#1B2C44`، تركواز `#2DD4BF` + سماوي `#38BDF8`، نص `#E6EDF7/#8FA3BF`. أعلام: 🔴 `#F43F5E` · 🟠 `#F59E0B` · 🟢 `#10B981`.
- **الخطوط:** Almarai (عناوين/أرقام، 700/800) + Tajawal (نصوص). أرقام KPI ضخمة `tabular-nums`.
- **RTL أولاً** (`<html dir="rtl" lang="ar">`) مع مبدّل EN كامل (قاموسا ar/en).
- **الخريطة:** MapLibre GL + Carto dark-matter raster tiles (بلا مفاتيح).
- **شارات إلزامية:** «بيانات تجريبية · demo data» عند أي بيانات مولّدة · «إشارة إقليمية ~300كم» بجانب منحنى GRACE.
- الشاشات: `/` الخريطة الوطنية · `/basin/azraq` تفاصيل الحوض (+دفتر الميزان+آلة الزمن) · `/queue` طابور التفتيش (+بانل الدليل) · `/impact` عدّاد الأثر (نطاق بسيناريوهات) · `/methodology` المنهجية (CORE/SUPPORT/STRETCH + الحدود الخمسة + model card + إفصاح AI) · `/validation` التحقّق P7.

---

## 6) معرّفات الداتاستات (geo) — المصحَّحة

- Sentinel-2: `COPERNICUS/S2_SR_HARMONIZED` (+`COPERNICUS/S2_CLOUD_PROBABILITY`)
- CHIRPS: `UCSB-CHG/CHIRPS/DAILY`
- GRACE mascon: `NASA/GRACE/MASS_GRIDS_V04/MASCON` — band `lwe_thickness` (سم، ينتهي 9/2024)
- **GLDAS (مصحَّح):** `NASA/GLDAS/V022/CLSM/G025/DA1D` — band `GWS_tavg` (مم، ~27.8كم) — لا `GRACE_DA`
- MODIS ET: `MODIS/061/MOD16A2GF` للفترة 2018–2020 + `MODIS/061/MOD16A2` من 2021 (فخ التغطية الزمنية)
- WorldCover: `ESA/WorldCover/v200` — **فلتر موسَّع** `{cropland, bare, tree cover, shrubland}` (الزيتون) أو قناع استبعاد فقط (built-up + water)
- JRC: `JRC/GSW1_4/GlobalSurfaceWater` · HLS: `NASA/HLS/HLSL30/v002` + `HLSS30/v002` (سلسلة first_seen)
- SMAP: `NASA/SMAP/SPL4SMGP/008` — `sm_rootzone` كتوكيد مستقل في بانل الدليل
- AOI الأزرق bbox: lon 36.45–37.30, lat 31.55–32.25 · فجوة GRACE: 2017-07→2018-05
