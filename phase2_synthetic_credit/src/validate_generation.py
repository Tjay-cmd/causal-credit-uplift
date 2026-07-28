"""Validate Phase 2 synthetic credit generation (no modeling).

Loads the modeling table + ground-truth table, checks the join, randomization,
segment proportions, and that observed treated-control gaps align with true_cate.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
DATA_DIR: Path = PROJECT_ROOT / "data"
FULL_PATH: Path = DATA_DIR / "synthetic_credit_full.parquet"
GT_PATH: Path = DATA_DIR / "synthetic_credit_ground_truth.parquet"

EXPECTED_PROPS: dict[str, float] = {
    "Persuadables": 0.20,
    "Sure Things": 0.30,
    "Lost Causes": 0.25,
    "Sleeping Dogs": 0.25,
}


def load_tables(
    full_path: Path = FULL_PATH,
    gt_path: Path = GT_PATH,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load both files and inner-join on customer_id."""
    if not full_path.exists() or not gt_path.exists():
        raise FileNotFoundError(
            f"Missing data files. Run generate_data.py first.\n"
            f"  expected: {full_path}\n  expected: {gt_path}"
        )
    full = pd.read_parquet(full_path)
    gt = pd.read_parquet(gt_path)

    if full["customer_id"].duplicated().any():
        raise AssertionError("Duplicate customer_id in modeling table.")
    if gt["customer_id"].duplicated().any():
        raise AssertionError("Duplicate customer_id in ground-truth table.")

    leak = {"segment", "true_cate", "baseline_prob", "true_prob"} & set(full.columns)
    if leak:
        raise AssertionError(f"Ground-truth columns leaked into modeling table: {leak}")

    merged = full.merge(gt, on="customer_id", how="inner", validate="one_to_one")
    if len(merged) != len(full) or len(merged) != len(gt):
        raise AssertionError(
            f"Join incomplete: full={len(full)}, gt={len(gt)}, merged={len(merged)}"
        )
    print(f"Join OK: {len(merged):,} rows on customer_id")
    return full, gt, merged


def print_segment_proportions(merged: pd.DataFrame) -> None:
    print("\n=== Segment size proportions ===")
    props = merged["segment"].value_counts(normalize=True)
    counts = merged["segment"].value_counts()
    for seg, target in EXPECTED_PROPS.items():
        p = float(props.get(seg, 0.0))
        n = int(counts.get(seg, 0))
        print(f"  {seg:15s}  n={n:6,}  share={p:.4f}  target={target:.2f}  "
              f"gap={p - target:+.4f}")


def print_randomization_check(merged: pd.DataFrame) -> None:
    print("\n=== Randomization check (validate script) ===")
    t = merged["treatment"] == 1
    c = merged["treatment"] == 0
    print(f"Treatment share = {merged['treatment'].mean():.4f}")

    print("\nSegment distribution by arm:")
    for seg in EXPECTED_PROPS:
        p_t = float((merged.loc[t, "segment"] == seg).mean())
        p_c = float((merged.loc[c, "segment"] == seg).mean())
        print(f"  {seg:15s}  treated={p_t:.4f}  control={p_c:.4f}  |diff|={abs(p_t - p_c):.4f}")

    numeric = [
        "months_since_account_open",
        "avg_utilization_last_3m",
        "payment_consistency_score",
        "existing_limit",
        "num_active_credit_lines",
    ]
    print("\nNumeric means by arm:")
    for col in numeric:
        m_t = float(merged.loc[t, col].mean())
        m_c = float(merged.loc[c, col].mean())
        sd = float(merged[col].std(ddof=0))
        smd = abs(m_t - m_c) / sd if sd > 0 else abs(m_t - m_c)
        print(
            f"  {col:28s}  T={m_t:.4f}  C={m_c:.4f}  |diff|={abs(m_t - m_c):.4f}  "
            f"SMD={smd:.4f}"
        )

    print("\nCategorical shares by arm:")
    for col in ["channel", "region", "income_band"]:
        series = merged[col].astype("string").fillna("<missing>")
        for level in sorted(series.unique().tolist()):
            p_t = float((series[t] == level).mean())
            p_c = float((series[c] == level).mean())
            print(
                f"  {col}={level:12s}  T={p_t:.4f}  C={p_c:.4f}  "
                f"|diff|={abs(p_t - p_c):.4f}"
            )


def print_segment_effect_check(merged: pd.DataFrame) -> None:
    """Compare mean true_cate vs observed treated-control gap within each segment."""
    print("\n=== Per-segment true_cate vs observed outcome gap ===")
    print(
        f"{'segment':15s}  {'n':>6s}  {'mean_true_cate':>14s}  "
        f"{'obs_gap(T-C)':>12s}  {'mean_baseline':>13s}  "
        f"{'clip_rate':>9s}"
    )
    for seg in EXPECTED_PROPS:
        g = merged[merged["segment"] == seg]
        mean_cate = float(g["true_cate"].mean())
        mean_base = float(g["baseline_prob"].mean())
        t = g[g["treatment"] == 1]
        c = g[g["treatment"] == 0]
        obs_gap = float(t["good_standing"].mean() - c["good_standing"].mean())
        # How often true_prob sat on a clip boundary relative to unclipped
        unclipped = g["baseline_prob"] + g["treatment"] * g["true_cate"]
        clip_rate = float(((unclipped < 0) | (unclipped > 1)).mean())
        print(
            f"{seg:15s}  {len(g):6,}  {mean_cate:14.4f}  {obs_gap:12.4f}  "
            f"{mean_base:13.4f}  {clip_rate:9.4f}"
        )

    print(
        "\nExpectation: Persuadables obs_gap >> 0 and near mean_true_cate; "
        "Sure Things / Lost Causes obs_gap ~ 0; Sleeping Dogs obs_gap << 0."
    )

    # Soft consistency assertions (sampling noise allowed)
    by_seg = {
        seg: merged[merged["segment"] == seg] for seg in EXPECTED_PROPS
    }

    def obs_gap(seg: str) -> float:
        g = by_seg[seg]
        return float(
            g.loc[g["treatment"] == 1, "good_standing"].mean()
            - g.loc[g["treatment"] == 0, "good_standing"].mean()
        )

    checks: list[str] = []
    if obs_gap("Persuadables") < 0.08:
        checks.append(
            f"Persuadables observed gap too small: {obs_gap('Persuadables'):.4f}"
        )
    if abs(obs_gap("Sure Things")) > 0.05:
        checks.append(
            f"Sure Things observed gap not near 0: {obs_gap('Sure Things'):.4f}"
        )
    if abs(obs_gap("Lost Causes")) > 0.05:
        checks.append(
            f"Lost Causes observed gap not near 0: {obs_gap('Lost Causes'):.4f}"
        )
    if obs_gap("Sleeping Dogs") > -0.05:
        checks.append(
            f"Sleeping Dogs observed gap not clearly negative: "
            f"{obs_gap('Sleeping Dogs'):.4f}"
        )

    # Baseline headroom check (option A)
    base = merged["baseline_prob"]
    if float(base.min()) < 0.24 or float(base.max()) > 0.76:
        checks.append(
            f"baseline_prob outside designed ~[0.25, 0.75] band: "
            f"[{base.min():.3f}, {base.max():.3f}]"
        )

    if checks:
        raise AssertionError(
            "Segment effect consistency checks FAILED:\n  - "
            + "\n  - ".join(checks)
        )
    print("\n=== Segment effect consistency checks PASSED ===")


def print_misc(merged: pd.DataFrame) -> None:
    print("\n=== Misc generation diagnostics ===")
    miss = merged["income_band"].isna().mean()
    print(f"income_band missingness = {miss:.4f} (target ~0.05)")
    corr = np.corrcoef(
        merged["months_since_account_open"].to_numpy(dtype=float),
        merged["existing_limit"].to_numpy(dtype=float),
    )[0, 1]
    print(f"corr(months_since_account_open, existing_limit) = {corr:.4f} (expect mild +)")
    print(
        f"baseline_prob range = [{merged['baseline_prob'].min():.3f}, "
        f"{merged['baseline_prob'].max():.3f}]"
    )
    print(
        f"true_cate range = [{merged['true_cate'].min():.3f}, "
        f"{merged['true_cate'].max():.3f}]"
    )
    print(
        f"good_standing rate overall = {merged['good_standing'].mean():.4f} "
        f"| treated = {merged.loc[merged['treatment']==1, 'good_standing'].mean():.4f} "
        f"| control = {merged.loc[merged['treatment']==0, 'good_standing'].mean():.4f}"
    )


def main() -> None:
    _, _, merged = load_tables()
    print_segment_proportions(merged)
    print_randomization_check(merged)
    print_segment_effect_check(merged)
    print_misc(merged)
    print("\nValidation complete.")


if __name__ == "__main__":
    main()
