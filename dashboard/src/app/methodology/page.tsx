import Link from "next/link";
import { QuadrantBadge } from "@/components/Quadrant";
import { Callout, Section } from "@/components/ui";

export default function MethodologyPage() {
  return (
    <div className="space-y-12">
      <header className="max-w-3xl space-y-4">
        <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-amber">
          Methodology
        </p>
        <h1 className="font-display text-4xl tracking-tight text-ink md:text-5xl">
          How to read this project
        </h1>
        <p className="text-lg leading-relaxed text-muted">
          Short notes on estimators and metrics — enough to interpret the charts
          without reopening the notebooks.
        </p>
      </header>

      <Section title="T-learner vs CausalForestDML">
        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-lg border border-edge bg-surface p-5">
            <p className="font-mono text-[11px] uppercase tracking-widest text-amber">
              T-learner
            </p>
            <p className="mt-2 text-sm leading-relaxed text-muted">
              Fit separate outcome models on treated and control units, then
              score everyone with ĈATE(x) = μ₁(x) − μ₀(x). Simple, strong baseline;
              two models can diverge in regions with little overlap.
            </p>
          </div>
          <div className="rounded-lg border border-edge bg-surface p-5">
            <p className="font-mono text-[11px] uppercase tracking-widest text-amber">
              CausalForestDML
            </p>
            <p className="mt-2 text-sm leading-relaxed text-muted">
              Double/debiased ML with a forest final stage for heterogeneous
              effects. Orthogonalizes outcome and treatment nuisances before
              estimating CATE — the Phase 2 choice for recovering flexible
              segment effects.
            </p>
          </div>
        </div>
      </Section>

      <Section title="Qini vs PEHE">
        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-lg border border-edge bg-surface p-5">
            <p className="font-display text-xl text-ink">Qini / uplift-at-k</p>
            <p className="mt-2 text-sm leading-relaxed text-muted">
              Policy metrics from the RCT alone: rank by predicted CATE and ask
              whether treated outcomes beat control in the top of the list. No
              ground truth required — what you can measure in production.
            </p>
          </div>
          <div className="rounded-lg border border-edge bg-surface p-5">
            <p className="font-display text-xl text-ink">PEHE</p>
            <p className="mt-2 text-sm leading-relaxed text-muted">
              Precision in Estimating Heterogeneous Effects: mean squared error
              between predicted and true CATE. Only possible with a simulated
              answer key (Phase 2). Complements Qini when you care about effect
              size recovery, not only ranking.
            </p>
          </div>
        </div>
      </Section>

      <Section title="Why AUC / accuracy are wrong here">
        <Callout title="Different scientific question">
          <div className="flex items-start gap-3">
            <QuadrantBadge active="Sure Things" />
            <p>
              A classifier that predicts <em>good standing</em> or <em>visit</em>{" "}
              will prefer Sure Things — people who succeed without treatment.
              Uplift wants Persuadables and must avoid Sleeping Dogs. Accuracy and
              AUC optimize the wrong objective for targeting decisions.
            </p>
          </div>
        </Callout>
      </Section>

      <Section title="Accent & presentation">
        <p className="max-w-2xl text-sm leading-relaxed text-muted">
          Electric amber on near-black is deliberate: uplift work is about
          spotting a hidden incremental signal that risk scoring alone would
          miss. The 2×2 badge is the recurring motif so Persuadables / Sleeping
          Dogs stay visually anchored wherever they appear.
        </p>
        <p className="mt-4 font-mono text-xs text-muted">
          Source:{" "}
          <a
            href="https://github.com/Tjay-cmd/causal-credit-uplift"
            target="_blank"
            rel="noopener noreferrer"
            className="text-amber hover:underline"
          >
            github.com/Tjay-cmd/causal-credit-uplift
          </a>
        </p>
        <p className="mt-6">
          <Link href="/" className="font-mono text-sm text-amber hover:underline">
            ← Back to overview
          </Link>
        </p>
      </Section>
    </div>
  );
}
