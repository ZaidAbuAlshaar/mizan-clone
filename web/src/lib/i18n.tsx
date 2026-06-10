"use client";
/**
 * i18n خفيف — عربي-RTL أولاً مع مبدّل EN كامل (قاعدة الدستور §22: كل visualization ثنائي اللغة)
 */
import React, { createContext, useContext, useEffect, useState } from "react";

export type Lang = "ar" | "en";

const dict = {
  // ---- عام
  app_name: { ar: "ميزان", en: "MIZAN" },
  app_tag: { ar: "نوزِن مياه الأردن المسروقة — من الفضاء", en: "Weighing Jordan's stolen water — from space" },
  team: { ar: "AstroCode 2026 · فريق Vcoders", en: "AstroCode 2026 · Team Vcoders" },
  demo_badge: { ar: "بيانات تجريبية", en: "demo data" },
  demo_tooltip: {
    ar: "بيانات مولّدة موسومة — تُستبدل بمخرجات GEE الحقيقية بلا تغيير في العقد. لا mock كحقيقي أبداً.",
    en: "Labeled synthetic data — replaced by real GEE outputs with no contract change. Never mock-as-real.",
  },
  source_api: { ar: "متصل بالـ API الحي", en: "Live API connected" },
  source_static: { ar: "وضع العرض الساكن (بلا API)", en: "Static demo mode (no API)" },
  regional_badge: { ar: "إشارة إقليمية ~300كم", en: "Regional signal ~300km" },
  approx_boundaries: { ar: "حدود تقريبية", en: "Approximate boundaries" },
  last_update: { ar: "آخر تحديث", en: "Last update" },
  loading: { ar: "جارٍ التحميل…", en: "Loading…" },

  // ---- التنقل
  nav_map: { ar: "الخريطة الوطنية", en: "National Map" },
  nav_timemachine: { ar: "آلة الزمن", en: "Time Machine" },
  nav_basin: { ar: "تفاصيل الحوض", en: "Basin Details" },
  nav_queue: { ar: "طابور التفتيش", en: "Inspection Queue" },
  nav_impact: { ar: "عدّاد الأثر", en: "Impact Counter" },
  nav_validation: { ar: "التحقّق", en: "Validation" },
  nav_methodology: { ar: "المنهجية", en: "Methodology" },

  // ---- الشاشة 1: الخريطة الوطنية
  map_title: { ar: "غرفة عمليات المياه الجوفية — الأردن", en: "Jordan Groundwater Operations Room" },
  red_flags: { ar: "أعلام حمراء 🔴", en: "Red flags 🔴" },
  suspect_fields: { ar: "حقل مشبوه مكتشف", en: "suspect fields detected" },
  est_recoverable: { ar: "م³/سنة مقدَّرة (نطاق أوسط)", en: "est. m³/yr (mid range)" },
  top_alerts: { ar: "أعلى التنبيهات", en: "Top alerts" },
  view_queue: { ar: "افتح طابور التفتيش", en: "Open inspection queue" },
  basin_health: { ar: "صحة الأحواض", en: "Basin health" },
  of_safe_yield: { ar: "من الإنتاج الآمن", en: "of safe yield" },
  basin_closed: { ar: "مغلق قانونياً", en: "Legally closed" },
  context_basin: { ar: "خارج النموذج التجريبي", en: "Outside pilot model" },
  layer_fields: { ar: "الحقول المشبوهة", en: "Suspect fields" },
  layer_basins: { ar: "الأحواض", en: "Basins" },
  layer_exclusions: { ar: "مناطق الاستبعاد (محمية RAMSAR)", en: "Exclusion zones (RAMSAR reserve)" },
  layer_validation: { ar: "مواقع الإنفاذ الحقيقية", en: "Real enforcement sites" },
  open_evidence: { ar: "افتح الدليل", en: "Open evidence" },
  search_placeholder: { ar: "ابحث عن حقل (AZQ-0001)…", en: "Search field (AZQ-0001)…" },

  // ---- الشاشة 2: الحوض
  basin_azraq: { ar: "حوض الأزرق", en: "Azraq Basin" },
  grace_curve_title: { ar: "منحنى GRACE للمنطقة الشرقية/الأردن", en: "GRACE curve — East Jordan region" },
  grace_subtitle: {
    ar: "سماكة الماء المكافئ (سم) — GRACE+GRACE-FO MASCON الحقيقي (JPL RL06.3v04) · الفجوة 2017–2018 معروضة",
    en: "Equivalent water thickness (cm) — real GRACE+GRACE-FO MASCON (JPL RL06.3v04) · 2017–2018 gap shown",
  },
  grace_gap: { ar: "فجوة GRACE → GRACE-FO", en: "GRACE → GRACE-FO gap" },
  tws_label: { ar: "TWS (إجمالي تخزين الماء)", en: "TWS (total water storage)" },
  gws_label: { ar: "GWS (جوفي = TWS − رطوبة التربة)", en: "GWS (groundwater = TWS − soil moisture)" },
  forecast_label: { ar: "تنبّؤ Prophet (مساند)", en: "Prophet forecast (supporting)" },
  forecast_band: { ar: "نطاق الثقة", en: "Confidence band" },
  backtest: { ar: "خطأ التنبؤ التاريخي (backtest)", en: "Historical forecast error (backtest)" },
  well_level_title: { ar: "قياسات آبار الوزارة — العتبة الحرجة", en: "Ministry well measurements — critical threshold" },
  well_level_sub: {
    ar: "الأزرق −20م (2000–2017) · ~1م/سنة — العتبة الحرجة تُعرَّف هنا، لا على إشارة GRACE الإقليمية",
    en: "Azraq −20m (2000–2017) · ~1m/yr — the critical threshold is defined here, not on the regional GRACE signal",
  },
  critical_window: { ar: "نافذة العتبة الحرجة", en: "Critical threshold window" },
  detected_hectares: { ar: "الهكتارات المكتشفة", en: "Detected hectares" },
  time_machine: { ar: "آلة الزمن 2016 ↔ 2026", en: "Time machine 2016 ↔ 2026" },
  time_machine_note: {
    ar: "الصحراء تخضرّ: الحقول حسب سنة الظهور الأول (Sentinel-2 / Landsat لسنة 2016)",
    en: "The desert turns green: fields by first-seen year (Sentinel-2 / Landsat for 2016)",
  },
  fields_visible: { ar: "حقل ظاهر", en: "fields visible" },
  ledger_title: { ar: "دفتر الميزان — تدقيق الكتلة", en: "The Mizan Ledger — Mass-Balance Audit" },
  ledger_left: { ar: "ما يقوله الميزان الفضائي (إقليمي)", en: "What the space scale says (regional)" },
  ledger_right: { ar: "ما نستطيع تفسيره", en: "What we can explain" },
  ledger_grace: { ar: "فقد GRACE الإقليمي", en: "GRACE regional loss" },
  ledger_recharge: { ar: "التغذية المقدّرة", en: "Estimated recharge" },
  ledger_documented: { ar: "سحب موثّق", en: "Documented abstraction" },
  ledger_detected: { ar: "ET الحقول المكتشفة", en: "Detected fields ET" },
  ledger_unknown: { ar: "العجز المجهول", en: "Unknown deficit" },
  ledger_unit: { ar: "مليون م³/سنة", en: "MCM/yr" },
  exploitation: { ar: "نسبة الاستغلال", en: "Exploitation" },
  closure_year: { ar: "سنة الإغلاق القانوني", en: "Legal closure year" },
  closure_logic: {
    ar: "الحوض مغلق قانونياً منذ 1992 — أي توسّع مروي جديد بعد الإغلاق يستلزم سحباً جديداً أو تجاوزاً للحصص، وكلاهما يستوجب التفتيش",
    en: "Legally closed since 1992 — any new irrigated expansion implies new abstraction or quota violation; both warrant inspection",
  },

  // ---- الشاشة 3: الطابور
  queue_title: { ar: "طابور التفتيش", en: "Inspection Queue" },
  queue_sub: { ar: "قلب المنتج — مرشّحات لا اتهامات: المفتّش يقرر، النظام يوجّه عينه", en: "The product core — filters, not accusations: the inspector decides, the system aims their eyes" },
  col_rank: { ar: "الرتبة", en: "Rank" },
  col_id: { ar: "المعرف", en: "ID" },
  col_gps: { ar: "GPS", en: "GPS" },
  col_area: { ar: "المساحة (هكتار)", en: "Area (ha)" },
  col_first_seen: { ar: "الظهور الأول", en: "First seen" },
  col_volume: { ar: "م³/سنة (نطاق)", en: "m³/yr (range)" },
  col_score: { ar: "الدرجة", en: "Score" },
  col_status: { ar: "الحالة", en: "Status" },
  col_evidence: { ar: "الدليل", en: "Evidence" },
  filter_basin: { ar: "الحوض", en: "Basin" },
  filter_min_score: { ar: "حد الدرجة الأدنى", en: "Min score" },
  filter_status: { ar: "الحالة", en: "Status" },
  filter_flag: { ar: "العَلَم", en: "Flag" },
  all: { ar: "الكل", en: "All" },
  status_new: { ar: "جديد", en: "New" },
  status_inspected: { ar: "تم التفتيش", en: "Inspected" },
  status_confirmed: { ar: "مؤكَّد", en: "Confirmed" },
  status_cleared: { ar: "بريء", en: "Cleared" },
  flag_new: { ar: "جديد بعد الإغلاق", en: "New after closure" },
  flag_expanding: { ar: "يتوسّع", en: "Expanding" },
  flag_stable: { ar: "مستقر", en: "Stable" },
  results_count: { ar: "نتيجة", en: "results" },

  // ---- بانل الدليل
  evidence_title: { ar: "بانل الدليل", en: "Evidence Panel" },
  ndvi_vs_rain: { ar: "بصمة الريّ: NDVI ضد المطر (anti-phase)", en: "Irrigation fingerprint: NDVI vs rain (anti-phase)" },
  ndvi_note: {
    ar: "أخضر في صيف بلا مطر = ريّ جوفي — لا تفسير آخر فيزيائياً",
    en: "Green in a rainless summer = groundwater irrigation — no other physical explanation",
  },
  before_after: { ar: "قبل / بعد", en: "Before / After" },
  illustrative: { ar: "تصوّر توضيحي", en: "Illustrative" },
  score_components: { ar: "مكوّنات درجة الاشتباه", en: "Suspicion score components" },
  sc_inside: { ar: "داخل حوض محمي", en: "Inside protected basin" },
  sc_new: { ar: "جديد بعد الإغلاق", en: "New after closure" },
  sc_persistence: { ar: "استمرارية النشاط", en: "Activity persistence" },
  sc_area: { ar: "المساحة", en: "Area" },
  sc_expansion: { ar: "معدل التوسّع", en: "Expansion rate" },
  smap_confirm: { ar: "توكيد مستقل: رطوبة الجذور SMAP", en: "Independent confirmation: SMAP root-zone moisture" },
  smap_note: {
    ar: "رطوبة جذور عالية مستمرة في أشهر صفر-مطر = توكيد ريّ مستقل عن NDVI",
    en: "Sustained high root-zone moisture in zero-rain months = irrigation confirmation independent of NDVI",
  },
  update_status: { ar: "تحديث الحالة (المفتّش)", en: "Update status (inspector)" },
  mark_inspected: { ar: "تم التفتيش", en: "Mark inspected" },
  mark_confirmed: { ar: "تأكيد المخالفة", en: "Confirm violation" },
  mark_cleared: { ar: "إخلاء (بريء)", en: "Clear (innocent)" },
  status_saved_local: { ar: "حُفظت محلياً (وضع العرض)", en: "Saved locally (demo mode)" },
  status_saved_api: { ar: "حُفظت في قاعدة البيانات", en: "Saved to database" },
  anti_phase: { ar: "بصمة الريّ", en: "Anti-phase score" },
  persistence_months: { ar: "أشهر النشاط/سنة", en: "Active months/yr" },
  rain: { ar: "مطر CHIRPS (مم)", en: "CHIRPS rain (mm)" },

  // ---- الشاشة 4: الأثر
  impact_title: { ar: "عدّاد الأثر", en: "Impact Counter" },
  impact_sub: {
    ar: "نطاق بافتراضات معلنة — لا رقم واحد (potential recoverable under stated assumptions)",
    en: "A range under stated assumptions — not a single number",
  },
  recoverable_m3: { ar: "م³ قابلة للاسترجاع سنوياً", en: "Recoverable m³ per year" },
  people_equiv: { ar: "مكافئ الأشخاص (مياه سنة)", en: "People equivalent (a year of water)" },
  money_equiv: { ar: "مكافئ بالدولار (كلفة تحلية بديلة)", en: "USD equivalent (avoided desalination)" },
  confirmation_rate: { ar: "معدل تأكيد التفتيش (افتراض معلَن)", en: "Inspection confirmation rate (stated assumption)" },
  scenario_conservative: { ar: "متحفّظ", en: "Conservative" },
  scenario_expected: { ar: "متوسط", en: "Expected" },
  carrier_compare: { ar: "مقارنة مع الناقل الوطني", en: "vs National Carrier" },
  carrier_line: {
    ar: "الضخّ الجائر السنوي (205 مليون م³) = 68% ≈ ثلثا إنتاج مشروع التحلية الوطني بـ6 مليارات دولار",
    en: "Annual overdraft (205 MCM) = 68% ≈ two-thirds of the $6bn National Carrier's output",
  },
  manual_line: {
    ar: "اليدوي اليوم: ردم 201 بئر في 2023/24 وفّر 62 مليون م³ (يعادل 21% من إنتاج المشروع)",
    en: "Manual today: sealing 201 wells in 2023/24 saved 62 MCM (≈21% of the Carrier's output)",
  },
  people_method: {
    ar: "معادلة الوزارة نفسها: 42.9 م.م³ ≈ 160 ألف شخص → 1 مليون م³ ≈ ~3,730 شخصاً لسنة",
    en: "The ministry's own equation: 42.9 MCM ≈ 160k people → 1 MCM ≈ ~3,730 people-years",
  },
  money_method: {
    ar: "المنهجية معلنة: م³ × كلفة التحلية البديلة 0.5–0.7$ — تقديرية",
    en: "Stated methodology: m³ × alternative desalination cost $0.5–0.7 — estimate",
  },
  detected_from: { ar: "من", en: "from" },
  fields_detected_short: { ar: "حقلاً مكتشفاً", en: "detected fields" },

  // ---- التحقّق P7
  validation_title: { ar: "التحقّق بالواقع — مواقع إنفاذ حقيقية", en: "Ground-truthing — real enforcement sites" },
  validation_sub: {
    ar: "تطابق حالات (case-study concordance) — لا precision/recall إحصائي على عيّنة إخبارية منحازة",
    en: "Case-study concordance — not statistical precision/recall on a biased news sample",
  },
  in_methodology: { ar: "داخل المنهجية (منطق صحراوي)", en: "In methodology (desert logic)" },
  out_methodology: { ar: "خارج المنهجية — بشفافية", en: "Out of methodology — transparently" },
  hits: { ar: "تطابق", en: "hits" },
  threshold: { ar: "العتبة المعلَنة", en: "Declared threshold" },
  lift: { ar: "معامل الإثراء (lift)", en: "Enrichment factor (lift)" },
  red_area: { ar: "نسبة المساحة الحمراء", en: "Red area share" },
  precision20: { ar: "precision@20 (طابور التفتيش)", en: "precision@20 (queue)" },

  // ---- المنهجية
  meth_title: { ar: "المنهجية والمصادر والحدود", en: "Methodology, Sources & Limits" },
  meth_engines: { ar: "ثلاثة محرّكات + لوحة", en: "Three engines + dashboard" },
  meth_datasets: { ar: "الداتاستات", en: "Datasets" },
  meth_limits: { ar: "الحدود الخمسة — الصراحة سلاح", en: "The five limits — candor is a weapon" },
  meth_model_card: { ar: "بطاقة النموذج (Model Card)", en: "Model Card" },
  meth_refs: { ar: "المراجع الرئيسية", en: "Key references" },
  meth_ai: { ar: "الإفصاح عن الذكاء الاصطناعي", en: "AI disclosure" },
  meth_ai_text: {
    ar: "بُني ميزان بمساعدة مكثّفة من Claude (Anthropic) في الكود والتصميم والوثائق — نفصح بفخر لا نخفي. القرارات العلمية والأرقام تتبع مصادرها الموثّقة حصراً.",
    en: "MIZAN was built with extensive help from Claude (Anthropic) for code, design and docs — disclosed proudly. Scientific decisions and numbers trace exclusively to documented sources.",
  },

  // ---- الطبقات والقمر الصناعي (إعادة التصميم)
  basemap_satellite: { ar: "قمر صناعي (NASA)", en: "Satellite (NASA)" },
  basemap_dark: { ar: "خريطة داكنة", en: "Dark map" },
  layers: { ar: "الطبقات", en: "Layers" },
  layer_suspect: { ar: "حقول مشبوهة", en: "Suspect fields" },
  layer_basins_risk: { ar: "أحواض الخطر", en: "Risk basins" },
  layer_real_imagery: { ar: "صور NASA حيّة", en: "Live NASA imagery" },
  nasa_live_badge: { ar: "صور NASA حيّة", en: "Live NASA imagery" },
  real_nasa: { ar: "بيانات NASA حقيقية", en: "Real NASA data" },
  layer_heatmap: { ar: "خريطة حرارة الاشتباه", en: "Suspicion heatmap" },
  live_sat: { ar: "قمر مباشر (آخر 48س)", en: "Live satellite (48h)" },
  sc_ml_anomaly: { ar: "مؤشر شذوذ AI", en: "AI anomaly" },
  sc_ml_supporting: { ar: "مساند · IsolationForest", en: "supporting · IsolationForest" },
  live_sat_on: { ar: "بث حي", en: "LIVE" },
  basemap_follows_year: { ar: "خلفية القمر تتبع السنة المختارة", en: "Basemap follows selected year" },
  growth_play: { ar: "▶ شاهد الزحف الأخضر", en: "▶ Watch the green crawl" },
  growth_stop: { ar: "⏸ إيقاف", en: "⏸ Stop" },
  growth_caption: { ar: "الحقول تظهر بسنة أول رصد (Sentinel-2/HLS)", en: "Fields appear by first-detection year (Sentinel-2/HLS)" },
  tm_autoplay: { ar: "▶ تشغيل", en: "▶ Play" },
  tm_autoplay_stop: { ar: "⏸ إيقاف", en: "⏸ Pause" },
  real_s2_thumb: { ar: "حقيقي · Sentinel-2", en: "Real · Sentinel-2" },
  growth_chart_title: { ar: "نمو الزحف الأخضر — هكتارات تراكمية", en: "Green-crawl growth — cumulative hectares" },
  growth_fields_label: { ar: "حقل مكشوف", en: "fields detected" },

  // ---- لوحة الاستراتيجية (إلهام التصميم — mockup 2)
  kpi_performance: { ar: "مؤشرات الأداء", en: "KPI Performance" },
  strategic_issues: { ar: "القضايا الاستراتيجية", en: "Strategic Issues" },
  recommendation: { ar: "التوصية", en: "Recommendation" },
  high_priority_zones: { ar: "مناطق أولوية قصوى", en: "High-priority zones" },
  median_risk_zones: { ar: "مناطق خطر متوسط", en: "Median-risk zones" },
  national_deficit: { ar: "العجز المائي الوطني", en: "National water deficit" },
  overdraft_rate: { ar: "معدل الضخّ الجائر", en: "Overdraft rate" },
  alert_status: { ar: "حالة الإنذار", en: "Alert status" },
  rec_azraq: { ar: "ركّزوا الإنفاذ على حوض الأزرق", en: "Focus enforcement on Azraq Basin" },
  rec_azraq_sub: { ar: "أعلى كثافة 🔴 + مغلق قانونياً + استرجاع أكبر لكل عملية", en: "Highest 🔴 density + legally closed + max recovery per operation" },
  issue_closure: { ar: "إنفاذ إغلاق الأزرق", en: "Enforce Azraq closure" },
  issue_recharge: { ar: "تدابير تغذية ذات أولوية", en: "Prioritized recharge measures" },
  issue_conservation: { ar: "تدابير حفظ ذات أولوية", en: "Prioritized conservation" },
  issue_targeting: { ar: "استهداف الآبار الكبرى أولاً", en: "Target largest wells first" },

  // ---- آلة الزمن السينمائية (mockup 1)
  satellite_time_machine: { ar: "آلة الزمن الفضائية", en: "Satellite Time Machine" },
  before: { ar: "قبل", en: "before" },
  after: { ar: "بعد", en: "after" },
  intelligence: { ar: "التحليل", en: "Intelligence" },
  recharge_rate: { ar: "معدل التغذية الجوفية", en: "Groundwater recharge rate" },
  well_detections: { ar: "كشوف آبار غير مرخّصة", en: "Unauthorized well detections" },
  risk_matrix: { ar: "مصفوفة الخطر", en: "Risk matrix" },
  historical_water: { ar: "منسوب الماء التاريخي", en: "Historical water level" },
  real_imagery_caption: {
    ar: "صور MODIS/VIIRS حقيقية من NASA GIBS — الصحراء تخضرّ فوق الضخّ الجوفي",
    en: "Real MODIS/VIIRS imagery from NASA GIBS — the desert greens over groundwater pumping",
  },
} as const;

export type DictKey = keyof typeof dict;

interface LangCtx {
  lang: Lang;
  setLang: (l: Lang) => void;
  t: (k: DictKey) => string;
}

const Ctx = createContext<LangCtx>({ lang: "ar", setLang: () => {}, t: (k) => String(k) });

export function LangProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLang] = useState<Lang>("ar");

  useEffect(() => {
    const saved = (typeof window !== "undefined" && localStorage.getItem("mizan_lang")) as Lang | null;
    if (saved === "en" || saved === "ar") setLang(saved);
  }, []);

  useEffect(() => {
    document.documentElement.dir = lang === "ar" ? "rtl" : "ltr";
    document.documentElement.lang = lang;
    if (typeof window !== "undefined") localStorage.setItem("mizan_lang", lang);
  }, [lang]);

  const t = (k: DictKey) => dict[k]?.[lang] ?? String(k);
  return <Ctx.Provider value={{ lang, setLang, t }}>{children}</Ctx.Provider>;
}

export function useLang() {
  return useContext(Ctx);
}
