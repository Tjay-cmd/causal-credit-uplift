import type { Metadata } from "next";
import { Syne, Source_Sans_3, IBM_Plex_Mono } from "next/font/google";
import { SiteNav } from "@/components/SiteNav";
import "./globals.css";

const display = Syne({
  subsets: ["latin"],
  variable: "--font-display",
  weight: ["500", "600", "700", "800"],
});

const body = Source_Sans_3({
  subsets: ["latin"],
  variable: "--font-body",
  weight: ["400", "500", "600"],
});

const mono = IBM_Plex_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  weight: ["400", "500"],
});

export const metadata: Metadata = {
  title: "Causal Credit Uplift",
  description:
    "Portfolio dashboard: Phase 1 Hillstrom uplift methodology + Phase 2 synthetic credit CATE recovery.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${display.variable} ${body.variable} ${mono.variable} font-body antialiased`}
      >
        <SiteNav />
        <main className="mx-auto max-w-6xl px-5 py-10 md:py-14">{children}</main>
        <footer className="mx-auto max-w-6xl border-t border-edge px-5 py-8">
          <p className="font-mono text-[11px] uppercase tracking-widest text-muted">
            Presentation layer only — numbers from exported Phase 1 / Phase 2 artifacts.
          </p>
        </footer>
      </body>
    </html>
  );
}
