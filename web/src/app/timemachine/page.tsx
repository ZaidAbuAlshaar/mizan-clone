"use client";
/**
 * آلة الزمن الفضائية — شاشة سينمائية (إلهام التصميم mockup 1)
 * صور NASA GIBS حقيقية (MODIS TrueColor) قبل/بعد + سحّاب + لوحة التحليل + مصفوفة الخطر + منسوب الماء.
 */
import { useEffect, useMemo, useRef, useState } from "react";
import {
  Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import type { ClimateData, FieldsFC, Forecast, NasaManifest, TimeMachineData } from "@/lib/types";
import { getClimate, getFields, getForecast, getNasa, getTimeMachine } from "@/lib/api";
import { useLang } from "@/lib/i18n";
import { fmt } from "@/lib/format";
import RiskMatrix from "@/components/RiskMatrix";
import { DemoBadge } from "@/components/Badges";

const FALLBACK_YEARS = [2016, 2018, 2020, 2022, 2024];

export default function TimeMachinePage() {
  const { t, lang } = useLang();
  const [nasa, setNasa] = useState<NasaManifest | null>(null);
  const [tm, setTm] = useState<TimeMachineData | null>(null);
  const [fields, setFields] = useState<FieldsFC | null>(null);
  const [forecast, setForecast] = useState<Forecast | null>(null);
  const [climate, setClimate] = useState<ClimateData | null>(null);
  const [split, setSplit] = useState(50);
  const [yearIdx, setYearIdx] = useState(FALLBACK_YEARS.length - 1);
  const [playing, setPlaying] = useState(false);
  const playRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    getNasa().then(setNasa).catch(() => {});
    getTimeMachine().then(setTm).catch(() => {});
    getFields({ basin: "azraq" }).then(setFields).catch(() => {});
    getForecast("azraq").then(setForecast).catch(() => {});
    getClimate().then(setClimate).catch(() => {});
  }, []);

  // السنوات من المانيفست (تشمل أي سنوات جديدة من Sentinel-2) مع fallback
  const YEARS = useMemo(() => {
    const ys = nasa ? Object.keys(nasa.time_machine.years).map(Number).filter((y) => y > 2016).sort((a, b) => a - b) : null;
    return ys && ys.length ? ys : FALLBACK_YEARS.slice(1);
  }, [nasa]);
  useEffect(() => setYearIdx(YEARS.length - 1), [YEARS]);

  // تشغيل تلقائي سينمائي: يمرّ على السنوات ويكشفها تدريجياً
  function togglePlay() {
    if (playRef.current) {
      clearInterval(playRef.current);
      playRef.current = null;
      setPlaying(false);
      return;
    }
    setPlaying(true);
    setSplit(38);
    let i = 0;
    setYearIdx(0);
    playRef.current = setInterval(() => {
      i += 1;
      if (i >= YEARS.length) {
        if (playRef.current) clearInterval(playRef.current);
        playRef.current = null;
        setPlaying(false);
        return;
      }
      setYearIdx(i);
    }, 1500);
  }
  useEffect(() => () => { if (playRef.current) clearInterval(playRef.current); }, []);

  const afterYear = YEARS[Math.min(yearIdx, YEARS.length - 1)];
  const beforeImg = nasa?.time_machine.years["2016"];
  const afterImg = nasa?.time_machine.years[String(afterYear)];
  const stats = tm?.years[String(afterYear)];

  // كشوف الآبار حتى السنة المختارة (من مخرجات الكشف)
  const detections = useMemo(() => {
    if (!fields) return 0;
    return fields.features.filter((f) => f.properties.first_seen_year <= afterYear).length;
  }, [fields, afterYear]);

  return (
    <div className="space-y-3">
      {/* العنوان السينمائي */}
      <div className="relative flex flex-col items-center justify-center py-4 text-center">
        <span className="text-xs font-bold uppercase tracking-[0.3em] text-ink-mute">{t("satellite_time_machine")}</span>
        <h1 dir="ltr" className="kpi-number mt-1 text-hero text-gold glow-text">
          2016 <span className="text-ink-dim">→</span> {afterYear}
        </h1>
        <span className="mt-1 inline-flex items-center gap-1.5 rounded-full border border-flag-green/40 bg-flag-green/10 px-3 py-1 text-[11px] font-bold text-flag-green">
          ● {t("nasa_live_badge")} · {nasa?.time_machine.label ?? "NASA GIBS · MODIS"}
        </span>
      </div>

      <div className="grid gap-3 lg:grid-cols-[1fr_330px]">
        {/* مسرح الصور قبل/بعد */}
        <div className="panel relative overflow-hidden p-0">
          <div className="relative h-[58vh] min-h-[420px] w-full select-none" dir="ltr">
            {afterImg && (
              <img key={afterImg} src={afterImg} alt={`Azraq ${afterYear}`} className="absolute inset-0 h-full w-full animate-fade-in object-cover" draggable={false} />
            )}
            {beforeImg && (
              <div className="absolute inset-0 overflow-hidden" style={{ clipPath: `inset(0 ${100 - split}% 0 0)` }}>
                <img src={beforeImg} alt="Azraq 2016" className="h-full w-full object-cover" draggable={false} />
              </div>
            )}
            {/* مقبض السحب */}
            <div className="pointer-events-none absolute inset-y-0 z-10 w-0.5 bg-gold shadow-glow-gold" style={{ left: `${split}%` }}>
              <div className="absolute top-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full border border-gold bg-space-950/90 px-2 py-1 text-[10px] font-bold text-gold">⇄</div>
            </div>
            {/* ملصقات قبل/بعد */}
            <span className="absolute left-3 top-3 rounded-lg bg-space-950/80 px-2.5 py-1 text-xs font-bold text-ink-dim backdrop-blur">{t("before")} · 2016</span>
            <span className="absolute right-3 top-3 rounded-lg bg-space-950/80 px-2.5 py-1 text-xs font-bold text-gold backdrop-blur">{t("after")} · {afterYear}</span>
            {/* خط مسح سينمائي */}
            <div className="pointer-events-none absolute inset-0 overflow-hidden opacity-30">
              <div className="h-12 w-full bg-gradient-to-b from-transparent via-teal-glow/20 to-transparent animate-scan" />
            </div>
            <span className="absolute bottom-3 left-1/2 -translate-x-1/2 rounded-lg bg-space-950/80 px-3 py-1 text-[11px] text-ink-dim backdrop-blur">
              {t("real_imagery_caption")}
            </span>
          </div>
          {/* سحّاب الانقسام */}
          <div className="px-4 py-3">
            <input type="range" min={2} max={98} value={split} onChange={(e) => setSplit(Number(e.target.value))} className="mizan-range" dir="ltr" />
          </div>
        </div>

        {/* لوحة التحليل */}
        <div className="space-y-3">
          <div className="panel p-4">
            <h3 className="mb-3 font-head text-sm font-extrabold uppercase tracking-wide text-ink-dim">{t("intelligence")}</h3>
            <div className="space-y-3 text-sm">
              <div className="flex items-center justify-between border-b border-space-700/60 pb-2">
                <span className="text-xs text-ink-dim">{t("well_detections")}</span>
                <span className="kpi-number text-2xl text-flag-red">{detections}</span>
              </div>
              <div className="flex items-center justify-between border-b border-space-700/60 pb-2">
                <span className="text-xs text-ink-dim">{t("detected_hectares")}</span>
                <span className="kpi-number text-2xl text-gold">{stats ? fmt(stats.total_ha) : "—"}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-ink-dim">{t("recharge_rate")}</span>
                <span className="kpi-number text-xl text-flag-orange">{climate ? climate.rain_proof.mean_summer_mm : "—"}<span className="text-[10px] text-ink-mute"> mm/{lang === "ar" ? "صيف" : "summer"}</span></span>
              </div>
            </div>
          </div>

          <div className="panel p-4">
            <RiskMatrix fields={fields} />
          </div>

          {/* منسوب الماء التاريخي المصغّر */}
          {forecast && (
            <div className="panel p-4">
              <div className="mb-1 text-[11px] font-bold uppercase tracking-wide text-ink-dim">{t("historical_water")}</div>
              <MiniWaterLevel rate={forecast.well_level.rate_m_per_yr} />
              <p className="mt-1 text-[10px] text-ink-mute">
                {lang === "ar" ? "قياسات آبار الوزارة — الأزرق −20م (2000–2017)" : "Ministry wells — Azraq −20m (2000–2017)"}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* شريط الزمن السفلي + التشغيل التلقائي */}
      <div className="panel p-4">
        <div className="flex items-center gap-3" dir="ltr">
          <button
            onClick={togglePlay}
            className={`shrink-0 rounded-pill border px-4 py-1.5 text-xs font-bold transition-colors ${
              playing
                ? "border-flag-red/50 bg-flag-red/15 text-flag-red"
                : "border-teal-glow/40 bg-space-950/70 text-teal-glow hover:bg-teal-glow/10"
            }`}
          >
            {playing ? t("tm_autoplay_stop") : t("tm_autoplay")}
          </button>
          <input
            type="range" min={0} max={YEARS.length - 1} step={1} value={Math.min(yearIdx, YEARS.length - 1)}
            onChange={(e) => setYearIdx(Number(e.target.value))} className="mizan-range" dir="ltr"
          />
        </div>
        <div dir="ltr" className="mt-2 flex justify-between text-xs">
          {YEARS.map((y, i) => (
            <button
              key={y}
              onClick={() => setYearIdx(i)}
              className={`rounded px-2 py-0.5 font-bold transition-colors ${i === yearIdx ? "text-gold" : "text-ink-mute hover:text-ink-dim"}`}
            >
              {y}
            </button>
          ))}
        </div>
      </div>

      {/* إحصائية النمو — هكتارات تراكمية وحقول بسنة أول رصد (من الكشف الحقيقي) */}
      <GrowthChart fields={fields} highlightYear={afterYear} />

      <div className="flex justify-center"><DemoBadge /></div>
    </div>
  );
}

/** نمو الزحف الأخضر — تراكمي من first_seen_year الحقيقية (Sentinel-2/HLS) */
function GrowthChart({ fields, highlightYear }: { fields: FieldsFC | null; highlightYear: number }) {
  const { t, lang } = useLang();
  const data = useMemo(() => {
    if (!fields) return [];
    const years = Array.from({ length: 2026 - 2016 + 1 }, (_, i) => 2016 + i);
    return years.map((y) => {
      const upto = fields.features.filter((f) => f.properties.first_seen_year <= y);
      return {
        year: y,
        ha: Math.round(upto.reduce((s, f) => s + f.properties.area_ha, 0)),
        fields: upto.length,
      };
    });
  }, [fields]);
  if (!data.length) return null;
  const latest = data[data.length - 1];
  const at2018 = data.find((d) => d.year === 2018);
  return (
    <div className="panel p-4">
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <h3 className="font-head text-sm font-extrabold text-teal-glow">📈 {t("growth_chart_title")}</h3>
        <span className="text-[11px] text-ink-mute">
          {lang === "ar"
            ? `${fmt(latest.ha)} هكتاراً اليوم · +${fmt(latest.ha - (at2018?.ha ?? 0))} منذ 2018`
            : `${fmt(latest.ha)} ha today · +${fmt(latest.ha - (at2018?.ha ?? 0))} since 2018`}
        </span>
      </div>
      <div dir="ltr" className="h-44 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 6, right: 8, bottom: 0, left: -14 }}>
            <defs>
              <linearGradient id="growthFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#E9B949" stopOpacity={0.5} />
                <stop offset="100%" stopColor="#E9B949" stopOpacity={0.04} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="#272727" strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="year" tick={{ fill: "#5E5E5E", fontSize: 10 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: "#5E5E5E", fontSize: 10 }} axisLine={false} tickLine={false} />
            <Tooltip
              contentStyle={{ background: "#161616", border: "1px solid #272727", borderRadius: 12, fontSize: 12 }}
              labelStyle={{ color: "#B9B9B9" }}
              formatter={(v: number, name: string) =>
                name === "ha" ? [`${fmt(v)} ha`, lang === "ar" ? "هكتارات" : "hectares"]
                              : [v, lang === "ar" ? "حقول" : "fields"]}
            />
            <Area type="monotone" dataKey="ha" stroke="#E9B949" strokeWidth={2} fill="url(#growthFill)" animationDuration={900} />
            <Area type="monotone" dataKey="fields" stroke="#2DD4BF" strokeWidth={1.4} fill="transparent" animationDuration={900} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      <p className="mt-1 text-[10px] text-ink-mute">
        {t("growth_caption")} · {lang === "ar" ? `حتى ${highlightYear}: ` : `up to ${highlightYear}: `}
        <b className="text-gold num">{fmt(data.find((d) => d.year === highlightYear)?.ha ?? latest.ha)}</b> ha
      </p>
    </div>
  );
}

function MiniWaterLevel({ rate }: { rate: number }) {
  // منحنى هابط بسيط من −20م 2017 بمعدل rate — SVG خفيف
  const pts: string[] = [];
  for (let i = 0; i <= 24; i++) {
    const x = (i / 24) * 100;
    const level = -(20 * (i / 24)) + (i > 17 ? rate * 0 : 0);
    const y = 8 + (Math.abs(level) / 24) * 40;
    pts.push(`${x},${y}`);
  }
  return (
    <svg viewBox="0 0 100 56" className="h-16 w-full" preserveAspectRatio="none">
      <polyline points={pts.join(" ")} fill="none" stroke="#38BDF8" strokeWidth="1.4" />
      <line x1="0" y1="48" x2="100" y2="48" stroke="#F43F5E" strokeWidth="0.6" strokeDasharray="2 2" opacity="0.6" />
    </svg>
  );
}
