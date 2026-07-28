"""Phase 2 synthetic credit-limit RCT data generator.

Generates a randomized experiment with known latent segments and true CATE,
saved separately from the modeling table so ground truth cannot leak into
training.
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd

RANDOM_SEED: int = 42
N_CUSTOMERS: int = 40_000

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
DATA_DIR: Path = PROJECT_ROOT / "data"

SEGMENT_PROPS: dict[str, float] = {
    "Persuadables": 0.20,
    "Sure Things": 0.30,
    "Lost Causes": 0.25,
    "Sleeping Dogs": 0.25,
}

# Randomization balance thresholds (RCT proof)
MAX_MEAN_DIFF_NUMERIC: float = 0.05  # absolute gap in means (scaled features ~0-1 or similar)
MAX_PROP_DIFF_CATEGORICAL: float = 0.03  # max absolute gap in category share
MAX_SEGMENT_SHARE_DIFF: float = 0.02


def _rng(seed: int = RANDOM_SEED) -> np.random.Generator:
    return np.random.default_rng(seed)


def _clip(x: np.ndarray, lo: float, hi: float) -> np.ndarray:
    return np.clip(x, lo, hi)


def _sample_truncated_normal(
    rng: np.random.Generator,
    n: int,
    mean: float,
    std: float,
    lo: float,
    hi: float,
) -> np.ndarray:
    """Sample normals then clip — simple overlap-friendly truncated draws."""
    return _clip(rng.normal(mean, std, size=n), lo, hi)


def _weighted_choice(
    rng: np.random.Generator,
    n: int,
    categories: list[str],
    weights: list[float],
) -> np.ndarray:
    w = np.asarray(weights, dtype=float)
    w = w / w.sum()
    return rng.choice(categories, size=n, p=w)


def assign_segments(n: int, rng: np.random.Generator) -> np.ndarray:
    """Assign latent segments by target proportions (answer key only)."""
    names = list(SEGMENT_PROPS.keys())
    props = np.array([SEGMENT_PROPS[k] for k in names], dtype=float)
    props = props / props.sum()
    counts = rng.multinomial(n, props)
    segments = np.concatenate(
        [np.full(c, name, dtype=object) for name, c in zip(names, counts)]
    )
    rng.shuffle(segments)
    return segments


def generate_covariates_for_segment(
    segment: str,
    n: int,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Draw covariates from segment-specific distributions with intentional overlap."""
    if segment == "Persuadables":
        util = _sample_truncated_normal(rng, n, mean=0.55, std=0.10, lo=0.25, hi=0.85)
        pay = _sample_truncated_normal(rng, n, mean=0.62, std=0.08, lo=0.35, hi=0.90)
        lines = rng.integers(2, 6, size=n)  # 2-5
        channel = _weighted_choice(
            rng, n, ["App", "Branch", "CallCenter"], [0.55, 0.30, 0.15]
        )
        region = _weighted_choice(
            rng, n, ["Urban", "Suburban", "Rural"], [0.55, 0.30, 0.15]
        )
        months = rng.integers(12, 96, size=n)
        income = _weighted_choice(
            rng, n, ["Low", "Medium", "High", "Very High"], [0.15, 0.40, 0.30, 0.15]
        )
    elif segment == "Sure Things":
        util = _sample_truncated_normal(rng, n, mean=0.20, std=0.07, lo=0.02, hi=0.45)
        pay = _sample_truncated_normal(rng, n, mean=0.88, std=0.05, lo=0.70, hi=0.99)
        lines = rng.integers(1, 5, size=n)  # 1-4
        channel = _weighted_choice(
            rng, n, ["App", "Branch", "CallCenter"], [0.40, 0.40, 0.20]
        )
        region = _weighted_choice(
            rng, n, ["Urban", "Suburban", "Rural"], [0.40, 0.40, 0.20]
        )
        months = rng.integers(24, 121, size=n)
        income = _weighted_choice(
            rng, n, ["Low", "Medium", "High", "Very High"], [0.10, 0.30, 0.35, 0.25]
        )
    elif segment == "Lost Causes":
        util = _sample_truncated_normal(rng, n, mean=0.85, std=0.07, lo=0.60, hi=0.99)
        pay = _sample_truncated_normal(rng, n, mean=0.28, std=0.08, lo=0.05, hi=0.50)
        lines = rng.integers(2, 7, size=n)
        channel = _weighted_choice(
            rng, n, ["App", "Branch", "CallCenter"], [0.30, 0.35, 0.35]
        )
        region = _weighted_choice(
            rng, n, ["Urban", "Suburban", "Rural"], [0.35, 0.35, 0.30]
        )
        months = rng.integers(1, 60, size=n)
        income = _weighted_choice(
            rng, n, ["Low", "Medium", "High", "Very High"], [0.40, 0.35, 0.20, 0.05]
        )
    elif segment == "Sleeping Dogs":
        # Decent payers saturated on contact/channel (Phase 1 closing-note analogue)
        util = _sample_truncated_normal(rng, n, mean=0.85, std=0.07, lo=0.60, hi=0.99)
        pay = _sample_truncated_normal(rng, n, mean=0.70, std=0.08, lo=0.50, hi=0.92)
        lines = rng.integers(5, 9, size=n)  # 5-8
        channel = _weighted_choice(
            rng, n, ["App", "Branch", "CallCenter"], [0.15, 0.25, 0.60]
        )
        region = _weighted_choice(
            rng, n, ["Urban", "Suburban", "Rural"], [0.15, 0.30, 0.55]
        )
        months = rng.integers(18, 121, size=n)
        income = _weighted_choice(
            rng, n, ["Low", "Medium", "High", "Very High"], [0.20, 0.40, 0.30, 0.10]
        )
    else:
        raise ValueError(f"Unknown segment: {segment!r}")

    # Mild correlation: older accounts → higher limits, plus noise
    # Base limit around 1k-50k, shifted by tenure
    tenure_factor = (months.astype(float) / 120.0) * 25_000.0
    base_limit = rng.uniform(1_000.0, 25_000.0, size=n)
    existing_limit = _clip(base_limit + tenure_factor + rng.normal(0, 4_000, size=n), 1_000, 50_000)

    return pd.DataFrame(
        {
            "months_since_account_open": months.astype(int),
            "avg_utilization_last_3m": util.astype(float),
            "payment_consistency_score": pay.astype(float),
            "income_band": income,
            "existing_limit": existing_limit.astype(float),
            "num_active_credit_lines": lines.astype(int),
            "channel": channel,
            "region": region,
        }
    )


def generate_all_covariates(
    segments: np.ndarray,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Generate covariates per segment, then restore original row order."""
    frames: list[pd.DataFrame] = []
    for seg in SEGMENT_PROPS:
        idx = np.where(segments == seg)[0]
        if len(idx) == 0:
            continue
        chunk = generate_covariates_for_segment(seg, len(idx), rng)
        chunk.insert(0, "_orig_idx", idx)
        frames.append(chunk)

    combined = pd.concat(frames, axis=0, ignore_index=True)
    combined = combined.sort_values("_orig_idx").drop(columns=["_orig_idx"]).reset_index(drop=True)
    return combined


def apply_income_missingness(
    df: pd.DataFrame,
    rng: np.random.Generator,
    rate: float = 0.05,
) -> pd.DataFrame:
    """Set ~5% of income_band to missing (covariate messiness only)."""
    out = df.copy()
    mask = rng.random(len(out)) < rate
    out.loc[mask, "income_band"] = pd.NA
    return out


def assign_treatment(n: int, rng: np.random.Generator) -> np.ndarray:
    """Fully independent Bernoulli(0.5) treatment — no dependence on X or segment."""
    return rng.binomial(1, 0.5, size=n).astype(int)


def compute_baseline_prob(
    payment_consistency: np.ndarray,
    utilization: np.ndarray,
) -> np.ndarray:
    """Baseline P(good_standing | T=0) from payment quality and utilization.

    Designed (option A) so typical values land roughly in [0.25, 0.75], leaving
    headroom for Persuadable (+0.15..0.20) and Sleeping Dog (-0.10..-0.15) CATEs
    without heavy clipping.
    """
    # Linear map: high pay / low util → higher baseline
    raw = 0.30 + 0.40 * payment_consistency - 0.30 * utilization
    # Small smooth noise-free deterministic function (noise enters via CATE / outcome draw)
    return _clip(raw, 0.25, 0.75)


def sample_true_cate(segments: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Per-customer true CATE from segment-specific ranges (answer key)."""
    cate = np.empty(len(segments), dtype=float)
    for seg in SEGMENT_PROPS:
        mask = segments == seg
        k = int(mask.sum())
        if k == 0:
            continue
        if seg == "Persuadables":
            cate[mask] = rng.uniform(0.15, 0.20, size=k)
        elif seg in ("Sure Things", "Lost Causes"):
            cate[mask] = rng.uniform(-0.02, 0.02, size=k)
        elif seg == "Sleeping Dogs":
            cate[mask] = rng.uniform(-0.15, -0.10, size=k)
        else:
            raise ValueError(f"Unknown segment: {seg!r}")
    return cate


def generate_outcomes(
    baseline_prob: np.ndarray,
    true_cate: np.ndarray,
    treatment: np.ndarray,
    rng: np.random.Generator,
) -> Tuple[np.ndarray, np.ndarray]:
    """Return (true_prob, good_standing)."""
    true_prob = _clip(
        baseline_prob + treatment.astype(float) * true_cate,
        0.0,
        1.0,
    )
    good_standing = rng.binomial(1, true_prob).astype(int)
    return true_prob, good_standing


def _assert_randomization(
    df: pd.DataFrame,
    segments: np.ndarray,
    treatment: np.ndarray,
) -> None:
    """Fail loudly if treated vs control look unbalanced (RCT broken)."""
    treated = treatment == 1
    control = treatment == 0
    if treated.sum() == 0 or control.sum() == 0:
        raise AssertionError("Treatment assignment produced an empty arm.")

    print("\n=== Randomization check (treated vs control) ===")
    treat_rate = float(treatment.mean())
    print(f"Treatment share = {treat_rate:.4f} (expect ~0.50)")

    # Segment distribution
    print("\nSegment share by arm:")
    failures: list[str] = []
    for seg in SEGMENT_PROPS:
        p_t = float((segments[treated] == seg).mean())
        p_c = float((segments[control] == seg).mean())
        diff = abs(p_t - p_c)
        print(f"  {seg:15s}  treated={p_t:.4f}  control={p_c:.4f}  |diff|={diff:.4f}")
        if diff > MAX_SEGMENT_SHARE_DIFF:
            failures.append(
                f"Segment {seg!r} share gap {diff:.4f} > {MAX_SEGMENT_SHARE_DIFF}"
            )

    numeric_cols = [
        "months_since_account_open",
        "avg_utilization_last_3m",
        "payment_consistency_score",
        "existing_limit",
        "num_active_credit_lines",
    ]
    print("\nNumeric covariate means by arm:")
    # Scale-aware thresholds: for large-scale features use relative/absolute hybrid
    for col in numeric_cols:
        m_t = float(df.loc[treated, col].mean())
        m_c = float(df.loc[control, col].mean())
        diff = abs(m_t - m_c)
        # Normalize by pooled std for a scale-free check
        pooled_std = float(df[col].std(ddof=0))
        std_diff = diff / pooled_std if pooled_std > 0 else diff
        print(
            f"  {col:28s}  treated={m_t:.4f}  control={m_c:.4f}  "
            f"|diff|={diff:.4f}  |std|/sd={std_diff:.4f}"
        )
        # SMD > 0.10 is a common imbalance flag; use 0.08 as a tight RCT proof
        if std_diff > 0.08:
            failures.append(
                f"Covariate {col!r} standardized mean diff {std_diff:.4f} > 0.08"
            )

    print("\nCategorical distributions by arm:")
    for col in ["channel", "region", "income_band"]:
        # income_band may contain NA — treat as its own level for balance check
        series = df[col].astype("string").fillna("<missing>")
        levels = sorted(series.unique().tolist())
        for level in levels:
            p_t = float((series[treated] == level).mean())
            p_c = float((series[control] == level).mean())
            diff = abs(p_t - p_c)
            if diff > MAX_PROP_DIFF_CATEGORICAL:
                failures.append(
                    f"{col}={level!r} share gap {diff:.4f} > {MAX_PROP_DIFF_CATEGORICAL}"
                )
            print(
                f"  {col}={level:12s}  treated={p_t:.4f}  control={p_c:.4f}  "
                f"|diff|={diff:.4f}"
            )

    if failures:
        msg = "Randomization check FAILED:\n  - " + "\n  - ".join(failures)
        raise AssertionError(msg)
    print("=== Randomization check PASSED ===\n")


def build_dataset(
    n: int = N_CUSTOMERS,
    seed: int = RANDOM_SEED,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Generate modeling table + ground-truth table."""
    rng = _rng(seed)

    segments = assign_segments(n, rng)
    covariates = generate_all_covariates(segments, rng)
    covariates = apply_income_missingness(covariates, rng, rate=0.05)

    treatment = assign_treatment(n, rng)
    _assert_randomization(covariates, segments, treatment)

    baseline_prob = compute_baseline_prob(
        covariates["payment_consistency_score"].to_numpy(dtype=float),
        covariates["avg_utilization_last_3m"].to_numpy(dtype=float),
    )
    true_cate = sample_true_cate(segments, rng)
    true_prob, good_standing = generate_outcomes(
        baseline_prob, true_cate, treatment, rng
    )

    customer_id = np.arange(n, dtype=int)

    full = covariates.copy()
    full.insert(0, "customer_id", customer_id)
    full["treatment"] = treatment
    full["good_standing"] = good_standing
    # Explicitly ensure no ground-truth leakage columns
    leak_cols = {"segment", "true_cate", "baseline_prob", "true_prob"}
    assert leak_cols.isdisjoint(full.columns), "Ground truth leaked into modeling table."

    ground_truth = pd.DataFrame(
        {
            "customer_id": customer_id,
            "segment": segments,
            "true_cate": true_cate,
            "baseline_prob": baseline_prob,
            "true_prob": true_prob,
        }
    )
    return full, ground_truth


def save_dataset(
    full: pd.DataFrame,
    ground_truth: pd.DataFrame,
    data_dir: Path = DATA_DIR,
) -> Tuple[Path, Path]:
    """Write parquet outputs under phase2_synthetic_credit/data/."""
    data_dir.mkdir(parents=True, exist_ok=True)
    full_path = data_dir / "synthetic_credit_full.parquet"
    gt_path = data_dir / "synthetic_credit_ground_truth.parquet"
    full.to_parquet(full_path, index=False)
    ground_truth.to_parquet(gt_path, index=False)
    print(f"Wrote {full_path} ({len(full):,} rows, cols={list(full.columns)})")
    print(f"Wrote {gt_path} ({len(ground_truth):,} rows, cols={list(ground_truth.columns)})")
    return full_path, gt_path


def main() -> None:
    full, ground_truth = build_dataset()
    save_dataset(full, ground_truth)


if __name__ == "__main__":
    main()
