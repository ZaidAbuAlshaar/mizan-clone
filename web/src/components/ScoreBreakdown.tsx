"use client";
/** تفصيل مكوّنات درجة P4 — أوزان شفافة (الصيغة المعتمدة 35/25/15/12.5/12.5) */
import type { ScoreBreakdown as SB } from "@/lib/types";
import { useLang } from "@/lib/i18n";

const MAX: Record<keyof SB, number> = {
  inside_protected_basin: 35,
  new_after_closure: 25,
  persistence: 15,
  area: 12.5,
  expansion: 12.5,
};

export default function ScoreBreakdown({ breakdown, score, mlAnomaly }: { breakdown: SB; score: number; mlAnomaly?: number }) {
  const { t } = useLang();
  const rows: { key: keyof SB; label: string }[] = [
    { key: "inside_protected_basin", label: t("sc_inside") },
    { key: "new_after_closure", label: t("sc_new") },
    { key: "persistence", label: t("sc_persistence") },
    { key: "area", label: t("sc_area") },
    { key: "expansion", label: t("sc_expansion") },
  ];
  const color = score >= 70 ? "#F43F5E" : score >= 40 ? "#F59E0B" : "#10B981";

  return (
    <div className="space-y-2">
      {rows.map((r) => {
        const v = breakdown[r.key];
        const max = MAX[r.key];
        return (
          <div key={r.key} className="flex items-center gap-2 text-xs">
            <span className="w-32 shrink-0 text-ink-dim">{r.label}</span>
            <div className="h-2 flex-1 overflow-hidden rounded-full bg-space-700">
              <div
                className="h-full rounded-full"
                style={{ width: `${(v / max) * 100}%`, background: color, opacity: 0.85 }}
              />
            </div>
            <span className="num w-14 shrink-0 text-end text-ink-dim">
              {v}<span className="text-ink-mute">/{max}</span>
            </span>
          </div>
        );
      })}
      <div className="flex items-center justify-between border-t border-space-700 pt-2">
        <span className="text-xs font-bold text-ink-dim">{t("col_score")}</span>
        <span className="kpi-number text-2xl" style={{ color }}>
          {score}<span className="text-sm text-ink-mute">/100</span>
        </span>
      </div>
      {/* مؤشر الشذوذ AI — مساند حصراً، لا يدخل في الدرجة (plan.md §371: anomaly scoring) */}
      {mlAnomaly != null && (
        <div className="flex items-center gap-2 rounded-lg border border-cyanline/25 bg-cyanline/5 px-2 py-1.5 text-xs">
          <span className="shrink-0 text-ink-dim">🤖 {t("sc_ml_anomaly")}</span>
          <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-space-700">
            <div className="h-full rounded-full bg-cyanline" style={{ width: `${mlAnomaly * 100}%`, opacity: 0.8 }} />
          </div>
          <span className="num shrink-0 text-cyanline">{mlAnomaly.toFixed(2)}</span>
          <span className="shrink-0 text-[9px] text-ink-mute">{t("sc_ml_supporting")}</span>
        </div>
      )}
    </div>
  );
}
