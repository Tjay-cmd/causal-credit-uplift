import Link from "next/link";
import { QuadrantBadge } from "@/components/Quadrant";
import { Callout, Section } from "@/components/ui";

export default function MethodologyPage() {
  return (
    <div className="space-y-10 md:space-y-12">
      <header className="max-w-3xl space-y-3 md:space-y-4">
        <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-amber">
          Methodology
        </p>
        <h1 className="font-display text-3xl tracking-tight text-ink sm:text-4xl md:text-5xl">
          How to read this project
        </h1>
        <p className="text-base leading-relaxed text-muted sm:text-lg">
          Quick notes on the models and metrics so the charts make sense without
          opening the notebooks again.
        </p>
      </header>

      <Section title="T-learner vs CausalForestDML">
        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-lg border border-edge bg-surface p-5">
            <p className="font-mono text-[11px] uppercase tracking-widest text-amber">
              T-learner
            </p>
            <p className="mt-2 text-sm leading-relaxed text-muted">
              Train one outcome model on treated customers and one on control,
              then score everyone with CATE(x) = mu1(x) - mu0(x). Simple baseline.
              The two models can disagree in thin regions of the data.
            </p>
          </div>
          <div className="rounded-lg border border-edge bg-surface p-5">
            <p className="font-mono text-[11px] uppercase tracking-widest text-amber">
              CausalForestDML
            </p>
            <p className="mt-2 text-sm leading-relaxed text-muted">
              Double ML setup with a forest for heterogeneous effects. It first
              fits nuisance models for the outcome and treatment, then estimates
              CATE on the residuals. I used this in Phase 2 because the true
              effects differ a lot by segment.
            </p>
          </div>
        </div>
      </Section>

      <Section title="Qini vs PEHE">
        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-lg border border-edge bg-surface p-5">
            <p className="font-display text-xl text-ink">Qini / uplift-at-k</p>
            <p className="mt-2 text-sm leading-relaxed text-muted">
              Rank people by predicted CATE and check whether treated outcomes
              beat control near the top of the list. You only need the RCT
              labels for this, so it is closer to what you can measure in a real
              campaign.
            </p>
          </div>
          <div className="rounded-lg border border-edge bg-surface p-5">
            <p className="font-display text-xl text-ink">PEHE</p>
            <p className="mt-2 text-sm leading-relaxed text-muted">
              Mean squared error between predicted CATE and true CATE. You only
              get this with simulated ground truth (Phase 2). Useful when you
              care about recovering effect sizes, not just ranking.
            </p>
          </div>
        </div>
      </Section>

      <Section title="Why AUC / accuracy are wrong here">
        <Callout title="Different question">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start">
            <div className="flex items-center gap-2 sm:pt-0.5">
              <QuadrantBadge active="Sure Things" size={24} />
              <span className="font-mono text-[11px] uppercase tracking-widest text-amber sm:hidden">
                Sure Things
              </span>
            </div>
            <p className="min-w-0 flex-1 leading-relaxed">
              A classifier that predicts <em>good standing</em> or <em>visit</em>{" "}
              will push Sure Things to the top (people who succeed anyway).
              Uplift wants Persuadables and needs to avoid Sleeping Dogs.
              Accuracy and AUC optimize the wrong thing for targeting.
            </p>
          </div>
        </Callout>
      </Section>

      <Section title="Look and feel">
        <p className="max-w-2xl text-sm leading-relaxed text-muted">
          Dark background with amber highlights on the main charts and callouts.
          The little 2x2 badge shows up wherever a segment is mentioned so
          Persuadables / Sleeping Dogs stay easy to spot.
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
