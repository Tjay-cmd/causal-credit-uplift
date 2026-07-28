"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useId, useRef, useState } from "react";

const LINKS = [
  { href: "/", label: "Overview" },
  { href: "/phase-1", label: "Phase 1" },
  { href: "/phase-2", label: "Phase 2" },
  { href: "/methodology", label: "Methodology" },
];

export function SiteNav() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const menuId = useId();
  const panelRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    setOpen(false);
  }, [pathname]);

  useEffect(() => {
    if (!open) return;

    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    const onPointer = (e: MouseEvent | TouchEvent) => {
      const target = e.target as Node;
      if (
        panelRef.current?.contains(target) ||
        buttonRef.current?.contains(target)
      ) {
        return;
      }
      setOpen(false);
    };

    document.addEventListener("keydown", onKey);
    document.addEventListener("mousedown", onPointer);
    document.addEventListener("touchstart", onPointer);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.removeEventListener("mousedown", onPointer);
      document.removeEventListener("touchstart", onPointer);
    };
  }, [open]);

  return (
    <header className="sticky top-0 z-40 border-b border-edge bg-base/90 backdrop-blur-md pt-[env(safe-area-inset-top)]">
      <div className="relative mx-auto flex max-w-6xl items-center justify-between gap-2 px-4 py-3 sm:px-5 md:py-4">
        {/* Same width as the hamburger so the title stays centered on mobile */}
        <span className="invisible h-10 w-10 shrink-0 md:hidden" aria-hidden />

        <Link
          href="/"
          className="group min-w-0 flex-1 text-center md:flex-none md:text-left"
          onClick={() => setOpen(false)}
        >
          <span className="font-display text-base tracking-tight text-ink group-hover:text-amber sm:text-lg">
            Causal Credit Uplift
          </span>
        </Link>

        {/* Desktop links */}
        <nav className="hidden md:block" aria-label="Primary">
          <ul className="flex flex-wrap justify-end gap-1">
            {LINKS.map((link) => {
              const active =
                link.href === "/"
                  ? pathname === "/"
                  : pathname.startsWith(link.href);
              return (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className={`inline-flex min-h-10 items-center rounded-md px-3 py-2 font-mono text-xs uppercase tracking-wide transition ${
                      active
                        ? "bg-amber/15 text-amber"
                        : "text-muted hover:bg-surface-2 hover:text-ink"
                    }`}
                  >
                    {link.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Mobile hamburger */}
        <button
          ref={buttonRef}
          type="button"
          className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-md text-ink transition hover:bg-surface-2 md:hidden"
          aria-expanded={open}
          aria-controls={menuId}
          aria-label={open ? "Close menu" : "Open menu"}
          onClick={() => setOpen((v) => !v)}
        >
          <span className="sr-only">{open ? "Close menu" : "Open menu"}</span>
          <span className="flex w-5 flex-col gap-[5px]" aria-hidden>
            <span
              className={`h-0.5 w-full rounded-full bg-current transition ${
                open ? "translate-y-[7px] rotate-45" : ""
              }`}
            />
            <span
              className={`h-0.5 w-full rounded-full bg-current transition ${
                open ? "opacity-0" : ""
              }`}
            />
            <span
              className={`h-0.5 w-full rounded-full bg-current transition ${
                open ? "-translate-y-[7px] -rotate-45" : ""
              }`}
            />
          </span>
        </button>
      </div>

      {open ? (
        <div
          id={menuId}
          ref={panelRef}
          className="border-t border-edge bg-base/95 px-4 pb-4 pt-2 md:hidden"
        >
          <nav aria-label="Mobile">
            <ul className="flex flex-col gap-1">
              {LINKS.map((link) => {
                const active =
                  link.href === "/"
                    ? pathname === "/"
                    : pathname.startsWith(link.href);
                return (
                  <li key={link.href}>
                    <Link
                      href={link.href}
                      className={`flex min-h-11 items-center rounded-md px-3 font-mono text-xs uppercase tracking-wide transition ${
                        active
                          ? "bg-amber/15 text-amber"
                          : "text-muted hover:bg-surface-2 hover:text-ink"
                      }`}
                      onClick={() => setOpen(false)}
                    >
                      {link.label}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </nav>
        </div>
      ) : null}
    </header>
  );
}
