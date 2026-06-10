"use client";
/** الترويسة — ترحيب (يسار) + بحث + مبدّل سمة/لغة + أفاتار (طراز Dark Mood المرجعي) */
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useLang } from "@/lib/i18n";
import { getMeta } from "@/lib/api";

export default function TopBar() {
  const { lang, setLang, t } = useLang();
  const router = useRouter();
  const [demoMode, setDemoMode] = useState(false);
  const [q, setQ] = useState("");
  const [now, setNow] = useState<string>("");
  const tickRef = useRef(false);

  useEffect(() => {
    getMeta().then((m) => setDemoMode(m.data_mode !== "production")).catch(() => setDemoMode(true));
  }, []);

  useEffect(() => {
    // تاريخ ثابت العرض (لا ساعة حيّة لتجنّب hydration)
    const d = new Intl.DateTimeFormat(lang === "ar" ? "ar-JO" : "en-GB", { weekday: "long", day: "2-digit", month: "short", year: "numeric" });
    setNow(d.format(new Date(2026, 5, 10)));
    tickRef.current = true;
  }, [lang]);

  const greeting = lang === "ar" ? "أهلاً، المفتّش 👋" : "Hi, Inspector 👋";
  const sub = lang === "ar" ? "غرفة عمليات ميزان" : "MIZAN Operations Room";

  return (
    <header className="mb-3 flex flex-wrap items-center gap-3">
      {/* الترحيب */}
      <div className="me-auto leading-tight">
        <div className="font-ui text-sm text-ink-dim">{greeting}</div>
        <div className="font-head text-2xl font-extrabold text-ink">{sub}</div>
      </div>

      {/* البحث (حبّة) */}
      <form
        onSubmit={(e) => { e.preventDefault(); if (q.trim()) router.push(`/queue?focus=${encodeURIComponent(q.trim().toUpperCase())}`); }}
        className="hidden items-center gap-2 rounded-pill border border-space-600/50 bg-space-800 px-5 py-3 md:flex"
      >
        <svg viewBox="0 0 24 24" className="h-5 w-5 text-ink-mute" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><circle cx="11" cy="11" r="7" /><path d="m20 20-3-3" /></svg>
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder={lang === "ar" ? "ابحث عن حقل (AZQ-0001)…" : "Search a field (AZQ-0001)…"}
          className="w-44 bg-transparent text-sm text-ink placeholder:text-ink-mute focus:outline-none"
        />
      </form>

      {/* التاريخ (حبّة) */}
      <div className="hidden items-center gap-2 rounded-pill border border-space-600/50 bg-space-800 px-4 py-3 text-xs text-ink-dim lg:flex">
        <svg viewBox="0 0 24 24" className="h-4 w-4 text-ink-mute" fill="none" stroke="currentColor" strokeWidth="1.8"><rect x="3" y="4.5" width="18" height="16" rx="3" /><path d="M3 9h18M8 3v3M16 3v3" /></svg>
        <span className="num" dir="ltr">{now}</span>
      </div>

      {/* مبدّل اللغة (حبّة) */}
      <button
        onClick={() => setLang(lang === "ar" ? "en" : "ar")}
        aria-label="Switch language"
        className="rounded-pill border border-space-600/50 bg-space-800 px-4 py-3 text-sm font-bold text-ink-dim transition-colors hover:border-teal-glow/40 hover:text-teal-glow"
      >
        {lang === "ar" ? "EN" : "عربي"}
      </button>

      {/* شارة الوضع + الأفاتار */}
      <div className="flex items-center gap-2 rounded-pill border border-space-600/50 bg-space-800 py-1.5 ps-1.5 pe-3">
        <span className="grid h-9 w-9 place-items-center rounded-full bg-gradient-to-br from-teal-glow/30 to-cyanline/20 text-sm font-extrabold text-teal-glow">و</span>
        <div className="hidden leading-tight sm:block">
          <div className="text-xs font-bold text-ink">Vcoders</div>
          <div className="text-[10px] text-ink-mute">AstroCode 2026</div>
        </div>
      </div>
    </header>
  );
}
