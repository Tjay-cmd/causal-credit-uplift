import { CateRecoveryChart } from "@/components/charts/CateRecoveryChart";
import { QiniChart } from "@/components/charts/QiniChart";
import { QuadrantBadge } from "@/components/Quadrant";
import { MetricsTable, PeheTable } from "@/components/Tables";
import { Callout, EmptyState, Section, Stat } from "@/components/ui";
import { loadPhase2 } from "@/lib/loadData";
import { fmtMult, fmtPct, fmtSigned } from "@/lib/format";
import type { SegmentKey } from "@/lib/types";

export default async function Phase2Page() {
  const data = await loadPhase2();

  if (!data) {
    return <EmptyState label="phase2.json missing — run export_dashboard_data.py" />;
  }

  const segments = data.generation.segments;
  const composition = data.segment_recovery.composition.filter(
    (r) => r.predicted_decile === "top",
  );

  return (
    <div className="space-y-14">
      <header className="max-w-3xl space-y-4">
        <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-amber">
          Phase 2 · Ground-truth validation
        </p>
        <h1 className="font-display text-4xl tracking-tight text-ink md:text-5xl">
          {data.meta.title}
        </h1>
        <p className="text-lg leading-relaxed text-muted">{data.meta.framing}</p>
      </header>

      <div className="grid gap-3 sm:grid-cols-3">
        <Stat
          label="Simulated n"
          value={data.generation.n_total.toLocaleString()}
          hint={`Treatment share ${fmtPct(data.generation.treatment_share)}`}
        />
        <Stat label="Test n" value={String(data.meta.n_test)} />
        <Stat
          label="Safer on contamination"
          value={data.segment_recovery.safer_model}
          hint={fmtPct(data.segment_recovery.safer_sleeping_dogs_rate, 2) + " Sleeping Dogs in top decile"}
        />
      </div>

      <Section eyebrow="Answer key" title="Latent segments (DGP)">
        <div className="grid gap-3 md:grid-cols-2">
          {segments.map((seg) => (
            <div
              key={seg.segment}
              className={`rounded-lg border bg-surface p-4 ${
                seg.segment === "Sleeping Dogs" || seg.segment === "Persuadables"
                  ? "border-amber/35"
                  : "border-edge"
              }`}
            >
              <div className="mb-3 flex items-center gap-3">
                <QuadrantBadge active={seg.segment as SegmentKey} size={30} />
                <div>
                  <p className="font-display text-lg text-ink">{seg.segment}</p>
                  <p className="font-mono text-xs text-amber">
                    true CATE {fmtSigned(seg.mean_true_cate)} · share{" "}
                    {fmtPct(seg.share)} · obs gap {fmtSigned(seg.obs_gap)}
                  </p>
                </div>
              </div>
              <p className="text-sm leading-relaxed text-muted">{seg.traits}</p>
            </div>
          ))}
        </div>
      </Section>

      <Section
        eyebrow="Centerpiece"
        title="True vs recovered mean CATE"
        className="space-y-5"
      >
        <p className="max-w-2xl text-sm text-muted">
          Grouped bars: ground-truth mean CATE vs T-learner vs CausalForestDML on
          the held-out test set. This is the Phase 2 proof that models recover the
          DGP — not just overall risk.
        </p>
        <CateRecoveryChart rows={data.cate_recovery.by_segment} />
        <PeheTable rows={data.cate_recovery.overall} />
      </Section>

      <Section eyebrow="Policy ranking" title="Qini curves">
        <QiniChart models={data.models} />
        <MetricsTable models={data.models} />
      </Section>

      <Section eyebrow="Operational targeting" title="Top-decile true-segment mix">
        <p className="text-sm text-muted">
          If you treat the top 10% by predicted CATE, who do you actually reach?
        </p>
        <div className="overflow-x-auto rounded-lg border border-edge">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead className="bg-surface-2 font-mono text-[10px] uppercase tracking-widest text-muted">
              <tr>
                <th className="px-4 py-3">Model</th>
                <th className="px-4 py-3">True segment</th>
                <th className="px-4 py-3">% of top</th>
                <th className="px-4 py-3">Pop share</th>
                <th className="px-4 py-3">Enrichment</th>
              </tr>
            </thead>
            <tbody>
              {composition.map((r) => (
                <tr
                  key={`${r.model}-${r.true_segment}`}
                  className="border-t border-edge bg-surface"
                >
                  <td className="px-4 py-2 text-ink">{r.model}</td>
                  <td className="px-4 py-2">
                    <span className="inline-flex items-center gap-2">
                      <QuadrantBadge active={r.true_segment as SegmentKey} size={18} />
                      {r.true_segment}
                    </span>
                  </td>
                  <td className="px-4 py-2 font-mono text-amber">
                    {fmtPct(r.pct_of_decile)}
                  </td>
                  <td className="px-4 py-2 font-mono">{fmtPct(r.pop_share)}</td>
                  <td className="px-4 py-2 font-mono">{fmtMult(r.enrichment)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="grid gap-3 md:grid-cols-2">
          {data.segment_recovery.ops_summaries.map((s) => (
            <Callout
              key={s.model}
              tone={s.model === data.segment_recovery.safer_model ? "amber" : "muted"}
              title={s.model}
            >
              <p>{s.deploy_line}</p>
              <p className="font-mono text-xs text-muted">
                Persuadables {fmtPct(s.top_pct_persuadables)} · Sleeping Dogs{" "}
                {fmtPct(s.top_pct_sleeping_dogs, 2)}
              </p>
            </Callout>
          ))}
        </div>
      </Section>

      <Section eyebrow="Closing" title="A metric tradeoff, not a single winner">
        <Callout tone="amber" title="Qini vs PEHE vs contamination">
          <p>
            <span className="font-mono text-amber">{data.metric_tradeoff.qini_winner}</span>{" "}
            wins Qini ranking;{" "}
            <span className="font-mono text-amber">{data.metric_tradeoff.pehe_winner}</span>{" "}
            wins PEHE;{" "}
            <span className="font-mono text-amber">
              {data.metric_tradeoff.contamination_safer}
            </span>{" "}
            is safer on Sleeping Dogs contamination in the top decile.
          </p>
          <p>{data.metric_tradeoff.note}</p>
        </Callout>
      </Section>
    </div>
  );
}
