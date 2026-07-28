import type { SegmentKey } from "@/lib/types";

const SEGMENTS: SegmentKey[] = [
  "Persuadables",
  "Sure Things",
  "Lost Causes",
  "Sleeping Dogs",
];

/** Mini 2×2 motif — signature device when a segment is referenced. */
export function QuadrantBadge({
  active,
  size = 28,
}: {
  active?: SegmentKey | null;
  size?: number;
}) {
  const positions: Record<SegmentKey, string> = {
    Persuadables: "top-0 left-0",
    "Sure Things": "top-0 right-0",
    "Lost Causes": "bottom-0 left-0",
    "Sleeping Dogs": "bottom-0 right-0",
  };

  return (
    <div
      className="relative grid grid-cols-2 grid-rows-2 gap-px rounded-sm bg-edge p-px"
      style={{ width: size, height: size }}
      aria-hidden
    >
      {SEGMENTS.map((seg) => {
        const isActive = active === seg;
        return (
          <div
            key={seg}
            className={`relative ${positions[seg]} ${
              isActive ? "bg-amber" : "bg-surface-2"
            }`}
            title={seg}
          />
        );
      })}
    </div>
  );
}

/** Full labeled 2×2 diagram for landing / methodology. */
export function QuadrantDiagram() {
  const cells: Array<{
    key: SegmentKey;
    cate: string;
    blurb: string;
  }> = [
    {
      key: "Persuadables",
      cate: "CATE > 0",
      blurb: "Respond because of treatment — the targeting prize.",
    },
    {
      key: "Sure Things",
      cate: "CATE ≈ 0",
      blurb: "Succeed either way. Risk models love them; uplift does not.",
    },
    {
      key: "Lost Causes",
      cate: "CATE ≈ 0",
      blurb: "Fail either way. Ranking by outcome alone still misses this.",
    },
    {
      key: "Sleeping Dogs",
      cate: "CATE < 0",
      blurb: "Treatment backfires. The costly mistake in a treated list.",
    },
  ];

  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {cells.map((cell) => (
        <div
          key={cell.key}
          className={`rounded-lg border border-edge bg-surface p-4 ${
            cell.key === "Sleeping Dogs" || cell.key === "Persuadables"
              ? "border-amber/30"
              : ""
          }`}
        >
          <div className="mb-3 flex items-center gap-3">
            <QuadrantBadge active={cell.key} size={32} />
            <div>
              <p className="font-display text-lg text-ink">{cell.key}</p>
              <p className="font-mono text-xs text-amber">{cell.cate}</p>
            </div>
          </div>
          <p className="text-sm leading-relaxed text-muted">{cell.blurb}</p>
        </div>
      ))}
    </div>
  );
}
