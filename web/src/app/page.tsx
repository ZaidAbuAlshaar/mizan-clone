"use client";
/** الشاشة 1 — لوحة القيادة (طراز Dark Mood): هيرو الحوض + خريطة قمر صناعي NASA حيّة + بلاطات المؤشرات */
import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import MapView, { Basemap } from "@/components/MapView";
import LayerPanel from "@/components/LayerPanel";
import StrategicPanel from "@/components/StrategicPanel";
import { MetricTile, TileIcon } from "@/components/Tile";
import { DemoBadge, TierDot } from "@/components/Badges";
import {
  getAlerts, getBasins, getClimate, getExclusions, getFields, getImpact, getMeta, getValidation,
} from "@/lib/api";
import type { AlertItem, BasinsFC, ClimateData, FieldsFC, ImpactData, ValidationData } from "@/lib/types";
import { useLang } from "@/lib/i18n";
import { fmt, fmtMcm } from "@/lib/format";

export default function NationalMapPage() {
  const { t, lang } = useLang();
  const router = useRouter();
  const [fields, setFields] = useState<FieldsFC | null>(null);
  const [basins, setBasins] = useState<BasinsFC | null>(null);
  const [exclusions, setExclusions] = useState<GeoJSON.FeatureCollection | null>(null);
  const [validation, setValidation] = useState<ValidationData | null>(null);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [impact, setImpact] = useState<ImpactData | null>(null);
  const [climate, setClimate] = useState<ClimateData | null>(null);
  const [basemap, setBasemap] = useState<Basemap>("satellite");
  const [layers, setLayers] = useState({ fields: true, basins: true, validation: false, heatmap: false });
  // بث القمر الحي — آخر تمريرة VIIRS متاحة على GIBS (أمس الأول ضماناً للتوافر)
  const [satLive, setSatLive] = useState(false);
  const liveDate = useMemo(() => new Date(Date.now() - 2 * 86400000).toISOString().slice(0, 10), []);
  const satDate = satLive ? liveDate : "2024-08-12";
  // أنيميشن الزحف الأخضر — الحقول تظهر بسنة أول رصد
  const [growthYear, setGrowthYear] = useState<number | null>(null);
  const playRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const playing = growthYear != null;

  function toggleGrowth() {
    if (playRef.current) {
      clearInterval(playRef.current);
      playRef.current = null;
      setGrowthYear(null);
      return;
    }
    let y = 2016;
    setGrowthYear(y);
    playRef.current = setInterval(() => {
      y += 1;
      if (y > 2026) {
        if (playRef.current) clearInterval(playRef.current);
        playRef.current = null;
        setTimeout(() => setGrowthYear(null), 1600);
        return;
      }
      setGrowthYear(y);
    }, 750);
  }
  useEffect(() => () => { if (playRef.current) clearInterval(playRef.current); }, []);

  useEffect(() => {
    getFields().then(setFields).catch(console.error);
    getBasins().then(setBasins).catch(console.error);
    getExclusions().then(setExclusions).catch(() => {});
    getValidation().then(setValidation).catch(() => {});
    getAlerts().then(setAlerts).catch(() => {});
    getImpact().then(setImpact).catch(() => {});
    getClimate().then(setClimate).catch(() => {});
  }, []);

  const stats = useMemo(() => {
    if (!fields) return null;
    const p = fields.features.map((f) => f.properties);
    return {
      total: p.length,
      reds: p.filter((x) => x.tier === "red").length,
      oranges: p.filter((x) => x.tier === "orange").length,
      ha: p.reduce((s, x) => s + x.area_ha, 0),
      m3mid: p.reduce((s, x) => s + (x.est_m3_low + x.est_m3_high) / 2, 0),
    };
  }, [fields]);

  const c = impact?.constants;

  return (
    <div className="grid grid-cols-1 gap-3 xl:h-[calc(100vh-92px)] xl:grid-cols-[300px_1fr] xl:overflow-hidden">
      {/* العمود الجانبي (يمين RTL): الاستراتيجية + التنبيهات */}
      <aside className="order-2 flex min-h-0 flex-col gap-3 xl:order-1 xl:overflow-y-auto xl:pe-1">
        <StrategicPanel impact={impact} />
        <div className="panel p-4">
          <div className="mb-2 flex items-center justify-between">
            <h2 className="text-sm font-bold text-ink">{t("top_alerts")}</h2>
            <Link href="/queue" className="text-[11px] text-teal-glow hover:underline">{t("view_queue")} ←</Link>
          </div>
          <ul className="space-y-1">
            {alerts.slice(0, 5).map((a) => (
              <li key={a.id}>
                <Link href={`/queue?focus=${a.id}`} className="flex items-center justify-between rounded-tile px-2 py-1.5 text-xs transition-colors hover:bg-space-700">
                  <span className="flex items-center gap-2"><TierDot tier={a.tier} /><span dir="ltr" className="num">{a.id}</span></span>
                  <span className="num text-ink-dim">{a.area_ha} ha · <b style={{ color: "#F43F5E" }}>{a.score}</b></span>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      </aside>

      {/* العمود الأساسي: الخريطة تملأ المساحة + شريط المؤشرات أسفلها */}
      <div className="order-1 grid min-h-0 grid-rows-[1fr] gap-3 xl:order-2 xl:grid-rows-[1fr_auto]">
        {/* هيرو: خريطة القمر الصناعي الحيّة + شريحة حالة الحوض العائمة */}
        <div className="relative min-h-0">
          <MapView
            fields={fields}
            basins={layers.basins ? basins : null}
            exclusions={exclusions}
            validationSites={layers.validation && validation ? validation.sites : []}
            onFieldClick={(id) => router.push(`/queue?focus=${id}`)}
            className="h-[58vh] min-h-[420px] xl:h-full xl:min-h-0"
            showBasinLabels
            basemap={basemap}
            satelliteDate={satDate}
            showFields={layers.fields}
            heatmap={layers.heatmap}
            yearFilter={growthYear}
          />
          {/* عدّاد سنة الزحف الأخضر أثناء التشغيل */}
          {playing && (
            <div className="pointer-events-none absolute left-1/2 top-6 z-10 -translate-x-1/2 text-center">
              <div className="kpi-number text-6xl font-extrabold text-gold glow-text" dir="ltr">{growthYear}</div>
              <div className="mt-1 rounded-pill bg-space-950/80 px-3 py-1 text-[11px] text-ink-dim backdrop-blur">
                {t("growth_caption")} · <b className="text-flag-red num">
                  {fields ? fields.features.filter((f) => f.properties.first_seen_year <= (growthYear ?? 2026)).length : 0}
                </b> {t("growth_fields_label")}
              </div>
            </div>
          )}
          {/* زر الزحف الأخضر */}
          <button
            onClick={toggleGrowth}
            className={`absolute bottom-4 left-1/2 z-10 -translate-x-1/2 rounded-pill border px-4 py-2 text-xs font-bold backdrop-blur transition-colors ${
              playing
                ? "border-flag-red/50 bg-flag-red/15 text-flag-red"
                : "border-teal-glow/40 bg-space-950/80 text-teal-glow hover:bg-teal-glow/10"
            }`}
          >
            {playing ? t("growth_stop") : t("growth_play")}
          </button>
          {/* شريحة الحالة (مثل بطاقة الطقس الرئيسية) */}
          <Link
            href="/basin/azraq"
            className="absolute start-4 top-4 z-10 w-[230px] rounded-card border border-space-600/40 bg-space-950/80 p-4 shadow-cinematic backdrop-blur-md transition-transform hover:-translate-y-0.5"
          >
            <div className="flex items-center justify-between">
              <span className="pill !border-flag-red/30 !bg-flag-red/10 !px-3 !py-1 !text-[11px] !text-flag-red">📍 {t("basin_azraq")}</span>
              <DemoBadge small />
            </div>
            <div className="mt-3 flex items-end gap-1">
              <span className="kpi-number text-5xl text-flag-red">215</span>
              <span className="mb-1 text-xl text-ink-dim">%</span>
            </div>
            <div className="text-xs text-ink-dim">{lang === "ar" ? "من الإنتاج الآمن · مغلق قانونياً" : "of safe yield · legally closed"}</div>
            <div className="mt-2 text-[11px] text-ink-mute">{lang === "ar" ? "MWI 2009 عبر IWMI" : "MWI 2009 via IWMI"}</div>
          </Link>
          {/* لوحة الطبقات (أسفل) */}
          <div className="absolute bottom-4 end-4 z-10 w-[230px]">
            <LayerPanel
              basemap={basemap} onBasemap={setBasemap}
              layers={layers} onToggle={(k) => setLayers((s) => ({ ...s, [k]: !s[k] }))}
              live={satLive} onLive={setSatLive}
            />
          </div>
          {basemap === "satellite" && (
            <span className={`absolute end-4 top-4 z-10 inline-flex items-center gap-1 rounded-pill border px-3 py-1.5 text-[11px] font-bold backdrop-blur ${
              satLive ? "border-flag-red/50 bg-space-950/80 text-flag-red" : "border-flag-green/40 bg-space-950/80 text-flag-green"
            }`}>
              {satLive
                ? <>🔴 {t("live_sat_on")} · VIIRS <span dir="ltr" className="num">{liveDate}</span></>
                : <>🛰 {t("nasa_live_badge")}</>}
            </span>
          )}
        </div>

        {/* شريط أبرز المؤشرات — صفّ مضغوط أسفل الخريطة (يملأ الشاشة بلا scroll) */}
        <div className="grid grid-cols-3 gap-2 lg:grid-cols-6">
          <MetricTile compact
            icon={<TileIcon d="M12 21s7-6.5 7-11a7 7 0 1 0-14 0c0 4.5 7 11 7 11Z M12 7v3" />}
            label={t("high_priority_zones")} value={stats ? stats.reds : "—"} accent="#F43F5E"
            sub={lang === "ar" ? "🔴 درجة ≥70" : "🔴 score ≥70"} href="/queue"
          />
          <MetricTile compact
            icon={<TileIcon circle />} label={t("median_risk_zones")} value={stats ? stats.oranges : "—"} accent="#F59E0B"
            sub={lang === "ar" ? "🟠 40–69" : "🟠 40–69"} href="/queue"
          />
          <MetricTile compact
            icon={<TileIcon d="M4 19h16M8 16v-4M12 16V8M16 16v-7" />} label={t("est_recoverable")}
            value={stats ? fmtMcm(stats.m3mid, lang) : "—"} accent="#2DD4BF" sub={lang === "ar" ? "نطاق أوسط" : "mid range"} href="/impact"
          />
          <MetricTile compact
            icon={<TileIcon d="M5 14a7 7 0 1 0 14 0c0-3-3-7-7-10-4 3-7 7-7 10Z" />}
            label={lang === "ar" ? "مطر الصيف" : "Summer rain"}
            value={climate ? climate.rain_proof.mean_summer_mm : "—"} unit="mm" accent="#E9B949"
            sub={lang === "ar" ? "NASA حقيقي" : "real NASA"} href="/timemachine"
            badge={<span className="rounded-full border border-flag-green/40 bg-flag-green/10 px-1.5 py-0.5 text-[9px] font-bold text-flag-green">NASA</span>}
          />
          <MetricTile compact
            icon={<TileIcon d="M3 12h18M12 3v18" />} label={t("national_deficit")}
            value={c ? `−${c.overdraft_mcm}` : "—"} unit="MCM" accent="#F43F5E"
            sub={lang === "ar" ? "فوق الآمن (MWI)" : "above safe (MWI)"} href="/impact"
          />
          <MetricTile compact
            icon={<TileIcon d="M4 19V5m0 14h16M7 14l3-3 3 2 4-5" />} label={t("overdraft_rate")}
            value={c ? c.national_abstraction_pct : "—"} unit="%" accent="#F59E0B"
            sub={lang === "ar" ? "وطني/آمن" : "national/safe"} href="/methodology"
          />
        </div>
      </div>
    </div>
  );
}
