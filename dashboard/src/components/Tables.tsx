import type { ModelMetrics } from "@/lib/types";
import { fmtNum, fmtPct } from "@/lib/format";
import { EmptyState } from "./ui";
import { TableScroll } from "./TableScroll";

export function MetricsTable({ models }: { models: ModelMetrics[] | null | undefined }) {
  if (!models?.length) {
    return <EmptyState label="Metrics table unavailable" />;
  }

  return (
    <TableScroll>
      <table className="w-full min-w-[480px] border-collapse text-left text-sm">
        <thead className="bg-surface-2 font-mono text-[10px] uppercase tracking-widest text-muted">
          <tr>
            <th className="whitespace-nowrap px-3 py-3 sm:px-4">Model</th>
            <th className="whitespace-nowrap px-3 py-3 sm:px-4">Qini</th>
            <th className="whitespace-nowrap px-3 py-3 sm:px-4">Uplift@10%</th>
            <th className="whitespace-nowrap px-3 py-3 sm:px-4">Uplift@30%</th>
            <th className="whitespace-nowrap px-3 py-3 sm:px-4">Uplift@50%</th>
          </tr>
        </thead>
        <tbody>
          {models.map((m) => (
            <tr key={m.model} className="border-t border-edge bg-surface">
              <td className="whitespace-nowrap px-3 py-3 font-medium text-ink sm:px-4">
                {m.model}
              </td>
              <td className="px-3 py-3 font-mono text-amber sm:px-4">
                {fmtNum(m.qini_coefficient, 2)}
              </td>
              <td className="px-3 py-3 font-mono sm:px-4">{fmtNum(m.uplift_at_10pct)}</td>
              <td className="px-3 py-3 font-mono sm:px-4">{fmtNum(m.uplift_at_30pct)}</td>
              <td className="px-3 py-3 font-mono sm:px-4">{fmtNum(m.uplift_at_50pct)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </TableScroll>
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
    <TableScroll>
      <table className="w-full min-w-[360px] border-collapse text-left text-sm">
        <thead className="bg-surface-2 font-mono text-[10px] uppercase tracking-widest text-muted">
          <tr>
            <th className="whitespace-nowrap px-3 py-3 sm:px-4">Model</th>
            <th className="whitespace-nowrap px-3 py-3 sm:px-4">PEHE</th>
            <th className="whitespace-nowrap px-3 py-3 sm:px-4">corr(pred, true)</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.model} className="border-t border-edge bg-surface">
              <td className="whitespace-nowrap px-3 py-3 text-ink sm:px-4">{r.model}</td>
              <td className="px-3 py-3 font-mono text-amber sm:px-4">
                {fmtNum(r.pehe, 4)}
              </td>
              <td className="px-3 py-3 font-mono sm:px-4">
                {fmtNum(r.corr_pred_true_cate, 3)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </TableScroll>
  );
}

type Profile = {
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
};

export function ProfileCompare({
  top,
  bottom,
}: {
  top: Profile | null;
  bottom: Profile | null;
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
    <div className="min-w-0 space-y-3">
      {/* Mobile: stacked cards so nothing is clipped */}
      <div className="space-y-2 md:hidden">
        {rows.map((r) => (
          <div
            key={r.label}
            className="rounded-lg border border-edge bg-surface px-3 py-3"
          >
            <p className="text-xs text-muted">{r.label}</p>
            <div className="mt-2 grid grid-cols-2 gap-3">
              <div>
                <p className="font-mono text-[10px] uppercase tracking-widest text-amber">
                  Top decile
                </p>
                <p className="mt-0.5 break-words font-mono text-sm text-ink">{r.a}</p>
              </div>
              <div>
                <p className="font-mono text-[10px] uppercase tracking-widest text-muted">
                  Bottom decile
                </p>
                <p className="mt-0.5 break-words font-mono text-sm text-ink">{r.b}</p>
              </div>
            </div>
          </div>
        ))}
        <p className="font-mono text-[11px] text-muted">
          Profiles shown for {top.model} (Phase 1 top vs bottom decile).
        </p>
      </div>

      {/* Desktop / wide: scrollable table */}
      <div className="hidden md:block">
        <TableScroll hint="Drag sideways to see more columns">
          <table className="w-full min-w-[520px] border-collapse text-left text-sm">
            <thead className="bg-surface-2 font-mono text-[10px] uppercase tracking-widest text-muted">
              <tr>
                <th className="px-3 py-3 sm:px-4">Feature</th>
                <th className="whitespace-nowrap px-3 py-3 text-amber sm:px-4">
                  Top decile
                </th>
                <th className="whitespace-nowrap px-3 py-3 sm:px-4">Bottom decile</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.label} className="border-t border-edge bg-surface">
                  <td className="px-3 py-2.5 text-muted sm:px-4">{r.label}</td>
                  <td className="whitespace-nowrap px-3 py-2.5 font-mono text-ink sm:px-4">
                    {r.a}
                  </td>
                  <td className="whitespace-nowrap px-3 py-2.5 font-mono text-ink sm:px-4">
                    {r.b}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="border-t border-edge px-3 py-2 font-mono text-[11px] text-muted sm:px-4">
            Profiles shown for {top.model} (Phase 1 top vs bottom decile).
          </p>
        </TableScroll>
      </div>
    </div>
  );
}
