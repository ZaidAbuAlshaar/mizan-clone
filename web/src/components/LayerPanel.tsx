"use client";
/** لوحة الطبقات + مبدّل الخلفية (قمر صناعي NASA / داكنة) — إلهام التصميم mockup 2 */
import type { Basemap } from "./MapView";
import { useLang } from "@/lib/i18n";

interface LayerState {
  fields: boolean;
  basins: boolean;
  validation: boolean;
  heatmap: boolean;
}

export default function LayerPanel({
  basemap, onBasemap, layers, onToggle, live, onLive,
}: {
  basemap: Basemap;
  onBasemap: (b: Basemap) => void;
  layers: LayerState;
  onToggle: (k: keyof LayerState) => void;
  /** بث القمر الحي (VIIRS آخر 48 ساعة) */
  live?: boolean;
  onLive?: (v: boolean) => void;
}) {
  const { t } = useLang();
  const rows: { key: keyof LayerState; label: string; dot: string }[] = [
    { key: "fields", label: t("layer_suspect"), dot: "bg-flag-red" },
    { key: "heatmap", label: t("layer_heatmap"), dot: "bg-gold" },
    { key: "basins", label: t("layer_basins_risk"), dot: "bg-flag-orange" },
    { key: "validation", label: t("layer_validation"), dot: "bg-teal-glow" },
  ];
  return (
    <div className="panel space-y-3 p-3">
      {/* مبدّل الخلفية */}
      <div className="flex gap-1 rounded-xl border border-space-700 bg-space-950/60 p-1">
        {(["satellite", "dark"] as Basemap[]).map((b) => (
          <button
            key={b}
            onClick={() => onBasemap(b)}
            className={`flex-1 rounded-lg px-2 py-1.5 text-[11px] font-bold transition-colors ${
              basemap === b ? "bg-gold/15 text-gold shadow-glow-gold" : "text-ink-dim hover:text-ink"
            }`}
          >
            {b === "satellite" ? `🛰 ${t("basemap_satellite")}` : `◑ ${t("basemap_dark")}`}
          </button>
        ))}
      </div>
      {/* بث القمر الحي — صور VIIRS من آخر 48 ساعة عبر NASA GIBS */}
      {onLive && basemap === "satellite" && (
        <button
          onClick={() => onLive(!live)}
          className={`flex w-full items-center justify-between rounded-xl border px-3 py-1.5 text-[11px] font-bold transition-colors ${
            live
              ? "border-flag-red/60 bg-flag-red/15 text-flag-red"
              : "border-space-700 bg-space-950/60 text-ink-dim hover:text-ink"
          }`}
        >
          <span className="flex items-center gap-1.5">
            <span className={`h-2 w-2 rounded-full ${live ? "animate-pulse-dot bg-flag-red" : "bg-ink-mute"}`} />
            {t("live_sat")}
          </span>
          {live && <span className="text-[9px]">● {t("live_sat_on")}</span>}
        </button>
      )}
      {/* الطبقات */}
      <div>
        <div className="mb-1.5 text-[11px] font-bold uppercase tracking-wide text-ink-mute">{t("layers")}</div>
        <div className="space-y-1">
          {rows.map((r) => (
            <label key={r.key} className="flex cursor-pointer items-center justify-between rounded-lg px-2 py-1.5 text-xs transition-colors hover:bg-space-800">
              <span className="flex items-center gap-2 text-ink-dim">
                <span className={`h-2 w-2 rounded-full ${r.dot}`} />
                {r.label}
              </span>
              <input
                type="checkbox"
                checked={layers[r.key]}
                onChange={() => onToggle(r.key)}
                className="h-3.5 w-3.5 accent-teal-500"
              />
            </label>
          ))}
        </div>
      </div>
    </div>
  );
}
