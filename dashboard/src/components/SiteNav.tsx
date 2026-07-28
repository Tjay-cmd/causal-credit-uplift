"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Overview" },
  { href: "/phase-1", label: "Phase 1" },
  { href: "/phase-2", label: "Phase 2" },
  { href: "/methodology", label: "Methodology" },
];

export function SiteNav() {
  const pathname = usePathname();

  return (
    <header className="border-b border-edge bg-base/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-5 py-4">
        <Link href="/" className="group flex items-baseline gap-2">
          <span className="font-display text-lg tracking-tight text-ink group-hover:text-amber">
            Causal Credit Uplift
          </span>
          <span className="hidden font-mono text-[10px] uppercase tracking-widest text-muted sm:inline">
            portfolio
          </span>
        </Link>
        <nav className="flex flex-wrap gap-1">
          {LINKS.map((link) => {
            const active =
              link.href === "/"
                ? pathname === "/"
                : pathname.startsWith(link.href);
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`rounded-md px-3 py-1.5 font-mono text-xs uppercase tracking-wide transition ${
                  active
                    ? "bg-amber/15 text-amber"
                    : "text-muted hover:bg-surface-2 hover:text-ink"
                }`}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
