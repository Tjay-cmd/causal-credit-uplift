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
    <div className="space-y-10 md:space-y-16">
      <section className="max-w-3xl space-y-5 md:space-y-6">
        <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-amber">
          Causal inference · Uplift modeling
        </p>
        <h1 className="font-display text-3xl leading-[1.05] tracking-tight text-ink sm:text-4xl md:text-6xl">
          Causal Credit Uplift
        </h1>
        <p className="text-base leading-relaxed text-muted sm:text-lg md:text-xl">
          Risk scoring asks who will default. Uplift asks something else: whose
          outcome{" "}
          <span className="text-ink">actually changes because you did something</span>
          , like raising a credit limit. Phase 1 checks the methods on a real
          email RCT. Phase 2 checks whether the same models can recover known
          true effects on synthetic credit data.
        </p>
      </section>

      <section className="space-y-4">
        <h2 className="font-display text-xl text-ink sm:text-2xl">The four-quadrant frame</h2>
        <p className="max-w-2xl text-sm text-muted">
          Normal classification metrics mash these groups into one ranking.
          Uplift tries to keep them separate, especially Sleeping Dogs, where
          treatment can make things worse.
        </p>
        <QuadrantDiagram />
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <Link
          href="/phase-1"
          className="group rounded-xl border border-edge bg-surface p-5 transition hover:border-amber/50 sm:p-6"
        >
          <p className="font-mono text-[11px] uppercase tracking-widest text-amber">
            Phase 1
          </p>
          <h3 className="mt-2 font-display text-xl text-ink group-hover:text-amber sm:text-2xl">
            Hillstrom RCT
          </h3>
          <p className="mt-2 text-sm leading-relaxed text-muted">
            Real randomized email data. Get Qini / T-learner / causal forest
            working before moving to synthetic credit.
          </p>
          {p1Qini !== undefined ? (
            <p className="mt-5 break-words font-mono text-sm text-ink">
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
          className="group rounded-xl border border-edge bg-surface p-5 transition hover:border-amber/50 sm:p-6"
        >
          <p className="font-mono text-[11px] uppercase tracking-widest text-amber">
            Phase 2
          </p>
          <h3 className="mt-2 font-display text-xl text-ink group-hover:text-amber sm:text-2xl">
            Synthetic credit RCT
          </h3>
          <p className="mt-2 text-sm leading-relaxed text-muted">
            Known true CATE. See if the models find Persuadables and keep
            Sleeping Dogs out of the top decile.
          </p>
          {p2Pehe !== undefined && p2Contamination !== undefined ? (
            <p className="mt-5 break-words font-mono text-sm text-ink">
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
          hint="It ranks who looks likely to succeed, not who changes because of treatment."
        />
        <Stat
          label="Accent choice"
          value="Amber"
          hint="Dark UI with amber highlights for the main results and callouts."
        />
        <Stat
          label="Layers"
          value="Static JSON"
          hint="This dashboard only reads exported results. It does not retrain models."
        />
      </section>
    </div>
  );
}
