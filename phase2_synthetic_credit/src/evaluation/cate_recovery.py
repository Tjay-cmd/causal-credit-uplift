"""CATE recovery evaluation for Phase 2 (uses ground truth ONLY here).

Metrics
-------
- PEHE = mean( (predicted_cate - true_cate)^2 )
- Per-segment: mean predicted CATE vs mean true CATE

Ground-truth file is joined on customer_id at evaluation time only.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_SRC_DIR = Path(__file__).resolve().parent.parent
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from data_prep import PROJECT_ROOT

GT_PATH: Path = PROJECT_ROOT / "data" / "synthetic_credit_ground_truth.parquet"
SUMMARY_CSV: Path = PROJECT_ROOT / "outputs" / "cate_recovery_summary.csv"

SEGMENT_ORDER: list[str] = [
    "Persuadables",
    "Sure Things",
    "Lost Causes",
    "Sleeping Dogs",
]


def pehe(predicted_cate: np.ndarray | pd.Series, true_cate: np.ndarray | pd.Series) -> float:
    """Precision in Estimating Heterogeneous Effects: MSE of CATE estimates."""
    pred = np.asarray(predicted_cate, dtype=float)
    truth = np.asarray(true_cate, dtype=float)
    if len(pred) != len(truth):
        raise ValueError("predicted_cate and true_cate length mismatch.")
    return float(np.mean((pred - truth) ** 2))


def load_ground_truth(gt_path: Path = GT_PATH) -> pd.DataFrame:
    if not gt_path.exists():
        raise FileNotFoundError(f"Missing ground truth: {gt_path}")
    gt = pd.read_parquet(gt_path)
    required = {"customer_id", "segment", "true_cate"}
    missing = required - set(gt.columns)
    if missing:
        raise ValueError(f"Ground truth missing columns: {missing}")
    return gt


def join_preds_with_truth(
    preds: pd.DataFrame,
    gt: pd.DataFrame,
    model_name: str,
) -> pd.DataFrame:
    if "predicted_cate" not in preds.columns or "customer_id" not in preds.columns:
        raise ValueError(f"{model_name}: predictions need customer_id and predicted_cate.")
    merged = preds.merge(
        gt[["customer_id", "segment", "true_cate"]],
        on="customer_id",
        how="inner",
        validate="one_to_one",
    )
    if len(merged) != len(preds):
        raise ValueError(
            f"{model_name}: ground-truth join dropped rows "
            f"(preds={len(preds)}, merged={len(merged)})."
        )
    return merged


def per_segment_cate_comparison(merged: pd.DataFrame, model_name: str) -> pd.DataFrame:
    rows: list[dict[str, float | str | int]] = []
    for seg in SEGMENT_ORDER:
        g = merged[merged["segment"] == seg]
        if g.empty:
            continue
        mean_pred = float(g["predicted_cate"].mean())
        mean_true = float(g["true_cate"].mean())
        rows.append(
            {
                "model": model_name,
                "segment": seg,
                "n": int(len(g)),
                "mean_predicted_cate": mean_pred,
                "mean_true_cate": mean_true,
                "bias": mean_pred - mean_true,
                "segment_pehe": pehe(g["predicted_cate"], g["true_cate"]),
            }
        )
    return pd.DataFrame(rows)


def evaluate_model(
    preds: pd.DataFrame,
    gt: pd.DataFrame,
    model_name: str,
) -> tuple[dict[str, float | str], pd.DataFrame]:
    merged = join_preds_with_truth(preds, gt, model_name)
    overall = {
        "model": model_name,
        "n": float(len(merged)),
        "pehe": pehe(merged["predicted_cate"], merged["true_cate"]),
        "corr_pred_true_cate": float(
            np.corrcoef(merged["predicted_cate"], merged["true_cate"])[0, 1]
        ),
        "mean_predicted_cate": float(merged["predicted_cate"].mean()),
        "mean_true_cate": float(merged["true_cate"].mean()),
    }
    by_seg = per_segment_cate_comparison(merged, model_name)
    return overall, by_seg


def print_recovery_report(
    overall_rows: list[dict[str, float | str]],
    segment_df: pd.DataFrame,
) -> None:
    print("\n=== CATE Recovery (PEHE) ===")
    overall_df = pd.DataFrame(overall_rows)
    print(
        overall_df.to_string(
            index=False,
            float_format=lambda x: f"{x:.4f}",
        )
    )
    print("\n=== Per-segment mean predicted CATE vs mean true CATE ===")
    print(
        segment_df.to_string(
            index=False,
            float_format=lambda x: f"{x:.4f}",
        )
    )
    print(
        "\nExpectation: Persuadables mean_pred >> 0 and near ~0.15-0.20; "
        "Sure Things / Lost Causes near 0; Sleeping Dogs mean_pred << 0 near ~-0.10--0.15."
    )


def run_cate_recovery(
    t_learner_path: Path | None = None,
    causal_forest_path: Path | None = None,
    gt_path: Path = GT_PATH,
    summary_csv: Path = SUMMARY_CSV,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Evaluate saved predictions against held-out ground truth."""
    t_path = t_learner_path or (PROJECT_ROOT / "outputs" / "t_learner_predictions.csv")
    cf_path = causal_forest_path or (
        PROJECT_ROOT / "outputs" / "causal_forest_predictions.csv"
    )
    gt = load_ground_truth(gt_path)

    overall_rows: list[dict[str, float | str]] = []
    seg_frames: list[pd.DataFrame] = []

    if t_path.exists():
        overall, by_seg = evaluate_model(pd.read_csv(t_path), gt, "T-learner")
        overall_rows.append(overall)
        seg_frames.append(by_seg)
    else:
        print(f"WARNING: missing {t_path}")

    if cf_path.exists():
        overall, by_seg = evaluate_model(pd.read_csv(cf_path), gt, "CausalForestDML")
        overall_rows.append(overall)
        seg_frames.append(by_seg)
    else:
        print(f"WARNING: missing {cf_path}")

    if not overall_rows:
        raise FileNotFoundError("No prediction files found under outputs/.")

    overall_df = pd.DataFrame(overall_rows)
    segment_df = pd.concat(seg_frames, ignore_index=True)
    print_recovery_report(overall_rows, segment_df)

    # One combined CSV: overall rows tagged + segment rows
    overall_export = overall_df.copy()
    overall_export.insert(1, "row_type", "overall")
    overall_export["segment"] = "ALL"
    seg_export = segment_df.copy()
    seg_export.insert(1, "row_type", "per_segment")
    # Align columns for concat
    combined = pd.concat([overall_export, seg_export], ignore_index=True, sort=False)
    summary_csv.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(summary_csv, index=False)
    print(f"\nWrote {summary_csv}")
    return overall_df, segment_df


if __name__ == "__main__":
    run_cate_recovery()
