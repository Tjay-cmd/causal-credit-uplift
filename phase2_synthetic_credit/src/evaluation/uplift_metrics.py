"""Uplift evaluation metrics for Phase 2 (Qini + uplift-at-k from definition)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

_SRC_DIR = Path(__file__).resolve().parent.parent
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from data_prep import PROJECT_ROOT

QINI_PLOT_PATH: Path = PROJECT_ROOT / "outputs" / "qini_curve.png"


def _sorted_by_cate(
    y_true: np.ndarray,
    treatment: np.ndarray,
    cate: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    order = np.argsort(-cate)
    return y_true[order], treatment[order], cate[order]


def qini_curve(
    y_true: np.ndarray | pd.Series,
    treatment: np.ndarray | pd.Series,
    cate: np.ndarray | pd.Series,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Radcliffe-style Qini curve from first principles (same definition as Phase 1)."""
    y = np.asarray(y_true, dtype=float)
    t = np.asarray(treatment, dtype=float)
    c = np.asarray(cate, dtype=float)
    if not (len(y) == len(t) == len(c)):
        raise ValueError("y_true, treatment, and cate must have the same length.")

    y, t, _ = _sorted_by_cate(y, t, c)
    n = len(y)
    is_t = t == 1
    is_c = t == 0
    cum_n_t = np.concatenate([[0], np.cumsum(is_t)])
    cum_n_c = np.concatenate([[0], np.cumsum(is_c)])
    cum_y_t = np.concatenate([[0.0], np.cumsum(y * is_t)])
    cum_y_c = np.concatenate([[0.0], np.cumsum(y * is_c)])

    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where(cum_n_c > 0, cum_n_t / cum_n_c, 0.0)
        qini = cum_y_t - cum_y_c * ratio

    fractions = np.arange(n + 1) / n
    random_line = fractions * qini[-1]
    return fractions, qini, random_line


def qini_coefficient(
    y_true: np.ndarray | pd.Series,
    treatment: np.ndarray | pd.Series,
    cate: np.ndarray | pd.Series,
) -> float:
    fractions, qini, random_line = qini_curve(y_true, treatment, cate)
    return float(np.trapezoid(qini - random_line, fractions))


def uplift_at_k(
    y_true: np.ndarray | pd.Series,
    treatment: np.ndarray | pd.Series,
    cate: np.ndarray | pd.Series,
    k: float = 0.3,
) -> float:
    if not 0 < k <= 1:
        raise ValueError(f"k must be in (0, 1], got {k}")
    y = np.asarray(y_true, dtype=float)
    t = np.asarray(treatment, dtype=float)
    c = np.asarray(cate, dtype=float)
    y, t, _ = _sorted_by_cate(y, t, c)
    n_top = max(1, int(np.ceil(k * len(y))))
    top_y, top_t = y[:n_top], t[:n_top]
    treated_mask = top_t == 1
    control_mask = top_t == 0
    if treated_mask.sum() == 0 or control_mask.sum() == 0:
        raise ValueError(f"Top {k:.0%} slice missing treated or control units.")
    return float(top_y[treated_mask].mean() - top_y[control_mask].mean())


def evaluate_predictions(
    preds: pd.DataFrame,
    model_name: str,
    ks: Iterable[float] = (0.1, 0.3, 0.5),
) -> dict[str, float | str]:
    required = {"true_outcome", "true_treatment", "predicted_cate"}
    missing = required - set(preds.columns)
    if missing:
        raise ValueError(f"{model_name}: missing columns {missing}")

    metrics: dict[str, float | str] = {
        "model": model_name,
        "qini_coefficient": qini_coefficient(
            preds["true_outcome"], preds["true_treatment"], preds["predicted_cate"]
        ),
    }
    for k in ks:
        metrics[f"uplift_at_{int(k * 100)}pct"] = uplift_at_k(
            preds["true_outcome"],
            preds["true_treatment"],
            preds["predicted_cate"],
            k=k,
        )
    return metrics


def plot_qini_curves(
    model_preds: dict[str, pd.DataFrame],
    output_path: Path = QINI_PLOT_PATH,
) -> Path:
    if not model_preds:
        raise ValueError("model_preds is empty.")

    fig, ax = plt.subplots(figsize=(8, 5))
    for name, preds in model_preds.items():
        fractions, qini, random_line = qini_curve(
            preds["true_outcome"],
            preds["true_treatment"],
            preds["predicted_cate"],
        )
        ax.plot(fractions, qini, label=f"{name} (Qini)")
        ax.plot(fractions, random_line, linestyle="--", linewidth=1, label=f"{name} random")

    ax.set_xlabel("Fraction of population targeted (ranked by predicted CATE)")
    ax.set_ylabel("Incremental good_standing outcomes (Qini)")
    ax.set_title("Qini curves - Phase 2 synthetic credit-limit RCT")
    ax.legend(loc="best", fontsize=8)
    ax.grid(True, alpha=0.3)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    print(f"Saved Qini plot to {output_path}")
    return output_path


def print_summary_table(metrics_list: list[dict[str, float | str]]) -> pd.DataFrame:
    df = pd.DataFrame(metrics_list)
    cols = ["model", "qini_coefficient"] + [
        c for c in df.columns if c.startswith("uplift_at_")
    ]
    df = df[cols]
    print("\n=== Uplift Metrics Summary ===")
    print(df.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
    print("=== End Summary ===\n")
    return df


def run_evaluation(
    t_learner_path: Path | None = None,
    causal_forest_path: Path | None = None,
    plot_path: Path = QINI_PLOT_PATH,
) -> pd.DataFrame:
    t_path = t_learner_path or (PROJECT_ROOT / "outputs" / "t_learner_predictions.csv")
    cf_path = causal_forest_path or (
        PROJECT_ROOT / "outputs" / "causal_forest_predictions.csv"
    )

    model_preds: dict[str, pd.DataFrame] = {}
    metrics_list: list[dict[str, float | str]] = []

    if t_path.exists():
        t_preds = pd.read_csv(t_path)
        model_preds["T-learner"] = t_preds
        metrics_list.append(evaluate_predictions(t_preds, "T-learner"))
    else:
        print(f"WARNING: missing {t_path}")

    if cf_path.exists():
        cf_preds = pd.read_csv(cf_path)
        model_preds["CausalForestDML"] = cf_preds
        metrics_list.append(evaluate_predictions(cf_preds, "CausalForestDML"))
    else:
        print(f"WARNING: missing {cf_path}")

    if not metrics_list:
        raise FileNotFoundError("No prediction files found under outputs/.")

    plot_qini_curves(model_preds, output_path=plot_path)
    return print_summary_table(metrics_list)


if __name__ == "__main__":
    run_evaluation()
