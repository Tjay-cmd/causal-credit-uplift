"use client";

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ModelMetrics } from "@/lib/types";
import { chartTheme } from "@/lib/chartTheme";
import { useIsMobile } from "@/lib/useIsMobile";
import { EmptyState } from "../ui";

type Props = {
  models: ModelMetrics[] | null | undefined;
  height?: number;
};

export function QiniChart({ models, height }: Props) {
  const mobile = useIsMobile();
  const chartHeight = height ?? (mobile ? 260 : 340);

  if (!models?.length || !models[0]?.curve?.length) {
    return <EmptyState label="Qini curve data unavailable" />;
  }

  const n = Math.min(...models.map((m) => m.curve.length));
  const merged = Array.from({ length: n }, (_, i) => {
    const row: Record<string, number> = {
      fraction: models[0].curve[i].fraction,
      random: models[0].curve[i].random,
    };
    models.forEach((m) => {
      const key = m.model === "T-learner" ? "tLearner" : "causalForest";
      row[key] = m.curve[i]?.qini ?? 0;
    });
    return row;
  });

  return (
    <div className="rounded-lg border border-edge bg-surface p-2 sm:p-3 md:p-4">
      <div className="w-full min-w-0" style={{ height: chartHeight }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={merged}
            margin={{
              top: 8,
              right: mobile ? 4 : 12,
              left: 0,
              bottom: mobile ? 4 : 8,
            }}
          >
            <CartesianGrid stroke={chartTheme.grid} strokeDasharray="3 3" />
            <XAxis
              dataKey="fraction"
              type="number"
              domain={[0, 1]}
              tickFormatter={(v) => `${Math.round(v * 100)}%`}
              stroke={chartTheme.axis}
              tick={{ fill: chartTheme.muted, fontSize: mobile ? 10 : 11 }}
              label={
                mobile
                  ? undefined
                  : {
                      value: "Population fraction targeted",
                      position: "insideBottom",
                      offset: -2,
                      fill: chartTheme.muted,
                      fontSize: 11,
                    }
              }
            />
            <YAxis
              stroke={chartTheme.axis}
              tick={{ fill: chartTheme.muted, fontSize: mobile ? 10 : 11 }}
              width={mobile ? 36 : 48}
            />
            <Tooltip
              contentStyle={{
                background: chartTheme.tooltipBg,
                border: `1px solid ${chartTheme.tooltipBorder}`,
                borderRadius: 8,
                fontSize: 12,
              }}
              labelFormatter={(v) => `Fraction ${(Number(v) * 100).toFixed(0)}%`}
            />
            <Legend
              wrapperStyle={{ fontSize: mobile ? 11 : 12, color: chartTheme.muted }}
            />
            <Line
              type="monotone"
              dataKey="random"
              name="Random"
              stroke={chartTheme.random}
              strokeDasharray="4 4"
              dot={false}
              strokeWidth={1.5}
            />
            <Line
              type="monotone"
              dataKey="tLearner"
              name="T-learner"
              stroke={chartTheme.modelA}
              dot={false}
              strokeWidth={2}
            />
            <Line
              type="monotone"
              dataKey="causalForest"
              name={mobile ? "CausalForest" : "CausalForestDML"}
              stroke={chartTheme.modelB}
              dot={false}
              strokeWidth={2}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
