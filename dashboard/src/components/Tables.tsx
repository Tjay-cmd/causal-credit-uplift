import type { ModelMetrics } from "@/lib/types";
import { fmtNum, fmtPct } from "@/lib/format";
import { EmptyState } from "./ui";

export function MetricsTable({ models }: { models: ModelMetrics[] | null | undefined }) {
  if (!models?.length) {
    return <EmptyState label="Metrics table unavailable" />;
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-edge">
      <table className="w-full min-w-[520px] text-left text-sm">
        <thead className="bg-surface-2 font-mono text-[10px] uppercase tracking-widest text-muted">
          <tr>
            <th className="px-4 py-3">Model</th>
            <th className="px-4 py-3">Qini</th>
            <th className="px-4 py-3">Uplift@10%</th>
            <th className="px-4 py-3">Uplift@30%</th>
            <th className="px-4 py-3">Uplift@50%</th>
          </tr>
        </thead>
        <tbody>
          {models.map((m) => (
            <tr key={m.model} className="border-t border-edge bg-surface">
              <td className="px-4 py-3 font-medium text-ink">{m.model}</td>
              <td className="px-4 py-3 font-mono text-amber">
                {fmtNum(m.qini_coefficient, 2)}
              </td>
              <td className="px-4 py-3 font-mono">{fmtNum(m.uplift_at_10pct)}</td>
              <td className="px-4 py-3 font-mono">{fmtNum(m.uplift_at_30pct)}</td>
              <td className="px-4 py-3 font-mono">{fmtNum(m.uplift_at_50pct)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function PeheTable({
  rows,
}: {
  rows:
    | Array<{
        model: string;
        pehe: number;
        corr_pred_true_cate: number;
      }>
    | null
    | undefined;
}) {
  if (!rows?.length) {
    return <EmptyState label="PEHE table unavailable" />;
  }
  return (
    <div className="overflow-x-auto rounded-lg border border-edge">
      <table className="w-full min-w-[420px] text-left text-sm">
        <thead className="bg-surface-2 font-mono text-[10px] uppercase tracking-widest text-muted">
          <tr>
            <th className="px-4 py-3">Model</th>
            <th className="px-4 py-3">PEHE</th>
            <th className="px-4 py-3">corr(pred, true)</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.model} className="border-t border-edge bg-surface">
              <td className="px-4 py-3 text-ink">{r.model}</td>
              <td className="px-4 py-3 font-mono text-amber">{fmtNum(r.pehe, 4)}</td>
              <td className="px-4 py-3 font-mono">{fmtNum(r.corr_pred_true_cate, 3)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function ProfileCompare({
  top,
  bottom,
}: {
  top: {
    model: string;
    recency_mean: number;
    history_mean: number;
    mens_rate: number;
    womens_rate: number;
    newbie_rate: number;
    history_segment_mode: string;
    zip_code_mode: string;
    channel_mode: string;
    obs_uplift: number;
  } | null;
  bottom: {
    model: string;
    recency_mean: number;
    history_mean: number;
    mens_rate: number;
    womens_rate: number;
    newbie_rate: number;
    history_segment_mode: string;
    zip_code_mode: string;
    channel_mode: string;
    obs_uplift: number;
  } | null;
}) {
  if (!top || !bottom) {
    return <EmptyState label="Segment profiles unavailable" />;
  }

  const rows = [
    { label: "Recency (mean months)", a: top.recency_mean.toFixed(1), b: bottom.recency_mean.toFixed(1) },
    { label: "History (mean $)", a: `$${top.history_mean.toFixed(0)}`, b: `$${bottom.history_mean.toFixed(0)}` },
    { label: "Mens purchase rate", a: fmtPct(top.mens_rate), b: fmtPct(bottom.mens_rate) },
    { label: "Womens purchase rate", a: fmtPct(top.womens_rate), b: fmtPct(bottom.womens_rate) },
    { label: "Newbie rate", a: fmtPct(top.newbie_rate), b: fmtPct(bottom.newbie_rate) },
    { label: "Modal history segment", a: top.history_segment_mode, b: bottom.history_segment_mode },
    { label: "Modal zip", a: top.zip_code_mode, b: bottom.zip_code_mode },
    { label: "Modal channel", a: top.channel_mode, b: bottom.channel_mode },
    { label: "Observed uplift in slice", a: fmtNum(top.obs_uplift), b: fmtNum(bottom.obs_uplift) },
  ];

  return (
    <div className="overflow-x-auto rounded-lg border border-edge">
      <table className="w-full min-w-[560px] text-left text-sm">
        <thead className="bg-surface-2 font-mono text-[10px] uppercase tracking-widest text-muted">
          <tr>
            <th className="px-4 py-3">Feature</th>
            <th className="px-4 py-3 text-amber">Top decile (Persuadables)</th>
            <th className="px-4 py-3">Bottom decile (low uplift)</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.label} className="border-t border-edge bg-surface">
              <td className="px-4 py-2.5 text-muted">{r.label}</td>
              <td className="px-4 py-2.5 font-mono text-ink">{r.a}</td>
              <td className="px-4 py-2.5 font-mono text-ink">{r.b}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="border-t border-edge px-4 py-2 font-mono text-[11px] text-muted">
        Profiles shown for {top.model} (primary Phase 1 segment narrative).
      </p>
    </div>
  );
}
