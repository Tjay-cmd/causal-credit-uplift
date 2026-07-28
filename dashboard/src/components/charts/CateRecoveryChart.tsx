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
import { useIsMobile } from "@/lib/useIsMobile";
import { EmptyState } from "../ui";

const SHORT_SEGMENT: Record<string, string> = {
  Persuadables: "Pers.",
  "Sure Things": "Sure",
  "Lost Causes": "Lost",
  "Sleeping Dogs": "Dogs",
};

type Props = {
  rows: CateBySegment[] | null | undefined;
};

export function CateRecoveryChart({ rows }: Props) {
  const mobile = useIsMobile();
  const [ready, setReady] = useState(false);
  useEffect(() => {
    const t = requestAnimationFrame(() => setReady(true));
    return () => cancelAnimationFrame(t);
  }, []);

  if (!rows?.length) {
    return <EmptyState label="CATE recovery series unavailable" />;
  }

  const data = rows.map((r) => ({
    ...r,
    label: mobile ? SHORT_SEGMENT[r.segment] ?? r.segment : r.segment,
  }));

  const height = mobile ? 300 : 420;

  return (
    <div
      className={`rounded-lg border border-amber/35 bg-surface p-2 transition-all duration-700 sm:p-3 md:p-5 ${
        ready ? "translate-y-0 opacity-100" : "translate-y-3 opacity-0"
      }`}
    >
      <div className="w-full min-w-0" style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            margin={{
              top: 12,
              right: mobile ? 4 : 12,
              left: 0,
              bottom: mobile ? 4 : 8,
            }}
            barCategoryGap={mobile ? "12%" : "18%"}
          >
            <CartesianGrid
              stroke={chartTheme.grid}
              strokeDasharray="3 3"
              vertical={false}
            />
            <XAxis
              dataKey="label"
              stroke={chartTheme.axis}
              tick={{ fill: chartTheme.muted, fontSize: mobile ? 10 : 12 }}
              interval={0}
            />
            <YAxis
              stroke={chartTheme.axis}
              tick={{ fill: chartTheme.muted, fontSize: mobile ? 10 : 11 }}
              tickFormatter={(v) => Number(v).toFixed(2)}
              width={mobile ? 40 : 52}
            />
            <Tooltip
              contentStyle={{
                background: chartTheme.tooltipBg,
                border: `1px solid ${chartTheme.tooltipBorder}`,
                borderRadius: 8,
                fontSize: 12,
              }}
              labelFormatter={(_, payload) => {
                const row = payload?.[0]?.payload as CateBySegment | undefined;
                return row?.segment ?? "";
              }}
              formatter={(value) =>
                typeof value === "number"
                  ? value.toFixed(4)
                  : String(value ?? "-")
              }
            />
            <Legend
              wrapperStyle={{ fontSize: mobile ? 11 : 12, color: chartTheme.muted }}
            />
            <Bar
              dataKey="mean_true_cate"
              name="True CATE"
              fill={chartTheme.trueCate}
              radius={[3, 3, 0, 0]}
            />
            <Bar
              dataKey="t_learner"
              name="T-learner"
              fill={chartTheme.modelA}
              radius={[3, 3, 0, 0]}
            />
            <Bar
              dataKey="causal_forest"
              name={mobile ? "CausalForest" : "CausalForestDML"}
              fill={chartTheme.modelB}
              radius={[3, 3, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
