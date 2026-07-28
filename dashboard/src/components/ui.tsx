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
    <section className={`min-w-0 space-y-4 ${className}`}>
      <div>
        {eyebrow ? (
          <p className="mb-1 font-mono text-[11px] uppercase tracking-[0.18em] text-amber">
            {eyebrow}
          </p>
        ) : null}
        <h2 className="font-display text-xl tracking-tight text-ink sm:text-2xl md:text-3xl">
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
      className={`rounded-lg border p-4 sm:p-5 ${
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
      <div className="min-w-0 space-y-2 text-sm leading-relaxed text-ink/90">
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
    <div className="min-w-0 rounded-lg border border-edge bg-surface px-3 py-3 sm:px-4">
      <p className="font-mono text-[10px] uppercase tracking-widest text-muted">
        {label}
      </p>
      <p className="mt-1 break-words font-mono text-lg text-ink sm:text-xl">
        {value}
      </p>
      {hint ? (
        <p className="mt-1 text-xs leading-snug text-muted">{hint}</p>
      ) : null}
    </div>
  );
}
