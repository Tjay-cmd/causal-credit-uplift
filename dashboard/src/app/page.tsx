import Link from "next/link";
import { QuadrantDiagram } from "@/components/Quadrant";
import { EmptyState, Stat } from "@/components/ui";
import { loadPhase1, loadPhase2 } from "@/lib/loadData";
import { fmtNum, fmtPct } from "@/lib/format";

export default async function HomePage() {
  const [phase1, phase2] = await Promise.all([loadPhase1(), loadPhase2()]);

  const p1Qini = phase1?.models?.[0]?.qini_coefficient;
  const p2Pehe = phase2?.cate_recovery?.overall?.find(
    (r) => r.model === "CausalForestDML",
  )?.pehe;
  const p2Contamination = phase2?.segment_recovery?.safer_sleeping_dogs_rate;

  return (
    <div className="space-y-16">
      <section className="max-w-3xl space-y-6">
        <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-amber">
          Causal inference · Uplift modeling
        </p>
        <h1 className="font-display text-4xl leading-[1.05] tracking-tight text-ink md:text-6xl">
          Causal Credit Uplift
        </h1>
        <p className="text-lg leading-relaxed text-muted md:text-xl">
          Risk scoring asks who will default. Uplift modeling asks a different
          question: whose outcome{" "}
          <span className="text-ink">changes because of an action</span> — a
          credit-limit increase, a campaign, a treatment. This portfolio project
          validates that methodology on a real RCT (Phase 1), then proves models
          can recover known ground-truth effects on a synthetic credit
          experiment (Phase 2).
        </p>
      </section>

      <section className="space-y-4">
        <h2 className="font-display text-2xl text-ink">The four-quadrant frame</h2>
        <p className="max-w-2xl text-sm text-muted">
          Classification metrics collapse these into one ranking. Uplift keeps
          them apart — especially Sleeping Dogs, where treatment can hurt.
        </p>
        <QuadrantDiagram />
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <Link
          href="/phase-1"
          className="group rounded-xl border border-edge bg-surface p-6 transition hover:border-amber/50"
        >
          <p className="font-mono text-[11px] uppercase tracking-widest text-amber">
            Phase 1
          </p>
          <h3 className="mt-2 font-display text-2xl text-ink group-hover:text-amber">
            Hillstrom RCT
          </h3>
          <p className="mt-2 text-sm leading-relaxed text-muted">
            Real randomized email data. Prove Qini / T-learner / causal forest
            methodology before touching synthetic credit.
          </p>
          {p1Qini !== undefined ? (
            <p className="mt-5 font-mono text-sm text-ink">
              Teaser: T-learner Qini{" "}
              <span className="text-amber">{fmtNum(p1Qini, 2)}</span>
            </p>
          ) : (
            <div className="mt-5">
              <EmptyState label="Phase 1 metrics not loaded" />
            </div>
          )}
        </Link>

        <Link
          href="/phase-2"
          className="group rounded-xl border border-edge bg-surface p-6 transition hover:border-amber/50"
        >
          <p className="font-mono text-[11px] uppercase tracking-widest text-amber">
            Phase 2
          </p>
          <h3 className="mt-2 font-display text-2xl text-ink group-hover:text-amber">
            Synthetic credit RCT
          </h3>
          <p className="mt-2 text-sm leading-relaxed text-muted">
            Known true CATE. Test whether uplift models recover Persuadables and
            avoid Sleeping Dogs in a top-decile list.
          </p>
          {p2Pehe !== undefined && p2Contamination !== undefined ? (
            <p className="mt-5 font-mono text-sm text-ink">
              Teaser: CF PEHE{" "}
              <span className="text-amber">{fmtNum(p2Pehe, 4)}</span>
              {" · "}top-decile Sleeping Dogs{" "}
              <span className="text-amber">{fmtPct(p2Contamination, 2)}</span>
            </p>
          ) : (
            <div className="mt-5">
              <EmptyState label="Phase 2 metrics not loaded" />
            </div>
          )}
        </Link>
      </section>

      <section className="grid gap-3 sm:grid-cols-3">
        <Stat
          label="Why not AUC"
          value="Wrong Q"
          hint="Ranks likelihood of the outcome, not incremental effect of treatment."
        />
        <Stat
          label="Accent choice"
          value="Amber"
          hint="Signal-in-the-dark: uplift finds effects risk scores alone miss."
        />
        <Stat
          label="Layers"
          value="Static JSON"
          hint="Dashboard never retrains — it only visualizes exported artifacts."
        />
      </section>
    </div>
  );
}
