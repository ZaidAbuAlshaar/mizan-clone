"use client";
/** الشريط الجانبي — صفّ أيقونات رفيع (طراز Dark Mood): قائمة أعلى، تنقّل، مساعدة/إعدادات أسفل */
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useLang } from "@/lib/i18n";
import Logo from "./Logo";

type IconKey = "map" | "time" | "basin" | "queue" | "impact" | "validation" | "method";

function Icon({ k, className = "h-6 w-6" }: { k: IconKey; className?: string }) {
  const c = { fill: "none", stroke: "currentColor", strokeWidth: 1.7, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
  switch (k) {
    case "map":
      return <svg viewBox="0 0 24 24" className={className} {...c}><path d="M9 4 3 6v14l6-2 6 2 6-2V4l-6 2-6-2Z" /><path d="M9 4v14M15 6v14" /></svg>;
    case "time":
      return <svg viewBox="0 0 24 24" className={className} {...c}><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg>;
    case "basin":
      return <svg viewBox="0 0 24 24" className={className} {...c}><path d="M12 21s7-6.5 7-11a7 7 0 1 0-14 0c0 4.5 7 11 7 11Z" /><circle cx="12" cy="10" r="2.5" /></svg>;
    case "queue":
      return <svg viewBox="0 0 24 24" className={className} {...c}><path d="M8 6h12M8 12h12M8 18h12" /><circle cx="4" cy="6" r="1.2" fill="currentColor" stroke="none" /><circle cx="4" cy="12" r="1.2" fill="currentColor" stroke="none" /><circle cx="4" cy="18" r="1.2" fill="currentColor" stroke="none" /></svg>;
    case "impact":
      return <svg viewBox="0 0 24 24" className={className} {...c}><path d="M4 19V5M4 19h16M8 16v-4M12 16V8M16 16v-7M20 16v-3" /></svg>;
    case "validation":
      return <svg viewBox="0 0 24 24" className={className} {...c}><path d="M12 3 4 6v6c0 5 3.5 7.5 8 9 4.5-1.5 8-4 8-9V6l-8-3Z" /><path d="m9 12 2 2 4-4" /></svg>;
    case "method":
      return <svg viewBox="0 0 24 24" className={className} {...c}><path d="M4 5.5A1.5 1.5 0 0 1 5.5 4H18v16H5.5A1.5 1.5 0 0 1 4 18.5v-13Z" /><path d="M8 4v16M11 8h4M11 12h4" /></svg>;
  }
}

const NAV: { href: string; k: IconKey; key: "nav_map" | "nav_timemachine" | "nav_basin" | "nav_queue" | "nav_impact" | "nav_validation" | "nav_methodology" }[] = [
  { href: "/", k: "map", key: "nav_map" },
  { href: "/timemachine", k: "time", key: "nav_timemachine" },
  { href: "/basin/azraq", k: "basin", key: "nav_basin" },
  { href: "/queue", k: "queue", key: "nav_queue" },
  { href: "/impact", k: "impact", key: "nav_impact" },
  { href: "/validation", k: "validation", key: "nav_validation" },
  { href: "/methodology", k: "method", key: "nav_methodology" },
];

export default function Sidebar() {
  const { t } = useLang();
  const pathname = usePathname();

  return (
    <aside className="sticky top-3 z-40 flex h-[calc(100vh-24px)] w-[78px] shrink-0 flex-col items-center rounded-rail border border-space-600/40 bg-space-800 py-5 shadow-panel">
      {/* الشعار / القائمة */}
      <Link href="/" className="grid h-11 w-11 place-items-center" aria-label="MIZAN home">
        <Logo size={34} />
      </Link>
      <div className="rail-divider my-4 w-full" />

      {/* التنقّل */}
      <nav className="flex flex-1 flex-col items-center gap-2">
        {NAV.map((n) => {
          const active = n.href === "/" ? pathname === "/" : pathname.startsWith(n.href.split("/").slice(0, 2).join("/"));
          return (
            <Link
              key={n.href}
              href={n.href}
              title={t(n.key)}
              className={`group relative grid h-11 w-11 place-items-center rounded-2xl transition-colors ${
                active ? "text-teal-glow" : "text-ink-mute hover:text-ink"
              }`}
            >
              {active && <span className="absolute inset-0 rounded-2xl bg-teal-glow/12 ring-1 ring-teal-glow/30" />}
              <span className="relative"><Icon k={n.k} /></span>
              {/* تلميح جانبي */}
              <span className="pointer-events-none absolute start-[120%] z-50 whitespace-nowrap rounded-lg border border-space-600 bg-space-950 px-2 py-1 text-[11px] text-ink opacity-0 shadow-panel transition-opacity group-hover:opacity-100">
                {t(n.key)}
              </span>
            </Link>
          );
        })}
      </nav>

      <div className="rail-divider my-4 w-full" />
      {/* مساعدة */}
      <Link href="/methodology" title={t("nav_methodology")} className="grid h-10 w-10 place-items-center rounded-2xl text-ink-mute transition-colors hover:text-ink">
        <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round"><circle cx="12" cy="12" r="9" /><path d="M9.5 9a2.5 2.5 0 1 1 3.5 2.3c-.7.4-1 .9-1 1.7" /><circle cx="12" cy="16.5" r="0.6" fill="currentColor" /></svg>
      </Link>
    </aside>
  );
}
