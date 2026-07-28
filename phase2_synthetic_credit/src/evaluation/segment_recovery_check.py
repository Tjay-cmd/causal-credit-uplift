"""Operational segment recovery check for Phase 2.

Answers: if we target the top decile by predicted CATE, what TRUE segments
do we actually reach? Ground truth is joined ONLY here for reporting.
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
T_PREDS: Path = PROJECT_ROOT / "outputs" / "t_learner_predictions.csv"
CF_PREDS: Path = PROJECT_ROOT / "outputs" / "causal_forest_predictions.csv"
SUMMARY_CSV: Path = PROJECT_ROOT / "outputs" / "segment_recovery_summary.csv"

SEGMENT_ORDER: list[str] = [
    "Persuadables",
    "Sure Things",
    "Lost Causes",
    "Sleeping Dogs",
]
DECILE: float = 0.10


def load_preds(path: Path, model_name: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path} for {model_name}. Run the model script first "
            "(do not retrain from this module)."
        )
    preds = pd.read_csv(path)
    required = {"customer_id", "predicted_cate"}
    missing = required - set(preds.columns)
    if missing:
        raise ValueError(f"{model_name}: missing columns {missing}")
    return preds


def load_ground_truth(gt_path: Path = GT_PATH) -> pd.DataFrame:
    if not gt_path.exists():
        raise FileNotFoundError(f"Missing ground truth: {gt_path}")
    gt = pd.read_parquet(gt_path)
    required = {"customer_id", "segment"}
    missing = required - set(gt.columns)
    if missing:
        raise ValueError(f"Ground truth missing columns: {missing}")
    return gt[["customer_id", "segment"]].copy()


def assign_deciles(preds: pd.DataFrame, decile: float = DECILE) -> pd.DataFrame:
    """Tag top/bottom decile by predicted CATE (descending rank)."""
    if not 0 < decile < 0.5:
        raise ValueError(f"decile must be in (0, 0.5), got {decile}")
    out = preds.sort_values("predicted_cate", ascending=False).reset_index(drop=True)
    n = len(out)
    n_slice = max(1, int(np.floor(decile * n)))
    out["predicted_decile"] = "middle"
    out.loc[: n_slice - 1, "predicted_decile"] = "top"
    out.loc[out.index[-n_slice:], "predicted_decile"] = "bottom"
    return out


def population_segment_shares(gt: pd.DataFrame) -> pd.Series:
    return gt["segment"].value_counts(normalize=True).reindex(SEGMENT_ORDER).fillna(0.0)


def confusion_for_model(
    model_name: str,
    preds: pd.DataFrame,
    gt: pd.DataFrame,
    pop_shares: pd.Series,
    decile: float = DECILE,
) -> tuple[pd.DataFrame, dict[str, float | str]]:
    """Build predicted-decile x true-segment table + operational summary."""
    scored = assign_deciles(preds, decile=decile)
    merged = scored.merge(gt, on="customer_id", how="inner", validate="one_to_one")
    if len(merged) != len(preds):
        raise ValueError(
            f"{model_name}: ground-truth join dropped rows "
            f"(preds={len(preds)}, merged={len(merged)})."
        )

    rows: list[dict[str, float | str | int]] = []
    for dec in ("top", "bottom"):
        g = merged[merged["predicted_decile"] == dec]
        n_dec = len(g)
        counts = g["segment"].value_counts().reindex(SEGMENT_ORDER).fillna(0).astype(int)
        for seg in SEGMENT_ORDER:
            cnt = int(counts[seg])
            pct = cnt / n_dec if n_dec else float("nan")
            pop = float(pop_shares.get(seg, 0.0))
            enrichment = (pct / pop) if pop > 0 else float("nan")
            rows.append(
                {
                    "model": model_name,
                    "predicted_decile": dec,
                    "true_segment": seg,
                    "n": cnt,
                    "pct_of_decile": pct,
                    "pop_share": pop,
                    "enrichment": enrichment,
                    "decile_n": n_dec,
                }
            )

    table = pd.DataFrame(rows)

    top = merged[merged["predicted_decile"] == "top"]
    top_n = len(top)
    top_pers = float((top["segment"] == "Persuadables").mean()) if top_n else float("nan")
    top_dogs = float((top["segment"] == "Sleeping Dogs").mean()) if top_n else float("nan")
    bottom = merged[merged["predicted_decile"] == "bottom"]
    bot_n = len(bottom)
    bot_pers = float((bottom["segment"] == "Persuadables").mean()) if bot_n else float("nan")
    bot_dogs = float((bottom["segment"] == "Sleeping Dogs").mean()) if bot_n else float("nan")

    summary: dict[str, float | str] = {
        "model": model_name,
        "top_decile_n": float(top_n),
        "top_pct_persuadables": top_pers,
        "top_pct_sleeping_dogs": top_dogs,
        "bottom_pct_persuadables": bot_pers,
        "bottom_pct_sleeping_dogs": bot_dogs,
        "pop_pct_persuadables": float(pop_shares["Persuadables"]),
        "pop_pct_sleeping_dogs": float(pop_shares["Sleeping Dogs"]),
        "persuadables_enrichment_top": (
            top_pers / float(pop_shares["Persuadables"])
            if float(pop_shares["Persuadables"]) > 0
            else float("nan")
        ),
        "sleeping_dogs_enrichment_top": (
            top_dogs / float(pop_shares["Sleeping Dogs"])
            if float(pop_shares["Sleeping Dogs"]) > 0
            else float("nan")
        ),
        "deploy_line": (
            f"If you deployed {model_name} and targeted its top decile, you would reach "
            f"{100 * top_pers:.1f}% true Persuadables and "
            f"{100 * top_dogs:.1f}% true Sleeping Dogs."
        ),
    }
    return table, summary


def print_report(
    tables: list[pd.DataFrame],
    summaries: list[dict[str, float | str]],
) -> None:
    pop = summaries[0]
    print("\n=== Population segment shares (test-set join base) ===")
    print(
        f"  Persuadables={100 * float(pop['pop_pct_persuadables']):.1f}%  "
        f"Sleeping Dogs={100 * float(pop['pop_pct_sleeping_dogs']):.1f}%  "
        f"(full mix ~20/30/25/25 by design)"
    )

    for table, summary in zip(tables, summaries):
        model = str(summary["model"])
        print(f"\n=== Confusion-style table: {model} ===")
        pivot_n = table.pivot_table(
            index="predicted_decile",
            columns="true_segment",
            values="n",
            aggfunc="sum",
        ).reindex(index=["top", "bottom"], columns=SEGMENT_ORDER)
        pivot_pct = table.pivot_table(
            index="predicted_decile",
            columns="true_segment",
            values="pct_of_decile",
            aggfunc="sum",
        ).reindex(index=["top", "bottom"], columns=SEGMENT_ORDER)
        print("Counts:")
        print(pivot_n.to_string())
        print("\nPercent of decile:")
        print(pivot_pct.map(lambda x: f"{100 * x:.1f}%").to_string())

        print("\nEnrichment vs population (top decile):")
        top_rows = table[table["predicted_decile"] == "top"]
        for _, r in top_rows.iterrows():
            print(
                f"  {r['true_segment']:15s}  "
                f"{100 * float(r['pct_of_decile']):5.1f}% of top  vs  "
                f"{100 * float(r['pop_share']):5.1f}% pop  "
                f"({float(r['enrichment']):.2f}x)"
            )

        print(f"\n>>> {summary['deploy_line']}")

    # Operational safety: lower Sleeping Dogs in top decile
    print("\n=== Operational comparison (Sleeping Dogs contamination in TOP decile) ===")
    ranked = sorted(summaries, key=lambda s: float(s["top_pct_sleeping_dogs"]))
    for s in ranked:
        print(
            f"  {s['model']:16s}  top Sleeping Dogs = "
            f"{100 * float(s['top_pct_sleeping_dogs']):.2f}%"
        )
    safer = ranked[0]
    other = ranked[1] if len(ranked) > 1 else None
    print(
        f"\nOperationally safer on this metric: {safer['model']} "
        f"({100 * float(safer['top_pct_sleeping_dogs']):.2f}% Sleeping Dogs in top decile)"
        + (
            f" vs {other['model']} "
            f"({100 * float(other['top_pct_sleeping_dogs']):.2f}%)"
            if other
            else ""
        )
        + "."
    )
    print(
        "Note: this may differ from which model won on Qini or PEHE - "
        "report the contamination ranking as-is."
    )


def run_segment_recovery_check(
    t_path: Path = T_PREDS,
    cf_path: Path = CF_PREDS,
    gt_path: Path = GT_PATH,
    summary_csv: Path = SUMMARY_CSV,
    decile: float = DECILE,
) -> tuple[pd.DataFrame, list[dict[str, float | str]]]:
    gt = load_ground_truth(gt_path)
    # Population shares from the prediction customer universe (test set), via first model join
    # Use full GT shares among customers that appear in either prediction file
    t_preds = load_preds(t_path, "T-learner")
    cf_preds = load_preds(cf_path, "CausalForestDML")
    test_ids = set(t_preds["customer_id"]) | set(cf_preds["customer_id"])
    gt_test = gt[gt["customer_id"].isin(test_ids)]
    pop_shares = population_segment_shares(gt_test)

    tables: list[pd.DataFrame] = []
    summaries: list[dict[str, float | str]] = []

    for name, preds in (("T-learner", t_preds), ("CausalForestDML", cf_preds)):
        table, summary = confusion_for_model(
            name, preds, gt, pop_shares, decile=decile
        )
        tables.append(table)
        summaries.append(summary)

    print_report(tables, summaries)

    combined = pd.concat(tables, ignore_index=True)
    # Append one meta-row per model with deploy metrics
    meta_rows = []
    for s in summaries:
        meta_rows.append(
            {
                "model": s["model"],
                "predicted_decile": "TOP_DECILE_OPS_SUMMARY",
                "true_segment": "META",
                "n": int(float(s["top_decile_n"])),
                "pct_of_decile": float(s["top_pct_persuadables"]),
                "pop_share": float(s["pop_pct_persuadables"]),
                "enrichment": float(s["persuadables_enrichment_top"]),
                "decile_n": int(float(s["top_decile_n"])),
                "top_pct_persuadables": float(s["top_pct_persuadables"]),
                "top_pct_sleeping_dogs": float(s["top_pct_sleeping_dogs"]),
                "deploy_line": s["deploy_line"],
            }
        )
    combined = pd.concat([combined, pd.DataFrame(meta_rows)], ignore_index=True, sort=False)

    # Explicit safer-model row
    safer = min(summaries, key=lambda s: float(s["top_pct_sleeping_dogs"]))
    safer_row = {
        "model": "COMPARISON",
        "predicted_decile": "SAFER_ON_SLEEPING_DOGS_CONTAMINATION",
        "true_segment": str(safer["model"]),
        "n": np.nan,
        "pct_of_decile": float(safer["top_pct_sleeping_dogs"]),
        "pop_share": np.nan,
        "enrichment": np.nan,
        "decile_n": np.nan,
        "top_pct_persuadables": np.nan,
        "top_pct_sleeping_dogs": float(safer["top_pct_sleeping_dogs"]),
        "deploy_line": (
            f"Lower Sleeping Dogs contamination in top decile: {safer['model']} "
            f"({100 * float(safer['top_pct_sleeping_dogs']):.2f}%)."
        ),
    }
    combined = pd.concat([combined, pd.DataFrame([safer_row])], ignore_index=True, sort=False)

    summary_csv.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(summary_csv, index=False)
    print(f"\nWrote {summary_csv}")
    return combined, summaries


if __name__ == "__main__":
    run_segment_recovery_check()
