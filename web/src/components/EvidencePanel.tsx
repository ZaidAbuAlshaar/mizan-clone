"use client";
/**
 * بانل الدليل (explainability) — قلب لقطة الديمو 5:
 * بصمة الريّ NDVI×CHIRPS + قبل/بعد + مكوّنات الدرجة + توكيد SMAP + تحديث الحالة (human-in-the-loop)
 */
import { useState } from "react";
import type { FieldProps, FieldStatus } from "@/lib/types";
import { canTransition, patchFieldStatus } from "@/lib/api";
import { useLang } from "@/lib/i18n";
import { fmt, fmtGps, TIER_EMOJI } from "@/lib/format";
import NdviChart from "./NdviChart";
import BeforeAfter from "./BeforeAfter";
import ScoreBreakdown from "./ScoreBreakdown";
import { DemoBadge, StatusPill } from "./Badges";

const MONTH_LABELS = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"];

function SmapMini({ values }: { values: number[] }) {
  const max = Math.max(...values, 0.4);
  return (
    <div dir="ltr" className="flex h-14 items-end gap-1">
      {values.map((v, i) => (
        <div key={i} className="flex-1">
          <div
            className="w-full rounded-sm bg-cyanline/70"
            style={{ height: `${(v / max) * 48}px` }}
            title={`${MONTH_LABELS[i]}: ${v}`}
          />
        </div>
      ))}
    </div>
  );
}

export default function EvidencePanel({
  field,
  onClose,
  onStatusChange,
}: {
  field: FieldProps;
  onClose: () => void;
  onStatusChange: (id: string, status: FieldStatus) => void;
}) {
  const { t, lang } = useLang();
  const [status, setStatus] = useState<FieldStatus>(field.status);
  const [savedMsg, setSavedMsg] = useState<string | null>(null);

  async function update(next: FieldStatus) {
    const res = await patchFieldStatus(field.id, status, next);
    if (res.ok) {
      setStatus(next);
      onStatusChange(field.id, next);
      setSavedMsg(res.source === "api" ? t("status_saved_api") : t("status_saved_local"));
      setTimeout(() => setSavedMsg(null), 2500);
    }
  }

  const actions: { to: FieldStatus; label: string; cls: string }[] = [
    { to: "inspected", label: t("mark_inspected"), cls: "border-flag-orange/50 text-flag-orange hover:bg-flag-orange/10" },
    { to: "confirmed", label: t("mark_confirmed"), cls: "border-flag-red/50 text-flag-red hover:bg-flag-red/10" },
    { to: "cleared", label: t("mark_cleared"), cls: "border-flag-green/50 text-flag-green hover:bg-flag-green/10" },
  ];

  return (
    <aside className="panel-raised fixed inset-y-0 end-0 z-50 flex w-full max-w-md flex-col gap-4 overflow-y-auto p-5 sm:rounded-s-2xl sm:rounded-e-none">
      <div className="flex items-start justify-between gap-2">
        <div>
          <h2 className="font-head text-xl font-extrabold">
            {TIER_EMOJI[field.tier]} {t("evidence_title")} — <span dir="ltr">{field.id}</span>
          </h2>
          <p className="num mt-1 text-xs text-ink-dim" dir="ltr">
            {fmtGps(field.centroid)}
          </p>
        </div>
        <button
          onClick={onClose}
          className="rounded-lg border border-space-700 px-2.5 py-1 text-ink-dim hover:text-ink"
          aria-label="close"
        >
          ✕
        </button>
      </div>

      <div className="grid grid-cols-3 gap-2 text-center">
        <div className="panel p-2">
          <div className="kpi-number text-lg">{field.area_ha}</div>
          <div className="text-[10px] text-ink-mute">{t("col_area")}</div>
        </div>
        <div className="panel p-2">
          <div className="kpi-number text-lg">{field.first_seen_year}</div>
          <div className="text-[10px] text-ink-mute">{t("col_first_seen")}</div>
        </div>
        <div className="panel p-2">
          <div className="kpi-number text-lg" dir="ltr">
            {fmt(field.est_m3_low / 1000)}–{fmt(field.est_m3_high / 1000)}K
          </div>
          <div className="text-[10px] text-ink-mute">{t("col_volume")}</div>
        </div>
      </div>

      <section>
        <h3 className="mb-1 text-sm font-bold text-teal-glow">{t("ndvi_vs_rain")}</h3>
        <p className="mb-2 text-[11px] leading-relaxed text-ink-mute">{t("ndvi_note")}</p>
        <NdviChart series={field.ndvi_series} height={190} />
        <div className="mt-1 flex items-center justify-between text-[11px] text-ink-dim">
          <span>
            {t("anti_phase")}: <b className="num text-teal-glow">{Math.round(field.anti_phase_score * 100)}%</b>
          </span>
          <span>
            {t("persistence_months")}: <b className="num text-teal-glow">{field.persistence_months}</b>
          </span>
        </div>
      </section>

      <section>
        <h3 className="mb-2 text-sm font-bold text-teal-glow">{t("before_after")}</h3>
        <BeforeAfter field={field} />
      </section>

      <section className="panel p-3">
        <h3 className="mb-2 text-sm font-bold text-teal-glow">{t("score_components")}</h3>
        <ScoreBreakdown breakdown={field.score_breakdown} score={field.score} mlAnomaly={field.ml_anomaly} />
      </section>

      <section>
        <h3 className="mb-1 text-sm font-bold text-teal-glow">{t("smap_confirm")}</h3>
        <p className="mb-2 text-[11px] leading-relaxed text-ink-mute">{t("smap_note")}</p>
        <SmapMini values={field.sm_rootzone} />
        <div dir="ltr" className="mt-0.5 flex justify-between text-[9px] text-ink-mute">
          <span>Jan</span><span>Jun</span><span>Dec</span>
        </div>
      </section>

      <section className="panel p-3">
        <div className="mb-2 flex items-center justify-between">
          <h3 className="text-sm font-bold text-teal-glow">{t("update_status")}</h3>
          <StatusPill status={status} />
        </div>
        <div className="flex flex-wrap gap-2">
          {actions.map((a) => (
            <button
              key={a.to}
              disabled={!canTransition(status, a.to)}
              onClick={() => update(a.to)}
              className={`rounded-lg border px-3 py-1.5 text-xs font-bold transition-colors disabled:cursor-not-allowed disabled:opacity-30 ${a.cls}`}
            >
              {a.label}
            </button>
          ))}
        </div>
        {savedMsg && <p className="mt-2 text-[11px] text-flag-green">✓ {savedMsg}</p>}
        <p className="mt-2 text-[10px] leading-relaxed text-ink-mute">
          {lang === "ar"
            ? "مرشّحات لا اتهامات — المفتّش يقرر، النظام يوجّه عينه (human-in-the-loop)."
            : "Filters, not accusations — the inspector decides; the system aims their eyes (human-in-the-loop)."}
        </p>
      </section>

      {field.is_demo && <DemoBadge small />}
    </aside>
  );
}
