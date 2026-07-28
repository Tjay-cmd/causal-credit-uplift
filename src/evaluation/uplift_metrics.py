"""Uplift evaluation metrics: Qini curve/coefficient and uplift-at-k.

These are implemented from definition (not from a library wrapper) so the
mechanics are inspectable for portfolio / learning purposes.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Flat src/ layout: allow `from data_prep import ...` when run as a script
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
    """Sort samples by predicted CATE descending (highest uplift first)."""
    order = np.argsort(-cate)
    return y_true[order], treatment[order], cate[order]


def qini_curve(
    y_true: np.ndarray | pd.Series,
    treatment: np.ndarray | pd.Series,
    cate: np.ndarray | pd.Series,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute the Qini (incremental gains) curve from first principles.

    Definition used here (binary treatment, binary outcome):
    Rank customers by predicted CATE descending. At population fraction x
    (top x% of the ranked list), the incremental gain is:

        Q(x) = n_t(x) * (ȳ_t(x) - ȳ_c(x))

    where n_t(x) is the number of treated units in the top x%, and
    ȳ_t / ȳ_c are mean outcomes among treated / control in that slice.

    Equivalently (Radcliffe-style cumulative form used in practice):

        Q(k) = Y_t(k) - Y_c(k) * (N_t(k) / N_c(k))

    where Y_t(k), Y_c(k) are cumulative sums of outcomes among treated and
    control in the top k ranked customers, and N_t(k), N_c(k) are counts.

    The random-targeting baseline is the straight line from (0, 0) to
    (1, Q(1)) = overall ATE * n_treated (same endpoint as the model when
    the full population is targeted).

    Returns
    -------
    fractions : array shape (n+1,)
        Population fraction targeted, from 0 to 1.
    qini : array shape (n+1,)
        Model Qini values at each fraction.
    random_line : array shape (n+1,)
        Random-targeting baseline at the same fractions.
    """
    y = np.asarray(y_true, dtype=float)
    t = np.asarray(treatment, dtype=float)
    c = np.asarray(cate, dtype=float)
    if not (len(y) == len(t) == len(c)):
        raise ValueError("y_true, treatment, and cate must have the same length.")

    y, t, _ = _sorted_by_cate(y, t, c)
    n = len(y)

    # Cumulative treated/control counts and outcome sums along the ranked list
    is_t = t == 1
    is_c = t == 0
    cum_n_t = np.concatenate([[0], np.cumsum(is_t)])
    cum_n_c = np.concatenate([[0], np.cumsum(is_c)])
    cum_y_t = np.concatenate([[0.0], np.cumsum(y * is_t)])
    cum_y_c = np.concatenate([[0.0], np.cumsum(y * is_c)])

    # Avoid division by zero early in the curve when no controls yet
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where(cum_n_c > 0, cum_n_t / cum_n_c, 0.0)
        qini = cum_y_t - cum_y_c * ratio

    fractions = np.arange(n + 1) / n
    # Random line: linear from 0 to overall Qini at 100% (perfectly mixed targeting)
    random_line = fractions * qini[-1]
    return fractions, qini, random_line


def qini_coefficient(
    y_true: np.ndarray | pd.Series,
    treatment: np.ndarray | pd.Series,
    cate: np.ndarray | pd.Series,
) -> float:
    """Qini coefficient = area between model Qini curve and random line.

    Computed with the trapezoid rule on the population-fraction axis.
    Positive values mean the model beats random targeting.
    """
    fractions, qini, random_line = qini_curve(y_true, treatment, cate)
    # Area between curves (model - random). Normalize by n so the metric
    # is comparable across sample sizes: ∫(Q_model - Q_random) dx over [0,1].
    area = float(np.trapezoid(qini - random_line, fractions))
    return area


def uplift_at_k(
    y_true: np.ndarray | pd.Series,
    treatment: np.ndarray | pd.Series,
    cate: np.ndarray | pd.Series,
    k: float = 0.3,
) -> float:
    """Uplift among the top k fraction ranked by predicted CATE.

    uplift@k = mean(y | treated, top-k) - mean(y | control, top-k)

    Parameters
    ----------
    k :
        Fraction in (0, 1], e.g. 0.3 for uplift-at-30%.
    """
    if not 0 < k <= 1:
        raise ValueError(f"k must be in (0, 1], got {k}")

    y = np.asarray(y_true, dtype=float)
    t = np.asarray(treatment, dtype=float)
    c = np.asarray(cate, dtype=float)
    y, t, _ = _sorted_by_cate(y, t, c)

    n_top = max(1, int(np.ceil(k * len(y))))
    top_y = y[:n_top]
    top_t = t[:n_top]

    treated_mask = top_t == 1
    control_mask = top_t == 0
    if treated_mask.sum() == 0 or control_mask.sum() == 0:
        raise ValueError(
            f"Top {k:.0%} slice has no treated or no control units; "
            "cannot compute uplift-at-k."
        )
    return float(top_y[treated_mask].mean() - top_y[control_mask].mean())


def evaluate_predictions(
    preds: pd.DataFrame,
    model_name: str,
    ks: Iterable[float] = (0.1, 0.3, 0.5),
) -> dict[str, float | str]:
    """Compute Qini coefficient and uplift-at-k metrics for one model."""
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
        key = f"uplift_at_{int(k * 100)}pct"
        metrics[key] = uplift_at_k(
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
    """Plot Qini curves for multiple models on one chart and save PNG."""
    if not model_preds:
        raise ValueError("model_preds is empty.")

    fig, ax = plt.subplots(figsize=(8, 5))
    # Use the first model's random line endpoint as shared visual reference;
    # each model still has its own curve (endpoints may differ slightly by score ties).
    for name, preds in model_preds.items():
        fractions, qini, random_line = qini_curve(
            preds["true_outcome"],
            preds["true_treatment"],
            preds["predicted_cate"],
        )
        ax.plot(fractions, qini, label=f"{name} (Qini)")
        ax.plot(
            fractions,
            random_line,
            linestyle="--",
            linewidth=1,
            label=f"{name} random",
        )

    ax.set_xlabel("Fraction of population targeted (ranked by predicted CATE)")
    ax.set_ylabel("Incremental purchases (Qini)")
    ax.set_title("Qini curves — Hillstrom Mens E-Mail vs No E-Mail (visit)")
    ax.legend(loc="best", fontsize=8)
    ax.grid(True, alpha=0.3)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    print(f"Saved Qini plot to {output_path}")
    return output_path


def print_summary_table(metrics_list: list[dict[str, float | str]]) -> pd.DataFrame:
    """Print and return a comparison table of uplift metrics."""
    df = pd.DataFrame(metrics_list)
    # nicer column order
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
    """Load prediction CSVs, compute metrics, plot Qini, print summary."""
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
