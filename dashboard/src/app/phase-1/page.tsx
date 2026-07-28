import { QiniChart } from "@/components/charts/QiniChart";
import { QuadrantBadge } from "@/components/Quadrant";
import { MetricsTable, ProfileCompare } from "@/components/Tables";
import { Callout, EmptyState, Section, Stat } from "@/components/ui";
import { loadPhase1 } from "@/lib/loadData";
import { fmtMult, fmtNum, fmtPct } from "@/lib/format";

export default async function Phase1Page() {
  const data = await loadPhase1();

  if (!data) {
    return <EmptyState label="phase1.json missing — run export_dashboard_data.py" />;
  }

  const tProfiles = data.segment_profiles.filter((p) => p.model === "T-learner");
  const top = tProfiles.find((p) => p.segment.includes("top_decile")) ?? null;
  const bottom = tProfiles.find((p) => p.segment.includes("bottom_decile")) ?? null;

  const gaps = data.negative_cate.category_gaps
    .slice()
    .sort((a, b) => Math.abs(b.gap_pp) - Math.abs(a.gap_pp))
    .slice(0, 6);

  return (
    <div className="space-y-14">
      <header className="max-w-3xl space-y-4">
        <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-amber">
          Phase 1 · Methodology validation
        </p>
        <h1 className="font-display text-4xl tracking-tight text-ink md:text-5xl">
          {data.meta.title}
        </h1>
        <p className="text-lg leading-relaxed text-muted">{data.meta.framing}</p>
      </header>

      <div className="grid gap-3 sm:grid-cols-3">
        <Stat label="Test n" value={String(data.meta.n_test)} />
        <Stat
          label="Top-decile overlap"
          value={fmtPct(data.model_overlap.overlap_share, 1)}
          hint={`Jaccard ${fmtNum(data.model_overlap.jaccard, 3)}`}
        />
        <Stat
          label="Neg. CATE share"
          value={fmtPct(data.negative_cate.share_of_test, 1)}
          hint={`${data.negative_cate.n_negative} of ${data.negative_cate.n_test} test rows`}
        />
      </div>

      <Section eyebrow="Policy ranking" title="Qini curves">
        <QiniChart models={data.models} />
        <MetricsTable models={data.models} />
      </Section>

      <Section eyebrow="Who is the model finding" title="Persuadables vs low-uplift profile">
        <div className="mb-3 flex items-center gap-2 text-sm text-muted">
          <QuadrantBadge active="Persuadables" />
          <span>Top decile by predicted CATE vs bottom decile</span>
        </div>
        <ProfileCompare top={top} bottom={bottom} />
      </Section>

      <Section eyebrow="Honest disagreement" title="Models do not name the same people">
        <Callout title="CATE uncertainty">
          <p>
            Top-decile customer overlap between T-learner and CausalForestDML is{" "}
            <span className="font-mono text-amber">
              {fmtPct(data.model_overlap.overlap_share, 1)}
            </span>{" "}
            ({data.model_overlap.n_intersection} of {data.model_overlap.n_top}; Jaccard{" "}
            {fmtNum(data.model_overlap.jaccard, 3)}). Feature tilts agree more than
            mailing lists.
          </p>
          <p className="text-muted">{data.model_overlap.agreement_flag}</p>
          <p>
            Framed honestly: CATE estimation carries more uncertainty than standard
            risk scoring — metric tables can look similar while the people each model
            would treat first differ.
          </p>
        </Callout>
      </Section>

      <Section eyebrow="Sleeping Dogs candidate" title="Concentrated negative CATE">
        <div className="mb-3 flex items-center gap-2 text-sm text-muted">
          <QuadrantBadge active="Sleeping Dogs" />
          <span>T-learner predicted CATE &lt; 0</span>
        </div>
        <Callout tone="amber" title="Real signal · small sample">
          <p>
            {data.negative_cate.n_negative} customers (
            {fmtPct(data.negative_cate.share_of_test, 1)} of test) have negative
            predicted CATE — mean {fmtNum(data.negative_cate.mean_predicted_cate)}.
            Not scattered noise: concentration vs full test set peaks at{" "}
            {gaps[0] ? (
              <>
                <span className="font-mono text-amber">
                  {gaps[0].feature}={gaps[0].level}
                </span>{" "}
                ({gaps[0].gap_pp > 0 ? "+" : ""}
                {fmtNum(gaps[0].gap_pp, 1)} pp)
              </>
            ) : (
              "—"
            )}
            .
          </p>
          <p className="text-muted">{data.negative_cate.framing}</p>
        </Callout>
        {gaps.length ? (
          <div className="mt-4 overflow-x-auto rounded-lg border border-edge">
            <table className="w-full min-w-[480px] text-left text-sm">
              <thead className="bg-surface-2 font-mono text-[10px] uppercase tracking-widest text-muted">
                <tr>
                  <th className="px-4 py-3">Feature</th>
                  <th className="px-4 py-3">Level</th>
                  <th className="px-4 py-3">Neg share</th>
                  <th className="px-4 py-3">Test share</th>
                  <th className="px-4 py-3">Gap</th>
                </tr>
              </thead>
              <tbody>
                {gaps.map((g) => (
                  <tr
                    key={`${g.feature}-${g.level}`}
                    className="border-t border-edge bg-surface"
                  >
                    <td className="px-4 py-2 text-muted">{g.feature}</td>
                    <td className="px-4 py-2 font-mono text-ink">{g.level}</td>
                    <td className="px-4 py-2 font-mono">{fmtPct(g.neg_share)}</td>
                    <td className="px-4 py-2 font-mono">{fmtPct(g.test_share)}</td>
                    <td className="px-4 py-2 font-mono text-amber">
                      {g.gap_pp > 0 ? "+" : ""}
                      {fmtNum(g.gap_pp, 1)} pp
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
        <p className="mt-3 font-mono text-xs text-muted">
          History mean in negative group ${fmtNum(data.negative_cate.history_mean_neg, 0)} vs
          test ${fmtNum(data.negative_cate.history_mean_test, 0)} (
          {fmtMult(
            data.negative_cate.history_mean_neg / data.negative_cate.history_mean_test,
          )}{" "}
          ratio).
        </p>
      </Section>
    </div>
  );
}
