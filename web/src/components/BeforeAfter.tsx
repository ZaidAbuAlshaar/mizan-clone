"use client";
/**
 * سحّاب قبل/بعد — صور أقمار حقيقية لكل حقل (Sentinel-2 10م «بعد» + Landsat 2016 «قبل»)
 * مولّدة من tools/fetch_s2_timemachine.py → /nasa/fields/{id}_before|after.jpg
 * عند غياب القصاصات: fallback على التصوّر التوضيحي الموسوم (قرار المراجعة #7 محقق)
 */
import { useEffect, useState } from "react";
import { useLang } from "@/lib/i18n";
import { getNasa } from "@/lib/api";
import type { FieldProps } from "@/lib/types";

function DesertScene({ green, pivot, seed }: { green: boolean; pivot: boolean; seed: number }) {
  // بقع رملية حتمية من الـ seed
  const dots = Array.from({ length: 40 }, (_, i) => {
    const x = ((seed * 13 + i * 37) % 100);
    const y = ((seed * 7 + i * 53) % 100);
    const r = 0.6 + ((seed + i) % 5) * 0.28;
    return { x, y, r };
  });
  return (
    <svg viewBox="0 0 200 130" preserveAspectRatio="xMidYMid slice" className="h-full w-full">
      <defs>
        <linearGradient id={`sand${seed}${green ? "g" : "b"}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#3D3526" />
          <stop offset="1" stopColor="#2C2719" />
        </linearGradient>
        <radialGradient id={`field${seed}`} cx="0.5" cy="0.5" r="0.5">
          <stop offset="0" stopColor="#1FA75B" />
          <stop offset="0.8" stopColor="#157A41" />
          <stop offset="1" stopColor="#0E5A30" />
        </radialGradient>
      </defs>
      <rect width="200" height="130" fill={`url(#sand${seed}${green ? "g" : "b"})`} />
      {dots.map((d, i) => (
        <circle key={i} cx={d.x * 2} cy={d.y * 1.3} r={d.r} fill="#4A4130" opacity="0.5" />
      ))}
      {/* مجرى وادٍ جاف */}
      <path d="M-5 95 Q60 80 110 96 T210 88" stroke="#4A4130" strokeWidth="5" fill="none" opacity="0.6" />
      {green &&
        (pivot ? (
          <>
            <circle cx="100" cy="62" r="34" fill={`url(#field${seed})`} />
            <line x1="100" y1="62" x2="134" y2="62" stroke="#0B3D20" strokeWidth="1.6" />
            <circle cx="100" cy="62" r="2.4" fill="#0B3D20" />
          </>
        ) : (
          <>
            <rect x="58" y="34" width="84" height="56" rx="3" fill={`url(#field${seed})`} transform={`rotate(${(seed % 11) - 5} 100 62)`} />
            {[0, 1, 2, 3, 4].map((i) => (
              <line
                key={i}
                x1={66 + i * 17}
                y1="38"
                x2={66 + i * 17}
                y2="86"
                stroke="#0E5A30"
                strokeWidth="1.4"
                opacity="0.7"
                transform={`rotate(${(seed % 11) - 5} 100 62)`}
              />
            ))}
          </>
        ))}
    </svg>
  );
}

export default function BeforeAfter({ field }: { field: FieldProps }) {
  const { t } = useLang();
  const [pos, setPos] = useState(50);
  const [realOk, setRealOk] = useState(true);          // تنقلب false عند فشل تحميل القصاصة
  const [years, setYears] = useState<{ before: number; after: number }>({ before: 2016, after: 2025 });
  const seed = parseInt(field.id.replace(/\D/g, ""), 10) || 1;
  const pivot = seed % 3 === 0;
  const beforeYear = Math.max(2016, field.first_seen_year - 1);
  const beforeSrc = `/nasa/fields/${field.id}_before.jpg`;
  const afterSrc = `/nasa/fields/${field.id}_after.jpg`;

  useEffect(() => {
    getNasa().then((n) => {
      if (n?.fields_thumbs) setYears({ before: n.fields_thumbs.before_year, after: n.fields_thumbs.after_year });
    }).catch(() => {});   // غياب القصاصات يحسمه onError → fallback توضيحي
  }, []);

  return (
    <div>
      <div className="relative h-44 w-full overflow-hidden rounded-xl border border-space-700" dir="ltr">
        {realOk ? (
          <>
            {/* بعد (كامل) — Sentinel-2 حقيقي */}
            <img src={afterSrc} alt={`${field.id} ${years.after}`} draggable={false}
                 className="absolute inset-0 h-full w-full object-cover"
                 onError={() => setRealOk(false)} />
            {/* قبل (مقصوص بالموضع) — Landsat 2016 حقيقي */}
            <div className="absolute inset-0 overflow-hidden" style={{ clipPath: `inset(0 ${100 - pos}% 0 0)` }}>
              <img src={beforeSrc} alt={`${field.id} ${years.before}`} draggable={false}
                   className="h-full w-full object-cover"
                   onError={() => setRealOk(false)} />
            </div>
          </>
        ) : (
          <>
            {/* fallback توضيحي موسوم */}
            <div className="absolute inset-0">
              <DesertScene green pivot={pivot} seed={seed} />
            </div>
            <div className="absolute inset-0" style={{ clipPath: `inset(0 ${100 - pos}% 0 0)` }}>
              <DesertScene green={false} pivot={pivot} seed={seed} />
            </div>
          </>
        )}
        {/* مقبض */}
        <div className="absolute bottom-0 top-0 w-0.5 bg-teal-glow shadow-glow" style={{ left: `${pos}%` }}>
          <div className="absolute top-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full border border-teal-glow bg-space-950 p-1 text-[9px] text-teal-glow">
            ⇄
          </div>
        </div>
        <span className="absolute left-2 top-2 rounded bg-space-950/80 px-1.5 py-0.5 text-[10px] text-ink-dim">
          {realOk ? years.before : beforeYear}
        </span>
        <span className="absolute right-2 top-2 rounded bg-space-950/80 px-1.5 py-0.5 text-[10px] text-teal-glow">
          {realOk ? years.after : 2026}
        </span>
        {realOk ? (
          <span className="absolute bottom-2 right-2 rounded border border-flag-green/40 bg-flag-green/10 px-1.5 py-0.5 text-[10px] font-bold text-flag-green">
            {t("real_s2_thumb")}
          </span>
        ) : (
          <span className="absolute bottom-2 right-2 rounded bg-space-950/80 px-1.5 py-0.5 text-[10px] text-flag-orange">
            {t("illustrative")} · demo
          </span>
        )}
      </div>
      <input
        type="range"
        min={2}
        max={98}
        value={pos}
        onChange={(e) => setPos(Number(e.target.value))}
        className="mizan-range mt-2"
        dir="ltr"
        aria-label={t("before_after")}
      />
    </div>
  );
}
