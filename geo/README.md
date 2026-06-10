# ميزان MIZAN — `geo/` خط أنابيب تحليلات GEE‏ (P1–P7)

سكربتات Google Earth Engine‏ Python كاملة وجاهزة للتشغيل **لحظة نجاح `earthengine authenticate`**.
الالتزام الملزم: `CONTRACTS.md` (المخططات والمعرّفات المصحَّحة) + `plan.md` (الملحق أ للأرقام) + `review.md`.

## 0) التهيئة (مرة واحدة — TM-02)

```bash
pip install -r requirements.txt
earthengine authenticate
set EE_PROJECT=<معرّف مشروع Google Cloud>     # أو عدّل EE_PROJECT في config.py
```

> كل السكربتات تعمل من داخل مجلد `geo/`:‏ `cd geo` أولاً (الاستيرادات بين الملفات محلية).

## 1) ترتيب التشغيل

| # | الأمر | الناتج | يستبدل ملف demo |
|---|---|---|---|
| 0 | `python smoke_test.py` | تقرير TM-03: الداتاستات الأربعة + شاهد النفي المطري (TM-10) | — |
| 1 | `python p1_composites.py --to drive` | مركّبات NDVI/NDWI شهرية 2017–2026 — **شغّله يوم 0 (تأمين quota)** | — |
| 2 | `python p2_mask.py --year 2025 --to drive` | قناع الريّ v1 (GeoTIFF) | — |
| 3 | `python p3_change.py --year 2025 --to drive` | مضلعات + first_seen (HLS) + أعلام (GeoJSON على Drive) | — |
| 4 | `python p4_score.py --fields-geojson <ناتج P3>` | `outputs/fields.geojson` بالمخطط الحرفي §2.1 | `data/demo/fields.geojson` |
| 5 | `python p5_volume.py --fields-geojson outputs/fields.geojson` | `outputs/volume_estimate.json` — **نطاق** ثلاثي الطرق | أرقام م³ في `impact.json` (عبر المنسّق) |
| 6أ | `python p6_grace.py --export` ثم `--from-csv <الملف>` | `outputs/tws_series.json` (TWS−SM=GWS، إقليمي) | `data/demo/tws_series.json` |
| 6ب | `python p6_forecast.py --input outputs/tws_series.json` | `outputs/forecast.json` (+backtest MAE + النطاق الحرج) | `data/demo/forecast.json` |
| 7 | `python p7_validate.py --fields outputs/fields.geojson` | `outputs/validation.json` (تطابق حالات + lift) | `data/demo/validation.json` |
| 8 | `python export_thumbs.py --limit 20` + `--timemachine` | PNG قبل/بعد + 10 صور آلة الزمن + manifest | صور الواجهة |
| 9 | `gee_app/app.js` → لصق في Code Editor → Publish | رابط GEE App (بوابة H20 — غير قابلة للتفاوض) | — |

> **قاعدة الوسم:** مخرجات هذا الخط الحقيقية تُكتب بـ `is_demo: false`. أي ملف demo يبقى موسوماً
> ولا يُعرض كحقيقي أبداً. `p6_forecast.py` و`p7_validate.py` يرثان `is_demo` من المصدر تلقائياً.

## 2) البوابات المدمجة 🚦

- **H4 (الساعة 0–4):** `python p5_volume.py --h4-only` — تغطية MODIS ET زمنياً ومكانياً
  (الفخ مصحَّح: `MOD16A2GF` للفترة 2018–2020 + `MOD16A2` من 2021).
  القرار المكتوب سلفاً: تغطية جيدة ✅→Method B لاحقاً · ❌→**Method A نهائياً** (6,000–9,000 م³/هكتار)، لا نعود للموضوع.
- **H6 (4–8):** القناع لا يلتقط مزارع الأزرق المعروفة؟
  `--ndvi 0.30` أو `--ndvi 0.40` · `--window jul-aug` · أو Landsat (خيار `p1 --source landsat8`).
- **H8 (8–12، قرار القائد):** استمر فشل H6 → نقل AOI إلى عمّان–الزرقا:
  `p2_mask.py --bbox <bbox عمّان-الزرقا>` — بلا نقاش بعد 20 دقيقة.
- **H20:** نشر `gee_app/app.js` برابط يعمل من جهاز خارجي مهما كان حال الباقي.

## 3) قرارات معمارية ملزمة (من المراجعة)

- **قنبلة P7:** مواقع التحقق الستة خارج bbox الأزرق → الحل الأقوى تشغيل وطني
  `p2_mask.py --national` (100م، job ليلي واحد) أو `p7_validate.py --mini-aois`
  (يولّد bboxes جاهزة لكل موقع داخل المنهجية). مواقع الغور تُستبعد بشفافية مع السبب.
- **GLDAS المصحَّح:** `NASA/GLDAS/V022/CLSM/G025/DA1D` باند `GWS_tavg` — **لا** `GRACE_DA`.
  `smoke_test.py` يتحقق أيضاً من باند رطوبة التربة للتفكيك (`p6_grace.py --sm-source era5` بديل).
- **قاعدة صياغة GRACE:** السلسلة = «منحنى GRACE للمنطقة الشرقية/الأردن» (إقليمي ~300كم) —
  مضمّنة في مخرجات `p6_grace.py` حرفياً. هبوط الحوض من قياسات آبار الوزارة (−20م)،
  وتحديد الحقول من Sentinel-2 حصراً.
- **MASCON ينتهي 9/2024** — السلسلة تُقطع عند `2024-09` بشفافية، وفجوة GRACE→GRACE-FO
  ‏(2017-07→2018-05) تبقى ظاهرة كأشهر غائبة.
- **آلة الزمن 2016:** لا S2 L2A قبل ~2017 فوق الأردن → TOA L1C أو Landsat 8
  (`p1_composites.py --toa2016`، و`export_thumbs.py` يطبقها تلقائياً).
- **فلتر WorldCover الموسَّع** {شجري، شجيري، محاصيل، جرداء} — لالتقاط الزيتون،
  واستبعاد محمية الأزرق الرطبة (RAMSAR) من `data/demo/exclusions.geojson`.
- **شرط الاستمرارية (P3):** سنة الظهور الأول تتطلب نشاطاً **سنتين متتاليتين** ضد أخطاء البور.

## 4) سجل المخاطر التشغيلي

- أي تصدير > 45 دقيقة → صغّر الدقة لـ20م أو قسّم الـ AOI (`--bbox`).
- المركّبات تُصدَّر **يوم 0** إلى Drive/Assets — التأمين ضد GEE quota.
- Prophet غير مثبّت؟ `p6_forecast.py` يسقط تلقائياً على نموذج موثَّق
  (اتجاه خطي + توافقيات سنوية بفترات ثقة) ويصرّح بذلك في الناتج (`model`).
