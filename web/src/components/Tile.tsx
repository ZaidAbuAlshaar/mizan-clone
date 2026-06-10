"use client";
/** بلاطة مؤشر (طراز Dark Mood — أيقونة + عنوان + قيمة كبيرة + نص فرعي) */
import Link from "next/link";

export function MetricTile({
  icon, label, value, unit, sub, accent = "#FFFFFF", href, badge,
}: {
  icon: React.ReactNode;
  label: string;
  value: React.ReactNode;
  unit?: string;
  sub?: string;
  accent?: string;
  href?: string;
  badge?: React.ReactNode;
}) {
  const inner = (
    <div className="tile flex h-full flex-col gap-2 transition-transform hover:-translate-y-0.5">
      <div className="flex items-center justify-between">
        <span className="flex items-center gap-2 text-sm text-ink-dim">
          <span className="text-ink-mute">{icon}</span>
          {label}
        </span>
        {badge}
      </div>
      <div className="mt-auto">
        <span className="kpi-number text-3xl" style={{ color: accent }}>{value}</span>
        {unit && <span className="ms-1 text-xs text-ink-mute">{unit}</span>}
      </div>
      {sub && <div className="text-[11px] leading-tight text-ink-mute">{sub}</div>}
    </div>
  );
  return href ? <Link href={href} className="block h-full">{inner}</Link> : inner;
}

export function TileIcon({ d, circle }: { d?: string; circle?: boolean }) {
  return (
    <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      {circle && <circle cx="12" cy="12" r="9" />}
      {d && <path d={d} />}
    </svg>
  );
}
