# ميزان MIZAN — كشف سرقة المياه الجوفية من الفضاء

> نوزِن مياه الأردن المسروقة من الفضاء — ونعطي الوزارة خريطة استرجاعها.
> *We weigh Jordan's stolen groundwater from space — and hand the Ministry the map to take it back.*
> **AstroCode 2026 · التحدي 1 · فريق Vcoders**

## نظرة عامة على التنفيذ (Implementation Overview)

ميزان يحوّل بيانات الأقمار المفتوحة (Sentinel-2 · GRACE-FO · CHIRPS · HLS · SMAP · MODIS ET · GLDAS) إلى **أداة إنفاذ تشغيلية** لوزارة المياه: حقول خضراء في صحراء بلا مطر فوق حوض مغلق قانونياً = ضخّ جوفي مشبوه → طابور تفتيش GPS مرتّب بدرجة اشتباه شفافة، مع دليل قابل للشرح لكل موقع.

### ✅ بيانات حقيقية بالكامل (`data_mode: "real"`)

اللوحة تعمل على **بيانات فضائية حقيقية مُنزّلة**، لا محاكاة:

| الطبقة | المصدر الحقيقي | الوصول |
|---|---|---|
| **كشف الحقول + الدرجات** | Sentinel-2 L2A — **141 حقلاً** مكتشفاً من NDVI فعلي فوق الأزرق | Microsoft Planetary Computer (بلا مفتاح) |
| **GRACE TWS + التنبّؤ** | JPL GRACE/GRACE-FO mascon RL06.3v04 — **254 شهراً** (2002→2026، اتجاه −0.95سم/سنة، backtest MAE 1.01سم) | NASA PO.DAAC (Earthdata token) |
| **المناخ + النفي المطري** | NASA POWER — أمطار/تبخّر/حرارة **276 شهراً** (متوسط مطر الصيف 2.8مم) | NASA POWER (بلا مفتاح) |
| **خلفية الخريطة + آلة الزمن** | VIIRS/MODIS TrueColor + NDVI | NASA GIBS (بلا مفتاح) |
| **آلة الزمن الحادّة (20م)** | Sentinel-2 L2A صيفي 2018→2025 + Landsat 8 لسنة 2016 — مسرح المقارنة + قصاصات قبل/بعد لكل حقل | Microsoft Planetary Computer (بلا مفتاح) |
| **مخزون GLDAS الجوفي** | GLDAS-2.2 CLSM (مدمج بجاذبية GRACE) — **278 شهراً**، اتجاه −1.1مم/سنة: توكيد مستقل ثانٍ للنزيف | **Google Earth Engine** (مشروع `mizan-earth-engine`) |

الجزء الوحيد التوضيحي (بصراحة): **عتبة منسوب الآبار الحرجة** — استقراء من أرقام MWI المنشورة (−20م/−1م/سنة)، يحمل شارة «توضيحي».

### المحرّكات الثلاثة (The Three Engines)

| المحرّك | الوظيفة | البيانات |
|---|---|---|
| **E1 — الكشف** | قناع ريّ صحراوي (NDVI مرتفع + صفر مطر + خارج المياه السطحية) + بصمة الريّ الزمنية anti-phase + طبقات استبعاد (محمية RAMSAR، الزيتون ملتقط بفلتر موسَّع) | Sentinel-2 · CHIRPS · WorldCover · JRC |
| **E2 — الاشتباه والطابور** | مضلعات حقول + `first_seen_year` + درجة 0–100 بأوزان شفافة → طابور تفتيش بدورة حالة `new → inspected → confirmed/cleared` | Sentinel-2 · HLS · SMAP · MODIS ET |
| **E3 — التنبّؤ والميزان** | منحنى GRACE إقليمي + Prophet (مؤشر مساند) · التاريخ الحرج على **مناسيب آبار الوزارة** · دفتر الميزان (top-down ↔ bottom-up = «العجز المجهول») | GRACE-FO MASCON · GLDAS · CHIRPS |

## بنية المجلدات (Repository Structure)

```
├── CONTRACTS.md      # العقد الملزم بين الوحدات: مخططات البيانات + عقد API + التصميم + معرّفات GEE
├── CLAUDE.md         # مرجع جلسات Claude Code أثناء الحدث (القواعد + الأوامر + الملكية)
├── plan.md           # الخطة التنفيذية + ملحق أ (جدول الأرقام الملزم) + ملحق ب (المنهجية)
├── review.md         # تقرير لجنة المراجعة — إصلاحاته مدمجة في كل العقود والوثائق
├── data/real/        # المخرجات الحقيقية: fields.geojson (Sentinel-2) · tws_series/forecast (GRACE) · climate (POWER)
├── data/demo/        # طبقة العرض المدمجة (تفضّل data/real تلقائياً؛ توضيحية فقط حين يغيب الحقيقي)
├── tools/            # جالبات NASA الحقيقية + محرّك كشف Sentinel-2 + المولّد المدمج
├── geo/              # سكربتات GEE Python‏ P1–P7 + GEE App        (وكيل Geo)
├── backend/          # FastAPI + SQLite/PostGIS — عقد API كامل في CONTRACTS §4   (وكيل Backend)
├── web/              # Next.js 14 dashboard — عربي RTL أولاً + EN، MapLibre داكنة (المنسّق)
├── pitch/            # نص الديمو (8 لقطات) · بطاقات الحكّام الـ12 · وثيقة التقديم · بروتوكول البروفات
└── docs/             # الدستور + خطة الحرب (المرجعان الكاملان)
```

## التشغيل السريع (Quickstart)

```bash
# 1) دمج البيانات الحقيقية (data/real/*) في طبقة العرض → data/demo/ + web/public/data/
python tools/generate_demo_data.py   # (لإعادة جلب الحقيقي من المصدر: انظر قسم «إعادة الجلب» أدناه)

# 2) الـ backend (FastAPI على http://localhost:8000)
cd backend && pip install -r requirements.txt && uvicorn main:app --reload --port 8000

# 3) الواجهة (Next.js على http://localhost:3000)
cd web && npm install && npm run dev
```

الواجهة تقرأ عبر طبقة fallback: تجرّب `NEXT_PUBLIC_API_URL` ثم تسقط على نسخة البيانات في `web/public/data/` — **لا تسقط أبداً** (انسخ `data/demo/*` إليها عند التحديث).

> **مهم:** الـ backend يحمّل البيانات في الذاكرة عند الإقلاع — بعد إعادة توليد البيانات **أعد تشغيل الـ backend** كي تظهر القيم المحدَّثة.

## إعادة جلب البيانات الحقيقية بنفسك (Reproduce the Real Data)

كل المخرجات الحقيقية **مرفوعة جاهزة** في المستودع، فاللوحة تعمل فورًا. لإعادة جلبها من المصدر:

```bash
pip install -r tools/requirements.txt

# 1) مناخ NASA POWER + صور NASA GIBS — بلا أي مفتاح
python tools/fetch_nasa_data.py
powershell -File tools/fetch_nasa_imagery.ps1     # أو نفّذ أوامر WMS يدوياً

# 2) كشف الحقول الحقيقي من Sentinel-2 — بلا مفتاح (Microsoft Planetary Computer)
python tools/detect_real_fields.py --res 50       # → data/real/fields.geojson (141 حقل)

# 3) GRACE/GRACE-FO الحقيقي — يحتاج token مجاني من NASA Earthdata
#    سجّل: https://urs.earthdata.nasa.gov/users/new  ثم Generate Token
$env:MIZAN_ED_TOKEN = "<your-earthdata-token>"     # PowerShell
# export MIZAN_ED_TOKEN="<your-earthdata-token>"   # bash
python tools/fetch_grace.py                        # → data/real/tws_series.json + forecast.json

# 4) آلة الزمن عالية الدقة — Sentinel-2 ‏20م + Landsat 2016 (بلا مفتاح)
python tools/fetch_s2_timemachine.py               # → web/public/nasa/tm_azraq_*.jpg
                                                   #   + قصاصات قبل/بعد حقيقية لكل حقل (nasa/fields/)

# 5) مخزون GLDAS الجوفي عبر Google Earth Engine — توكيد مستقل ثانٍ
#    يحتاج: earthengine authenticate + مشروع Cloud (EE_PROJECT)
$env:EE_PROJECT = "mizan-earth-engine"
python geo/fetch_gldas_gws.py                      # → data/real/gws_series.json

# 6) دمج كل ذلك في data/demo/ ونسخه للواجهة
python tools/generate_demo_data.py
```

🔒 **بلا أسرار في المستودع:** الـ token يُؤخذ من متغيّر البيئة `MIZAN_ED_TOKEN` أو ملف محلي `data/real/.ed_token` — **كلاهما مُستثنى من git ولا يُرفع أبداً**. استخدم token الخاص بك.

## انضباط الأرقام (Data Integrity)

**قاعدة غير قابلة للكسر:** لا mock يُعرض كحقيقي أبداً. الطبقات الحقيقية تحمل `"is_real": true` وتظهر بشارة خضراء **«بيانات حقيقية · Sentinel-2 + NASA»**؛ والأجزاء المنمذجة على اتجاه منشور (عتبة الآبار) تحمل شارة **«توضيحي»**. وكل رقم واقعي معروض كحقيقة يتتبّع حصراً لجدول الأرقام في `plan.md` (ملحق أ) بمصادره المنشورة.

## ملفات التوثيق (Documentation Map)

| الملف | الدور |
|---|---|
| [`CONTRACTS.md`](CONTRACTS.md) | **العقد الملزم لكل الوحدات** — مخططات `data/demo/`، صيغة درجة P4، عقد الـ API، هوية التصميم، معرّفات الداتاستات المصحَّحة |
| [`plan.md`](plan.md) | **الخطة التنفيذية المتكاملة** — المراحل (T-minus + 0–5)، الأدوار، 54 مهمة بمعرّفات ومعايير إنجاز، 9 بوابات قرار 🚦، المخاطر، سلّم الخروج، خط الـ Pitch، انضباط الأرقام، أوامر الانطلاق |
| [`progress.md`](progress.md) | **متتبع التقدم الحي** — يحدَّث أثناء التنفيذ: checklists، سجل البوابات، سجل العوائق، تثبيت الأرقام، الأهلية، سجل الجلسات |
| [`review.md`](review.md) / [`review-details.md`](review-details.md) | **تقرير لجنة المراجعة الداخلية** — 6 قضاة، إصلاحات مدمجة (قنبلة P7، 8 لقطات، البطاقات الـ12، دفتر الميزان…) |
| [`CLAUDE.md`](CLAUDE.md) | **مرجع جلسات Claude Code** — يغني عن لصق الوثائق الكاملة كل جلسة (إصلاح المراجعة #13) |
| [`pitch/demo_script.md`](pitch/demo_script.md) | نص الديمو — 8 لقطات / 3 دقائق + نسختا 60ث و5د |
| [`pitch/judges_qa.md`](pitch/judges_qa.md) | ورقة أسئلة الحكّام — 12 بطاقة بأجوبة محفوظة |
| [`pitch/submission_doc.md`](pitch/submission_doc.md) | وثيقة التقديم — بيانات الفضاء بالاسم + مطابقة المتطلبات + إفصاح AI |
| [`pitch/rehearsal_protocol.md`](pitch/rehearsal_protocol.md) | بروتوكول البروفات والفيديو الاحتياطي (قاعدة الـ 10 ثوانٍ) |
| [`docs/ميزان_MIZAN_FINAL_v2.md`](docs/ميزان_MIZAN_FINAL_v2.md) | **الدستور** — المواصفة الكاملة (ماذا ولماذا): القصة، العلم، architecture، pipeline P1–P7، الشاشات. **مصدر الحقيقة الوحيد لكل رقم (§4)** |
| [`docs/MIZAN_ULTRA_PLAN.md`](docs/MIZAN_ULTRA_PLAN.md) | **خطة الحرب التشغيلية** — متى ومَن وكيف نقرّر: T-minus، المصفوفة ساعة بساعة، بوابات H4–H46 |

## بروتوكول بدء الجلسات (محدَّث — إصلاح المراجعة #13)

كل جلسة Claude Code تبدأ بقراءة **`CLAUDE.md`** (يُقرأ تلقائياً) + أمر الانطلاق الخاص بالحساب (`plan.md` §15) — **بدل لصق الوثيقتين الكاملتين (~25 ألف token)**. الوثائق الكاملة في الـ repo تُفتح عند الحاجة فقط.

## القواعد الذهبية

1. **working > perfect** — خط القطع: Phase 1 منتهية = نجاح مضمون.
2. **commit كل 30–60 دقيقة** — التأمين ضد rate limits (كل وكيل يضيف مجلده فقط — لا `git add -A`).
3. **لا أحد يخترع رقماً** — كل رقم يتتبّع لجدول الأرقام (`plan.md` الملحق أ = الدستور §4).

## الإفصاح عن الذكاء الاصطناعي (AI Disclosure)

بُني ميزان باستخدام **Claude (Anthropic) بكثافة** عبر Claude Code — كوداً ووثائق وبيانات عرض تجريبية موسومة. الفريق صمّم المعمارية والمنهجية وراجع كل المخرجات؛ كل رقم واقعي يتتبّع لمصدر منشور، وكل بيانات مولّدة موسومة `is_demo`. **نفصح بفخر، لا نخفي** — التفاصيل في [`pitch/submission_doc.md`](pitch/submission_doc.md) §8.

## الترخيص (License)

**MIT** — انظر [`LICENSE`](LICENSE). الكود كله مفتوح المصدر؛ البيانات الفضائية المستخدمة كلها مفتوحة (Copernicus, NASA, CHIRPS) بشروط مزوّديها.

---

*كل قطرة محسوبة… من الفضاء — والوزن لا يكذب.*
