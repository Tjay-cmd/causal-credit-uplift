import { ReactNode } from "react";

export function Section({
  eyebrow,
  title,
  children,
  className = "",
}: {
  eyebrow?: string;
  title: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`space-y-4 ${className}`}>
      <div>
        {eyebrow ? (
          <p className="mb-1 font-mono text-[11px] uppercase tracking-[0.18em] text-amber">
            {eyebrow}
          </p>
        ) : null}
        <h2 className="font-display text-2xl tracking-tight text-ink md:text-3xl">
          {title}
        </h2>
      </div>
      {children}
    </section>
  );
}

export function Callout({
  tone = "amber",
  title,
  children,
}: {
  tone?: "amber" | "muted";
  title: string;
  children: ReactNode;
}) {
  return (
    <aside
      className={`rounded-lg border p-5 ${
        tone === "amber"
          ? "border-amber/40 bg-amber/5"
          : "border-edge bg-surface"
      }`}
    >
      <p
        className={`mb-2 font-mono text-[11px] uppercase tracking-[0.16em] ${
          tone === "amber" ? "text-amber" : "text-muted"
        }`}
      >
        {title}
      </p>
      <div className="space-y-2 text-sm leading-relaxed text-ink/90">
        {children}
      </div>
    </aside>
  );
}

export function EmptyState({ label }: { label: string }) {
  return (
    <div className="rounded-lg border border-dashed border-edge bg-surface px-4 py-8 text-center font-mono text-sm text-muted">
      {label}
    </div>
  );
}

export function Stat({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint?: string;
}) {
  return (
    <div className="rounded-lg border border-edge bg-surface px-4 py-3">
      <p className="font-mono text-[10px] uppercase tracking-widest text-muted">
        {label}
      </p>
      <p className="mt-1 font-mono text-xl text-ink">{value}</p>
      {hint ? <p className="mt-1 text-xs text-muted">{hint}</p> : null}
    </div>
  );
}
