import { CateRecoveryChart } from "@/components/charts/CateRecoveryChart";
import { QiniChart } from "@/components/charts/QiniChart";
import { QuadrantBadge } from "@/components/Quadrant";
import { TableScroll } from "@/components/TableScroll";
import { MetricsTable, PeheTable } from "@/components/Tables";
import { Callout, EmptyState, Section, Stat } from "@/components/ui";
import { loadPhase2 } from "@/lib/loadData";
import { fmtMult, fmtPct, fmtSigned } from "@/lib/format";
import type { SegmentKey } from "@/lib/types";

export default async function Phase2Page() {
  const data = await loadPhase2();

  if (!data) {
    return <EmptyState label="phase2.json missing. Run export_dashboard_data.py first." />;
  }

  const segments = data.generation.segments;
  const composition = data.segment_recovery.composition.filter(
    (r) => r.predicted_decile === "top",
  );

  return (
    <div className="space-y-10 md:space-y-14">
      <header className="max-w-3xl space-y-3 md:space-y-4">
        <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-amber">
          Phase 2 · Ground-truth check
        </p>
        <h1 className="font-display text-3xl tracking-tight text-ink sm:text-4xl md:text-5xl">
          {data.meta.title}
        </h1>
        <p className="text-base leading-relaxed text-muted sm:text-lg">{data.meta.framing}</p>
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

      <Section eyebrow="Built-in answer key" title="Latent segments (DGP)">
        <div className="grid gap-3 md:grid-cols-2">
          {segments.map((seg) => (
            <div
              key={seg.segment}
              className={`min-w-0 rounded-lg border bg-surface p-4 ${
                seg.segment === "Sleeping Dogs" || seg.segment === "Persuadables"
                  ? "border-amber/35"
                  : "border-edge"
              }`}
            >
              <div className="mb-3 flex items-start gap-3">
                <QuadrantBadge active={seg.segment as SegmentKey} size={30} />
                <div className="min-w-0">
                  <p className="font-display text-lg text-ink">{seg.segment}</p>
                  <p className="break-words font-mono text-xs leading-relaxed text-amber">
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
        eyebrow="Main result"
        title="True vs recovered mean CATE"
        className="space-y-5"
      >
        <p className="max-w-2xl text-sm text-muted">
          Grouped bars compare true mean CATE to T-learner and CausalForestDML on
          the test set. This is the check that the models recover the simulated
          segments, not just overall good_standing risk.
        </p>
        <CateRecoveryChart rows={data.cate_recovery.by_segment} />
        <PeheTable rows={data.cate_recovery.overall} />
      </Section>

      <Section eyebrow="Policy ranking" title="Qini curves">
        <QiniChart models={data.models} />
        <MetricsTable models={data.models} />
      </Section>

      <Section eyebrow="Who would get treated" title="Top-decile true-segment mix">
        <p className="text-sm text-muted">
          If you treat the top 10% by predicted CATE, which true segments show up?
        </p>
        <TableScroll>
          <table className="w-full min-w-[560px] border-collapse text-left text-sm">
            <thead className="bg-surface-2 font-mono text-[10px] uppercase tracking-widest text-muted">
              <tr>
                <th className="whitespace-nowrap px-3 py-3 sm:px-4">Model</th>
                <th className="whitespace-nowrap px-3 py-3 sm:px-4">True segment</th>
                <th className="whitespace-nowrap px-3 py-3 sm:px-4">% of top</th>
                <th className="whitespace-nowrap px-3 py-3 sm:px-4">Pop share</th>
                <th className="whitespace-nowrap px-3 py-3 sm:px-4">Enrichment</th>
              </tr>
            </thead>
            <tbody>
              {composition.map((r) => (
                <tr
                  key={`${r.model}-${r.true_segment}`}
                  className="border-t border-edge bg-surface"
                >
                  <td className="whitespace-nowrap px-3 py-2 text-ink sm:px-4">{r.model}</td>
                  <td className="px-3 py-2 sm:px-4">
                    <span className="inline-flex items-center gap-2">
                      <QuadrantBadge active={r.true_segment as SegmentKey} size={18} />
                      {r.true_segment}
                    </span>
                  </td>
                  <td className="px-3 py-2 font-mono text-amber sm:px-4">
                    {fmtPct(r.pct_of_decile)}
                  </td>
                  <td className="px-3 py-2 font-mono sm:px-4">{fmtPct(r.pop_share)}</td>
                  <td className="px-3 py-2 font-mono sm:px-4">{fmtMult(r.enrichment)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </TableScroll>

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

      <Section eyebrow="Takeaway" title="Different metrics, different winner">
        <Callout tone="amber" title="Qini vs PEHE vs contamination">
          <p>
            <span className="font-mono text-amber">{data.metric_tradeoff.qini_winner}</span>{" "}
            wins Qini ranking.{" "}
            <span className="font-mono text-amber">{data.metric_tradeoff.pehe_winner}</span>{" "}
            wins PEHE.{" "}
            <span className="font-mono text-amber">
              {data.metric_tradeoff.contamination_safer}
            </span>{" "}
            puts fewer Sleeping Dogs in the top decile.
          </p>
          <p>{data.metric_tradeoff.note}</p>
        </Callout>
      </Section>
    </div>
  );
}
