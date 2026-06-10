import type { Config } from "tailwindcss";

/**
 * هوية "Dark Mood" — مستوحاة من لوحة الطقس المرجعية:
 * أسود نقي، استدارة عالية، بلاطات #272727، حبوب (pills) مستديرة، نص أبيض/رمادي.
 * ألوان الخطر (أحمر/برتقالي/أخضر) تبقى للبيانات + لمسة تركوازية/ذهبية للتفاعل.
 */
const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        // مقياس الأسود (Dark Mood) — مُعاد تعيينه ليُحدّث كل المكوّنات تلقائياً
        space: {
          950: "#0C0C0C", // black-900 الأعمق
          900: "#0F0F0F", // الخلفية الأساسية
          850: "#161616",
          800: "#1E1E1E", // البطاقات الكبرى (black-800)
          750: "#232323",
          700: "#272727", // البلاطات الداخلية (inner tiles)
          650: "#2E2E2E",
          600: "#363636", // الحدود / الحبوب (black-500)
          500: "#4A4949", // فواصل التدرّج
        },
        ink: {
          DEFAULT: "#FFFFFF",
          dim: "#B9B9B9", // black-100
          mute: "#5E5E5E", // black-400
          faint: "#3A3A3A",
        },
        teal: { glow: "#2DD4BF" },
        cyanline: "#38BDF8",
        gold: { DEFAULT: "#E9B949", soft: "#F1C75B", deep: "#C99A2E" },
        flag: { red: "#F43F5E", orange: "#F59E0B", green: "#10B981" },
      },
      fontFamily: {
        head: ["var(--font-almarai)", "var(--font-inter)", "system-ui", "sans-serif"],
        body: ["var(--font-tajawal)", "var(--font-inter)", "system-ui", "sans-serif"],
        ui: ["var(--font-inter)", "var(--font-tajawal)", "system-ui", "sans-serif"],
      },
      borderRadius: {
        tile: "16px",
        card: "24px",
        rail: "32px",
        pill: "36px",
      },
      boxShadow: {
        glow: "0 0 24px rgba(45, 212, 191, 0.18)",
        "glow-red": "0 0 20px rgba(244, 63, 94, 0.30)",
        "glow-gold": "0 0 30px rgba(233, 185, 73, 0.22)",
        panel: "0 10px 40px rgba(0, 0, 0, 0.45)",
        cinematic: "0 24px 70px rgba(0, 0, 0, 0.6)",
        tile: "inset 0 1px 0 rgba(255,255,255,0.03)",
      },
      fontSize: {
        hero: ["clamp(2.6rem, 6vw, 5.4rem)", { lineHeight: "0.98", letterSpacing: "-0.03em" }],
      },
      animation: {
        "pulse-dot": "pulseDot 1.6s ease-in-out infinite",
        "fade-up": "fadeUp 0.5s ease-out",
        "fade-in": "fadeIn 0.7s ease-out",
        scan: "scan 6s linear infinite",
      },
      keyframes: {
        pulseDot: {
          "0%, 100%": { opacity: "1", transform: "scale(1)" },
          "50%": { opacity: "0.45", transform: "scale(1.6)" },
        },
        fadeUp: { from: { opacity: "0", transform: "translateY(10px)" }, to: { opacity: "1", transform: "translateY(0)" } },
        fadeIn: { from: { opacity: "0" }, to: { opacity: "1" } },
        scan: { "0%": { transform: "translateY(-100%)" }, "100%": { transform: "translateY(100%)" } },
      },
    },
  },
  plugins: [],
};
export default config;
