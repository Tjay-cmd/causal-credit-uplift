"use client";

import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { CateBySegment } from "@/lib/types";
import { chartTheme } from "@/lib/chartTheme";
import { EmptyState } from "../ui";

type Props = {
  rows: CateBySegment[] | null | undefined;
};

export function CateRecoveryChart({ rows }: Props) {
  const [ready, setReady] = useState(false);
  useEffect(() => {
    const t = requestAnimationFrame(() => setReady(true));
    return () => cancelAnimationFrame(t);
  }, []);

  if (!rows?.length) {
    return <EmptyState label="CATE recovery series unavailable" />;
  }

  return (
    <div
      className={`rounded-lg border border-amber/35 bg-surface p-3 transition-all duration-700 md:p-5 ${
        ready ? "translate-y-0 opacity-100" : "translate-y-3 opacity-0"
      }`}
    >
      <ResponsiveContainer width="100%" height={420}>
        <BarChart
          data={rows}
          margin={{ top: 12, right: 12, left: 0, bottom: 8 }}
          barCategoryGap="18%"
        >
          <CartesianGrid stroke={chartTheme.grid} strokeDasharray="3 3" vertical={false} />
          <XAxis
            dataKey="segment"
            stroke={chartTheme.axis}
            tick={{ fill: chartTheme.muted, fontSize: 12 }}
          />
          <YAxis
            stroke={chartTheme.axis}
            tick={{ fill: chartTheme.muted, fontSize: 11 }}
            tickFormatter={(v) => Number(v).toFixed(2)}
            width={52}
          />
          <Tooltip
            contentStyle={{
              background: chartTheme.tooltipBg,
              border: `1px solid ${chartTheme.tooltipBorder}`,
              borderRadius: 8,
              fontSize: 12,
            }}
            formatter={(value) =>
              typeof value === "number" ? value.toFixed(4) : String(value ?? "—")
            }
          />
          <Legend wrapperStyle={{ fontSize: 12, color: chartTheme.muted }} />
          <Bar dataKey="mean_true_cate" name="True CATE" fill={chartTheme.trueCate} radius={[3, 3, 0, 0]} />
          <Bar dataKey="t_learner" name="T-learner" fill={chartTheme.modelA} radius={[3, 3, 0, 0]} />
          <Bar
            dataKey="causal_forest"
            name="CausalForestDML"
            fill={chartTheme.modelB}
            radius={[3, 3, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
