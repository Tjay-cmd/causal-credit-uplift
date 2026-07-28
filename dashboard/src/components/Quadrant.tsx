import type { SegmentKey } from "@/lib/types";

const SEGMENTS: SegmentKey[] = [
  "Persuadables",
  "Sure Things",
  "Lost Causes",
  "Sleeping Dogs",
];

/** Small 2x2 badge used wherever a segment is mentioned. */
export function QuadrantBadge({
  active,
  size = 28,
  className = "",
}: {
  active?: SegmentKey | null;
  size?: number;
  className?: string;
}) {
  return (
    <div
      className={`grid shrink-0 grid-cols-2 grid-rows-2 gap-px overflow-hidden rounded-sm bg-edge p-px ${className}`}
      style={{ width: size, height: size, minWidth: size, minHeight: size }}
      aria-hidden
      title={active ?? undefined}
    >
      {SEGMENTS.map((seg) => (
        <div
          key={seg}
          className={active === seg ? "bg-amber" : "bg-surface-2"}
        />
      ))}
    </div>
  );
}

/** Full labeled 2x2 diagram for landing / methodology. */
export function QuadrantDiagram() {
  const cells: Array<{
    key: SegmentKey;
    cate: string;
    blurb: string;
  }> = [
    {
      key: "Persuadables",
      cate: "CATE > 0",
      blurb: "Only get better because you treated them. These are the people you want.",
    },
    {
      key: "Sure Things",
      cate: "CATE ≈ 0",
      blurb: "Do well either way. Risk models love them. Uplift mostly ignores them.",
    },
    {
      key: "Lost Causes",
      cate: "CATE ≈ 0",
      blurb: "Do poorly either way. Low outcome score, but treatment still barely helps.",
    },
    {
      key: "Sleeping Dogs",
      cate: "CATE < 0",
      blurb: "Treatment makes things worse. Bad people to put on a treated list.",
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
            <div className="min-w-0">
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
