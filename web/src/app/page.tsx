"use client";
/** الشاشة 1 — لوحة القيادة (طراز Dark Mood): هيرو الحوض + خريطة قمر صناعي NASA حيّة + بلاطات المؤشرات */
import { useEffect, useMemo, useState } from "react";
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
  const [layers, setLayers] = useState({ fields: true, basins: true, validation: false });

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
    <div className="grid gap-3 xl:grid-cols-[1fr_320px]">
      {/* العمود الأساسي */}
      <div className="space-y-3">
        {/* هيرو: خريطة القمر الصناعي الحيّة + شريحة حالة الحوض العائمة */}
        <div className="relative">
          <MapView
            fields={fields}
            basins={layers.basins ? basins : null}
            exclusions={exclusions}
            validationSites={layers.validation && validation ? validation.sites : []}
            onFieldClick={(id) => router.push(`/queue?focus=${id}`)}
            className="h-[64vh] min-h-[460px]"
            showBasinLabels
            basemap={basemap}
            showFields={layers.fields}
          />
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
            <LayerPanel basemap={basemap} onBasemap={setBasemap} layers={layers} onToggle={(k) => setLayers((s) => ({ ...s, [k]: !s[k] }))} />
          </div>
          {basemap === "satellite" && (
            <span className="absolute end-4 top-4 z-10 inline-flex items-center gap-1 rounded-pill border border-flag-green/40 bg-space-950/80 px-3 py-1.5 text-[11px] font-bold text-flag-green backdrop-blur">
              🛰 {t("nasa_live_badge")}
            </span>
          )}
        </div>

        {/* أبرز المؤشرات (Today's Highlight) */}
        <div className="panel p-5">
          <h2 className="mb-4 font-head text-xl font-extrabold text-ink">{lang === "ar" ? "أبرز المؤشرات" : "Today's Highlights"}</h2>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            <MetricTile
              icon={<TileIcon d="M12 21s7-6.5 7-11a7 7 0 1 0-14 0c0 4.5 7 11 7 11Z M12 7v3" />}
              label={t("high_priority_zones")} value={stats ? stats.reds : "—"} accent="#F43F5E"
              sub={lang === "ar" ? "حقول 🔴 درجة ≥70" : "fields 🔴 score ≥70"} href="/queue"
            />
            <MetricTile
              icon={<TileIcon circle />} label={t("median_risk_zones")} value={stats ? stats.oranges : "—"} accent="#F59E0B"
              sub={lang === "ar" ? "حقول 🟠 40–69" : "fields 🟠 40–69"} href="/queue"
            />
            <MetricTile
              icon={<TileIcon d="M4 19h16M8 16v-4M12 16V8M16 16v-7" />} label={t("est_recoverable")}
              value={stats ? fmtMcm(stats.m3mid, lang) : "—"} accent="#2DD4BF" sub={lang === "ar" ? "نطاق أوسط" : "mid range"} href="/impact"
            />
            <MetricTile
              icon={<TileIcon d="M12 2v6m0 0 3-2m-3 2L9 6 M5 14a7 7 0 1 0 14 0c0-3-3-7-7-10-4 3-7 7-7 10Z" />}
              label={lang === "ar" ? "مطر الصيف (NASA حقيقي)" : "Summer rain (real NASA)"}
              value={climate ? climate.rain_proof.mean_summer_mm : "—"} unit="mm" accent="#E9B949"
              sub={lang === "ar" ? "أي خُضرة صيفية = ضخّ" : "any summer green = pumping"} href="/timemachine"
              badge={<span className="rounded-full border border-flag-green/40 bg-flag-green/10 px-2 py-0.5 text-[9px] font-bold text-flag-green">NASA</span>}
            />
            <MetricTile
              icon={<TileIcon d="M3 12h18M12 3v18" />} label={t("national_deficit")}
              value={c ? `−${c.overdraft_mcm}` : "—"} unit="MCM" accent="#F43F5E"
              sub={lang === "ar" ? "ضخّ جائر فوق الآمن (MWI)" : "overdraft above safe (MWI)"} href="/impact"
            />
            <MetricTile
              icon={<TileIcon d="M4 19V5m0 14h16M7 14l3-3 3 2 4-5" />} label={t("overdraft_rate")}
              value={c ? c.national_abstraction_pct : "—"} unit="%" accent="#F59E0B"
              sub={lang === "ar" ? "السحب الوطني/الآمن" : "national/safe yield"} href="/methodology"
            />
          </div>
        </div>
      </div>

      {/* العمود الجانبي */}
      <aside className="space-y-3">
        <StrategicPanel impact={impact} />
        <div className="panel p-4">
          <div className="mb-2 flex items-center justify-between">
            <h2 className="text-sm font-bold text-ink">{t("top_alerts")}</h2>
            <Link href="/queue" className="text-[11px] text-teal-glow hover:underline">{t("view_queue")} ←</Link>
          </div>
          <ul className="space-y-1">
            {alerts.slice(0, 6).map((a) => (
              <li key={a.id}>
                <Link href={`/queue?focus=${a.id}`} className="flex items-center justify-between rounded-tile px-2 py-2 text-xs transition-colors hover:bg-space-700">
                  <span className="flex items-center gap-2"><TierDot tier={a.tier} /><span dir="ltr" className="num">{a.id}</span></span>
                  <span className="num text-ink-dim">{a.area_ha} ha · <b style={{ color: "#F43F5E" }}>{a.score}</b></span>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      </aside>
    </div>
  );
}
