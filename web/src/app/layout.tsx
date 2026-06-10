import type { Metadata } from "next";
import { Almarai, Tajawal, Inter } from "next/font/google";
import "./globals.css";
import { LangProvider } from "@/lib/i18n";
import Sidebar from "@/components/Sidebar";
import TopBar from "@/components/TopBar";

const almarai = Almarai({ weight: ["400", "700", "800"], subsets: ["arabic"], variable: "--font-almarai", display: "swap" });
const tajawal = Tajawal({ weight: ["400", "500", "700"], subsets: ["arabic", "latin"], variable: "--font-tajawal", display: "swap" });
const inter = Inter({ weight: ["400", "500", "600", "700", "800"], subsets: ["latin"], variable: "--font-inter", display: "swap" });

export const metadata: Metadata = {
  title: "ميزان MIZAN — نوزِن مياه الأردن المسروقة من الفضاء",
  description:
    "نظام فضائي–ذكي يكشف سرقة المياه الجوفية ويتنبّأ باستنزاف الخزانات في الأردن — GRACE-FO + Sentinel-2 + AI. AstroCode 2026 · Vcoders",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ar" dir="rtl" suppressHydrationWarning>
      <body className={`${almarai.variable} ${tajawal.variable} ${inter.variable} min-h-screen`}>
        <LangProvider>
          <div className="mx-auto flex max-w-[1700px] gap-3 p-3">
            <Sidebar />
            <div className="min-w-0 flex-1">
              <TopBar />
              <main>{children}</main>
            </div>
          </div>
        </LangProvider>
      </body>
    </html>
  );
}
