"""Export Phase 1 + Phase 2 results to static JSON for the Next.js dashboard.

Recomputes Qini curves / uplift metrics and Phase 2 generation diagnostics from
saved prediction CSVs and parquets (same definitions as the analysis scripts).
Does not retrain models.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "dashboard" / "public" / "data"
# Also keep a copy under dashboard/data for local inspection
OUT_DIR_MIRROR = ROOT / "dashboard" / "data"
P1_OUT = ROOT / "outputs"
P1_PROCESSED = ROOT / "data" / "processed"
P2_ROOT = ROOT / "phase2_synthetic_credit"
P2_OUT = P2_ROOT / "outputs"
P2_DATA = P2_ROOT / "data"

# Import Phase-1 Qini helpers (same definition used in the portfolio analysis)
sys.path.insert(0, str(ROOT / "src"))
from evaluation.uplift_metrics import (  # noqa: E402
    qini_coefficient,
    qini_curve,
    uplift_at_k,
)


def _downsample_curve(
    fractions: np.ndarray,
    qini: np.ndarray,
    random_line: np.ndarray,
    max_points: int = 200,
) -> list[dict[str, float]]:
    n = len(fractions)
    if n <= max_points:
        idx = np.arange(n)
    else:
        idx = np.unique(np.linspace(0, n - 1, max_points).astype(int))
    return [
        {
            "fraction": float(fractions[i]),
            "qini": float(qini[i]),
            "random": float(random_line[i]),
        }
        for i in idx
    ]


def model_qini_bundle(preds: pd.DataFrame, model_name: str) -> dict[str, Any]:
    y = preds["true_outcome"]
    t = preds["true_treatment"]
    c = preds["predicted_cate"]
    fractions, qini, random_line = qini_curve(y, t, c)
    return {
        "model": model_name,
        "qini_coefficient": qini_coefficient(y, t, c),
        "uplift_at_10pct": uplift_at_k(y, t, c, 0.1),
        "uplift_at_30pct": uplift_at_k(y, t, c, 0.3),
        "uplift_at_50pct": uplift_at_k(y, t, c, 0.5),
        "curve": _downsample_curve(fractions, qini, random_line),
    }


def _profile_row(row: pd.Series) -> dict[str, Any]:
    return {
        "model": str(row["model"]),
        "segment": str(row["segment"]),
        "n": int(row["n"]),
        "mean_predicted_cate": float(row["mean_predicted_cate"]),
        "median_predicted_cate": float(row["median_predicted_cate"]),
        "obs_visit_rate_treated": float(row["obs_visit_rate_treated"]),
        "obs_visit_rate_control": float(row["obs_visit_rate_control"]),
        "obs_uplift": float(row["obs_uplift"]),
        "share_negative_cate": float(row["share_negative_cate"]),
        "recency_mean": float(row["recency_mean"]),
        "recency_median": float(row["recency_median"]),
        "history_mean": float(row["history_mean"]),
        "history_median": float(row["history_median"]),
        "mens_rate": float(row["mens_rate"]),
        "womens_rate": float(row["womens_rate"]),
        "newbie_rate": float(row["newbie_rate"]),
        "history_segment_mode": str(row["history_segment_mode"]),
        "history_segment_mode_share": float(row["history_segment_mode_share"]),
        "zip_code_mode": str(row["zip_code_mode"]),
        "zip_code_mode_share": float(row["zip_code_mode_share"]),
        "channel_mode": str(row["channel_mode"]),
        "channel_mode_share": float(row["channel_mode_share"]),
    }


def reconstruct_categoricals(df: pd.DataFrame) -> pd.DataFrame:
    """Same one-hot reconstruction used in Phase 1 segment_profile.py."""
    out = df.copy()
    for prefix in ("history_segment_", "zip_code_", "channel_"):
        cols = [c for c in out.columns if c.startswith(prefix)]
        if not cols:
            raise ValueError(f"Missing one-hot block for {prefix}")
        block = out[cols].to_numpy()
        labels = [c[len(prefix) :] for c in cols]
        idx = block.argmax(axis=1)
        out[prefix.rstrip("_")] = pd.Series(idx).map(lambda i: labels[i]).values
    return out


def negative_cate_concentration() -> dict[str, Any]:
    """Recompute T-learner negative-CATE subgroup vs full test distribution."""
    preds = pd.read_csv(P1_OUT / "t_learner_predictions.csv")
    test = reconstruct_categoricals(pd.read_parquet(P1_PROCESSED / "test.parquet"))
    merged = preds.merge(
        test[
            [
                "customer_id",
                "recency",
                "history",
                "mens",
                "womens",
                "newbie",
                "history_segment",
                "zip_code",
                "channel",
            ]
        ],
        on="customer_id",
        how="inner",
        validate="one_to_one",
    )
    neg = merged[merged["predicted_cate"] < 0]
    n_test = len(merged)
    n_neg = len(neg)

    gaps: list[dict[str, Any]] = []
    for cat in ("history_segment", "zip_code", "channel"):
        neg_p = neg[cat].value_counts(normalize=True)
        all_p = merged[cat].value_counts(normalize=True)
        cmp = pd.DataFrame({"neg_share": neg_p, "test_share": all_p}).fillna(0.0)
        cmp["gap_pp"] = (cmp["neg_share"] - cmp["test_share"]) * 100
        cmp = cmp.sort_values("gap_pp", key=lambda s: s.abs(), ascending=False)
        for level, r in cmp.iterrows():
            gaps.append(
                {
                    "feature": cat,
                    "level": str(level),
                    "neg_share": float(r["neg_share"]),
                    "test_share": float(r["test_share"]),
                    "gap_pp": float(r["gap_pp"]),
                }
            )

    return {
        "n_negative": int(n_neg),
        "n_test": int(n_test),
        "share_of_test": float(n_neg / n_test) if n_test else None,
        "mean_predicted_cate": float(neg["predicted_cate"].mean()) if n_neg else None,
        "history_mean_neg": float(neg["history"].mean()) if n_neg else None,
        "history_mean_test": float(merged["history"].mean()),
        "category_gaps": gaps,
        "framing": (
            "Plausible but low-sample finding (1.4% of test set), not a confirmed "
            "population effect. Concentration among higher-history / Rural / "
            "Multichannel customers informed Phase 2 Sleeping Dogs design."
        ),
    }


def export_phase1() -> dict[str, Any]:
    t_preds = pd.read_csv(P1_OUT / "t_learner_predictions.csv")
    cf_preds = pd.read_csv(P1_OUT / "causal_forest_predictions.csv")
    profile = pd.read_csv(P1_OUT / "segment_profile_summary.csv")

    overlap_row = profile[profile["segment"] == "top_decile_customer_id_overlap"].iloc[0]
    profiles = [
        _profile_row(r)
        for _, r in profile[profile["row_type"] == "segment_profile"].iterrows()
    ]

    return {
        "meta": {
            "phase": 1,
            "title": "Hillstrom MineThatData",
            "framing": (
                "Real randomized email marketing experiment used to prove uplift "
                "methodology before touching synthetic credit data. Mens E-Mail vs "
                "No E-Mail; outcome = visit."
            ),
            "n_test": int(len(t_preds)),
        },
        "models": [
            model_qini_bundle(t_preds, "T-learner"),
            model_qini_bundle(cf_preds, "CausalForestDML"),
        ],
        "segment_profiles": profiles,
        "model_overlap": {
            "overlap_share": float(overlap_row["top_decile_overlap_share"]),
            "jaccard": float(overlap_row["top_decile_jaccard"]),
            "n_intersection": int(overlap_row["top_decile_n_intersection"]),
            "n_top": int(overlap_row["n_treated"]),
            "agreement_flag": str(overlap_row["agreement_flag"]),
        },
        "negative_cate": negative_cate_concentration(),
    }


def export_phase2_generation() -> dict[str, Any]:
    full = pd.read_parquet(P2_DATA / "synthetic_credit_full.parquet")
    gt = pd.read_parquet(P2_DATA / "synthetic_credit_ground_truth.parquet")
    merged = full.merge(gt, on="customer_id", how="inner", validate="one_to_one")

    segments: list[dict[str, Any]] = []
    order = ["Persuadables", "Sure Things", "Lost Causes", "Sleeping Dogs"]
    traits = {
        "Persuadables": (
            "Moderate utilization, decent payment consistency; App / Urban skew. "
            "True CATE +0.15 to +0.20."
        ),
        "Sure Things": (
            "High payment consistency, low utilization. True CATE ~0 "
            "(noise only)."
        ),
        "Lost Causes": (
            "Low payment consistency, high utilization. True CATE ~0 "
            "(noise only)."
        ),
        "Sleeping Dogs": (
            "High utilization, many active lines; Rural / CallCenter skew "
            "(contact saturation). True CATE -0.10 to -0.15."
        ),
    }
    for seg in order:
        g = merged[merged["segment"] == seg]
        t = g[g["treatment"] == 1]
        c = g[g["treatment"] == 0]
        segments.append(
            {
                "segment": seg,
                "n": int(len(g)),
                "share": float(len(g) / len(merged)),
                "mean_true_cate": float(g["true_cate"].mean()),
                "obs_gap": float(
                    t["good_standing"].mean() - c["good_standing"].mean()
                ),
                "mean_baseline_prob": float(g["baseline_prob"].mean()),
                "traits": traits[seg],
            }
        )

    return {
        "n_total": int(len(merged)),
        "treatment_share": float(merged["treatment"].mean()),
        "segments": segments,
    }


def export_phase2() -> dict[str, Any]:
    t_preds = pd.read_csv(P2_OUT / "t_learner_predictions.csv")
    cf_preds = pd.read_csv(P2_OUT / "causal_forest_predictions.csv")
    cate = pd.read_csv(P2_OUT / "cate_recovery_summary.csv")
    recovery = pd.read_csv(P2_OUT / "segment_recovery_summary.csv")

    overall = cate[cate["row_type"] == "overall"]
    per_seg = cate[cate["row_type"] == "per_segment"]

    pehe_rows = [
        {
            "model": str(r["model"]),
            "pehe": float(r["pehe"]),
            "corr_pred_true_cate": float(r["corr_pred_true_cate"]),
            "mean_predicted_cate": float(r["mean_predicted_cate"]),
            "mean_true_cate": float(r["mean_true_cate"]),
            "n": int(r["n"]),
        }
        for _, r in overall.iterrows()
    ]

    # Centerpiece: one row per segment with true + both model means
    segments_order = ["Persuadables", "Sure Things", "Lost Causes", "Sleeping Dogs"]
    cate_by_segment: list[dict[str, Any]] = []
    for seg in segments_order:
        rows = per_seg[per_seg["segment"] == seg]
        t_row = rows[rows["model"] == "T-learner"].iloc[0]
        cf_row = rows[rows["model"] == "CausalForestDML"].iloc[0]
        cate_by_segment.append(
            {
                "segment": seg,
                "mean_true_cate": float(t_row["mean_true_cate"]),
                "t_learner": float(t_row["mean_predicted_cate"]),
                "causal_forest": float(cf_row["mean_predicted_cate"]),
                "n": int(t_row["n"]),
            }
        )

    composition = recovery[
        recovery["true_segment"].isin(segments_order)
        & recovery["predicted_decile"].isin(["top", "bottom"])
    ]
    composition_rows = [
        {
            "model": str(r["model"]),
            "predicted_decile": str(r["predicted_decile"]),
            "true_segment": str(r["true_segment"]),
            "n": int(r["n"]),
            "pct_of_decile": float(r["pct_of_decile"]),
            "pop_share": float(r["pop_share"]),
            "enrichment": float(r["enrichment"]),
            "decile_n": int(r["decile_n"]),
        }
        for _, r in composition.iterrows()
    ]

    ops = recovery[recovery["predicted_decile"] == "TOP_DECILE_OPS_SUMMARY"]
    ops_rows = [
        {
            "model": str(r["model"]),
            "top_pct_persuadables": float(r["top_pct_persuadables"]),
            "top_pct_sleeping_dogs": float(r["top_pct_sleeping_dogs"]),
            "deploy_line": str(r["deploy_line"]),
        }
        for _, r in ops.iterrows()
    ]
    safer = recovery[
        recovery["predicted_decile"] == "SAFER_ON_SLEEPING_DOGS_CONTAMINATION"
    ].iloc[0]

    t_pehe = next(r["pehe"] for r in pehe_rows if r["model"] == "T-learner")
    cf_pehe = next(r["pehe"] for r in pehe_rows if r["model"] == "CausalForestDML")
    models = [
        model_qini_bundle(t_preds, "T-learner"),
        model_qini_bundle(cf_preds, "CausalForestDML"),
    ]
    t_qini = models[0]["qini_coefficient"]
    cf_qini = models[1]["qini_coefficient"]
    qini_winner = "T-learner" if t_qini >= cf_qini else "CausalForestDML"
    pehe_winner = "T-learner" if t_pehe <= cf_pehe else "CausalForestDML"

    return {
        "meta": {
            "phase": 2,
            "title": "Synthetic credit-limit RCT",
            "framing": (
                "Synthetic randomized credit-limit experiment with known latent "
                "segments and true CATE, designed so Sleeping Dogs mirror Phase 1's "
                "contact-saturation logic. Outcome = good_standing at 3 months."
            ),
            "n_test": int(len(t_preds)),
        },
        "generation": export_phase2_generation(),
        "models": models,
        "cate_recovery": {
            "overall": pehe_rows,
            "by_segment": cate_by_segment,
        },
        "segment_recovery": {
            "composition": composition_rows,
            "ops_summaries": ops_rows,
            "safer_model": str(safer["true_segment"]),
            "safer_sleeping_dogs_rate": float(safer["top_pct_sleeping_dogs"]),
            "safer_line": str(safer["deploy_line"]),
        },
        "metric_tradeoff": {
            "qini_winner": qini_winner,
            "pehe_winner": pehe_winner,
            "contamination_safer": str(safer["true_segment"]),
            "note": (
                "CausalForestDML wins on PEHE and Sleeping Dogs contamination safety; "
                "T-learner wins on Qini ranking. Prefer CF when individual effect-size "
                "estimation or harm-avoidance in the treated list matters; prefer "
                "T-learner when overall ranking quality for a mailing/approval curve "
                "is the primary KPI."
            ),
        },
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR_MIRROR.mkdir(parents=True, exist_ok=True)
    phase1 = export_phase1()
    phase2 = export_phase2()

    for directory in (OUT_DIR, OUT_DIR_MIRROR):
        p1_path = directory / "phase1.json"
        p2_path = directory / "phase2.json"
        p1_path.write_text(json.dumps(phase1, indent=2), encoding="utf-8")
        p2_path.write_text(json.dumps(phase2, indent=2), encoding="utf-8")
        print(f"Wrote {p1_path}")
        print(f"Wrote {p2_path}")
    print(
        f"Phase1 models Qini: "
        f"{[m['qini_coefficient'] for m in phase1['models']]}"
    )
    print(
        f"Phase2 PEHE: "
        f"{[(r['model'], r['pehe']) for r in phase2['cate_recovery']['overall']]}"
    )


if __name__ == "__main__":
    main()
