"use client";
/** الشاشة 2 — تفاصيل الحوض: منحنى GRACE الإقليمي + العتبة الحرجة على مناسيب الآبار + آلة الزمن + دفتر الميزان */
import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import MapView from "@/components/MapView";
import GraceChart from "@/components/GraceChart";
import WellLevelChart from "@/components/WellLevelChart";
import WaterBalanceChart from "@/components/WaterBalanceChart";
import RainProof from "@/components/RainProof";
import TimeMachine from "@/components/TimeMachine";
import LedgerScales from "@/components/LedgerScales";
import { DemoBadge, IllustrativeBadge, RegionalBadge } from "@/components/Badges";
import {
  getBasins, getClimate, getExclusions, getFields, getForecast, getGws, getLedger, getTimeMachine, getTws,
} from "@/lib/api";
import type {
  BasinsFC, ClimateData, FieldsFC, Forecast, GwsSeries, LedgerData, TimeMachineData, TwsSeries,
} from "@/lib/types";
import { useLang } from "@/lib/i18n";
import { fmt } from "@/lib/format";

export default function BasinPage() {
  const { t, lang } = useLang();
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const basinId = params.id || "azraq";

  const [tws, setTws] = useState<TwsSeries | null>(null);
  const [forecast, setForecast] = useState<Forecast | null>(null);
  const [ledger, setLedger] = useState<LedgerData | null>(null);
  const [fields, setFields] = useState<FieldsFC | null>(null);
  const [basins, setBasins] = useState<BasinsFC | null>(null);
  const [exclusions, setExclusions] = useState<GeoJSON.FeatureCollection | null>(null);
  const [tm, setTm] = useState<TimeMachineData | null>(null);
  const [climate, setClimate] = useState<ClimateData | null>(null);
  const [gws, setGws] = useState<GwsSeries | null>(null);
  const [year, setYear] = useState(2026);
  // خلفية القمر تتبع سنة آلة الزمن — 2026 = آخر تمريرة VIIRS حية
  const liveDate = useMemo(() => new Date(Date.now() - 2 * 86400000).toISOString().slice(0, 10), []);
  const satDate = year >= 2026 ? liveDate : `${year}-08-12`;

  useEffect(() => {
    getGws().then(setGws).catch(() => {});
    getTws().then(setTws).catch(console.error);
    getForecast(basinId).then(setForecast).catch(console.error);
    getLedger(basinId).then(setLedger).catch(() => {});
    getFields({ basin: basinId }).then(setFields).catch(console.error);
    getBasins().then(setBasins).catch(() => {});
    getExclusions().then(setExclusions).catch(() => {});
    getTimeMachine().then(setTm).catch(() => {});
    getClimate().then(setClimate).catch(() => {});
  }, [basinId]);

  const basin = basins?.features.find((b) => b.properties.id === basinId)?.properties;

  const hectares = useMemo(() => {
    if (!fields) return 0;
    return fields.features
      .filter((f) => f.properties.first_seen_year <= year)
      .reduce((s, f) => s + f.properties.area_ha, 0);
  }, [fields, year]);

  return (
    <div className="space-y-3">
      {/* الترويسة */}
      <div className="panel flex flex-wrap items-center justify-between gap-3 p-4">
        <div>
          <h1 className="font-head text-2xl font-extrabold glow-text">
            {basin ? (lang === "ar" ? basin.name_ar : basin.name_en) : t("basin_azraq")}
          </h1>
          {basin?.closure_year && (
            <p className="mt-1 max-w-2xl text-xs leading-relaxed text-ink-dim">{t("closure_logic")}</p>
          )}
        </div>
        <div className="flex items-center gap-4">
          {basin?.exploitation_pct && (
            <div className="text-center">
              <div className="kpi-number text-4xl text-flag-red">{basin.exploitation_pct}%</div>
              <div className="text-[10px] text-ink-mute">
                {t("exploitation")} · {basin.exploitation_source}
              </div>
            </div>
          )}
          {basin?.closure_year && (
            <div className="text-center">
              <div className="kpi-number text-4xl text-flag-orange">{basin.closure_year}</div>
              <div className="text-[10px] text-ink-mute">{t("closure_year")}</div>
            </div>
          )}
          <div className="text-center">
            <div className="kpi-number text-4xl text-teal-glow">{fmt(hectares)}</div>
            <div className="text-[10px] text-ink-mute">{t("detected_hectares")} (ha)</div>
          </div>
        </div>
      </div>

      <div className="grid gap-3 xl:grid-cols-2">
        {/* النصف الأول: المنحنيات */}
        <div className="space-y-3">
          <section className="panel p-4">
            <div className="mb-1 flex flex-wrap items-center justify-between gap-2">
              <h2 className="font-head text-lg font-extrabold text-cyanline">
                {tws ? (lang === "ar" ? tws.label_ar : tws.label_en) : t("grace_curve_title")}
              </h2>
              <div className="flex gap-2">
                <RegionalBadge />
                {tws?.is_real
                  ? <span className="inline-flex items-center gap-1 rounded-full border border-flag-green/50 bg-flag-green/10 px-2 py-0.5 text-[10px] font-bold text-flag-green"><span className="h-1.5 w-1.5 rounded-full bg-flag-green" />{lang === "ar" ? "GRACE حقيقي · JPL" : "Real GRACE · JPL"}</span>
                  : <IllustrativeBadge small />}
              </div>
            </div>
            <p className="mb-2 text-[11px] text-ink-mute">{t("grace_subtitle")}</p>
            {tws && forecast ? (
              <GraceChart tws={tws} forecast={forecast} />
            ) : (
              <p className="py-16 text-center text-ink-mute">{t("loading")}</p>
            )}
          </section>

          {/* توكيد مستقل ثانٍ: مخزون GLDAS الجوفي عبر Google Earth Engine */}
          {gws && gws.series.length > 0 && (
            <section className="panel p-4">
              <div className="mb-1 flex flex-wrap items-center justify-between gap-2">
                <h2 className="font-head text-base font-extrabold text-teal-glow">
                  💧 {lang === "ar" ? gws.label_ar : gws.label_en}
                </h2>
                <div className="flex gap-2">
                  <RegionalBadge />
                  <span className="inline-flex items-center gap-1 rounded-full border border-flag-green/50 bg-flag-green/10 px-2 py-0.5 text-[10px] font-bold text-flag-green">
                    <span className="h-1.5 w-1.5 rounded-full bg-flag-green" />
                    {lang === "ar" ? "حقيقي · Google Earth Engine" : "Real · Google Earth Engine"}
                  </span>
                </div>
              </div>
              <p className="mb-2 text-[11px] text-ink-mute">
                {lang === "ar"
                  ? `توكيد مستقل عن GRACE: نموذج أرضي مدمج بالجاذبية · ${gws.months} شهراً · اتجاه ${gws.trend_mm_per_yr} مم/سنة`
                  : `Independent of GRACE: land-surface model w/ gravity DA · ${gws.months} months · trend ${gws.trend_mm_per_yr} mm/yr`}
              </p>
              <div dir="ltr" className="h-36 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={gws.series} margin={{ top: 4, right: 8, bottom: 0, left: -8 }}>
                    <defs>
                      <linearGradient id="gwsFill" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#2DD4BF" stopOpacity={0.4} />
                        <stop offset="100%" stopColor="#2DD4BF" stopOpacity={0.03} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid stroke="#272727" strokeDasharray="3 3" vertical={false} />
                    <XAxis
                      dataKey="month" tick={{ fill: "#5E5E5E", fontSize: 9 }} axisLine={false} tickLine={false}
                      ticks={gws.series.filter((p) => p.month.endsWith("-01") && Number(p.month.slice(0, 4)) % 4 === 3).map((p) => p.month)}
                      tickFormatter={(m: string) => m.slice(0, 4)}
                    />
                    <YAxis tick={{ fill: "#5E5E5E", fontSize: 9 }} axisLine={false} tickLine={false} domain={["auto", "auto"]} />
                    <Tooltip
                      contentStyle={{ background: "#161616", border: "1px solid #272727", borderRadius: 12, fontSize: 12 }}
                      labelStyle={{ color: "#B9B9B9" }}
                      formatter={(v: number) => [`${v} mm`, "GWS"]}
                    />
                    <Area type="monotone" dataKey="gws_mm" stroke="#2DD4BF" strokeWidth={1.6} fill="url(#gwsFill)" dot={false} animationDuration={900} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
              <p className="mt-1 text-[10px] text-ink-mute" dir="ltr">{gws.source}</p>
            </section>
          )}

          <section className="panel p-4">
            <div className="mb-1 flex flex-wrap items-center justify-between gap-2">
              <h2 className="font-head text-lg font-extrabold text-flag-orange">{t("well_level_title")}</h2>
              <IllustrativeBadge small />
            </div>
            <p className="mb-2 text-[11px] text-ink-mute">{t("well_level_sub")}</p>
            {forecast ? (
              <WellLevelChart forecast={forecast} />
            ) : (
              <p className="py-16 text-center text-ink-mute">{t("loading")}</p>
            )}
          </section>
        </div>

        {/* النصف الثاني: الخريطة + آلة الزمن */}
        <div className="space-y-3">
          <div className="relative">
            <MapView
              fields={fields}
              basins={basins}
              exclusions={exclusions}
              yearFilter={year}
              bounds={[[36.3, 31.45], [37.45, 32.35]]}
              onFieldClick={(id) => router.push(`/queue?focus=${id}`)}
              className="h-[430px]"
              basemap="satellite"
              satelliteDate={satDate}
            />
            <div className="absolute start-3 top-3 z-10">
              <DemoBadge />
            </div>
            <span className={`absolute end-3 top-3 z-10 inline-flex items-center gap-1 rounded-pill border px-2.5 py-1 text-[10px] font-bold backdrop-blur ${
              year >= 2026 ? "border-flag-red/50 bg-space-950/80 text-flag-red" : "border-cyanline/40 bg-space-950/80 text-cyanline"
            }`}>
              {year >= 2026
                ? <>🔴 {t("live_sat_on")} · <span dir="ltr" className="num">{liveDate}</span></>
                : <>🛰 VIIRS <span dir="ltr" className="num">{year}-08</span></>}
            </span>
          </div>
          <p className="px-1 text-[10px] text-ink-mute">🛰 {t("basemap_follows_year")}</p>
          {tm && <TimeMachine data={tm} year={year} onYearChange={setYear} />}
          <p className="px-1 text-[11px] leading-relaxed text-ink-mute">{t("time_machine_note")}</p>
        </div>
      </div>

      {/* الميزان المائي الحقيقي (NASA POWER) + برهان المطر */}
      {climate && (
        <div className="grid gap-3 lg:grid-cols-[1fr_340px]">
          <WaterBalanceChart climate={climate} />
          <RainProof climate={climate} />
        </div>
      )}

      {/* دفتر الميزان */}
      {ledger && <LedgerScales ledger={ledger} />}
    </div>
  );
}
