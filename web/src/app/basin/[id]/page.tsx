"use client";
/** الشاشة 2 — تفاصيل الحوض: منحنى GRACE الإقليمي + العتبة الحرجة على مناسيب الآبار + آلة الزمن + دفتر الميزان */
import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import MapView from "@/components/MapView";
import GraceChart from "@/components/GraceChart";
import WellLevelChart from "@/components/WellLevelChart";
import WaterBalanceChart from "@/components/WaterBalanceChart";
import RainProof from "@/components/RainProof";
import TimeMachine from "@/components/TimeMachine";
import LedgerScales from "@/components/LedgerScales";
import { DemoBadge, IllustrativeBadge, RegionalBadge } from "@/components/Badges";
import {
  getBasins, getClimate, getExclusions, getFields, getForecast, getLedger, getTimeMachine, getTws,
} from "@/lib/api";
import type {
  BasinsFC, ClimateData, FieldsFC, Forecast, LedgerData, TimeMachineData, TwsSeries,
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
  const [year, setYear] = useState(2026);

  useEffect(() => {
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
                <IllustrativeBadge small />
              </div>
            </div>
            <p className="mb-2 text-[11px] text-ink-mute">{t("grace_subtitle")}</p>
            {tws && forecast ? (
              <GraceChart tws={tws} forecast={forecast} />
            ) : (
              <p className="py-16 text-center text-ink-mute">{t("loading")}</p>
            )}
          </section>

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
            />
            <div className="absolute start-3 top-3 z-10">
              <DemoBadge />
            </div>
          </div>
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
