"""Segment profiling for Phase 1 Hillstrom uplift models.

Loads *saved* test predictions + processed test parquet (no retraining).
Reconstructs original categoricals from one-hot columns locally so profiles
are human-readable without changing data_prep.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_SRC_DIR = Path(__file__).resolve().parent.parent
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from data_prep import PROCESSED_DIR, PROJECT_ROOT

T_LEARNER_PREDS: Path = PROJECT_ROOT / "outputs" / "t_learner_predictions.csv"
CAUSAL_FOREST_PREDS: Path = PROJECT_ROOT / "outputs" / "causal_forest_predictions.csv"
SUMMARY_CSV: Path = PROJECT_ROOT / "outputs" / "segment_profile_summary.csv"
NARRATIVE_MD: Path = PROJECT_ROOT / "outputs" / "segment_profile_narrative.md"

NUMERIC_FEATURES: list[str] = ["recency", "history"]
BINARY_FEATURES: list[str] = ["mens", "womens", "newbie"]
CATEGORICAL_PREFIXES: tuple[str, ...] = (
    "history_segment_",
    "zip_code_",
    "channel_",
)
DECILE: float = 0.10


def reconstruct_categoricals(df: pd.DataFrame) -> pd.DataFrame:
    """Rebuild history_segment / zip_code / channel from mutually exclusive one-hots."""
    out = df.copy()
    for prefix in CATEGORICAL_PREFIXES:
        cols = [c for c in out.columns if c.startswith(prefix)]
        if not cols:
            raise ValueError(
                f"No one-hot columns found for prefix {prefix!r}. "
                "Cannot reconstruct the original categorical."
            )
        # argmax over the dummy block; values should be 0/1 with exactly one hot
        block = out[cols].to_numpy()
        if not np.all((block.sum(axis=1) == 1)):
            bad = int((block.sum(axis=1) != 1).sum())
            print(
                f"WARNING: {bad} rows do not have exactly one active dummy "
                f"for {prefix}; using argmax anyway."
            )
        labels = [c[len(prefix) :] for c in cols]
        idx = block.argmax(axis=1)
        feature_name = prefix.rstrip("_")
        out[feature_name] = pd.Series(idx).map(lambda i: labels[i]).values
    return out


def load_test_with_features(
    processed_dir: Path = PROCESSED_DIR,
) -> pd.DataFrame:
    """Load processed test set and reconstruct human-readable categoricals."""
    test_path = processed_dir / "test.parquet"
    if not test_path.exists():
        raise FileNotFoundError(f"Missing {test_path}. Run data_prep.py first.")
    test_df = pd.read_parquet(test_path)
    return reconstruct_categoricals(test_df)


def load_predictions(path: Path, model_name: str) -> pd.DataFrame:
    """Load a predictions CSV; require the shared uplift columns."""
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path} for {model_name}. Run the model script first "
            "(do not retrain from this module)."
        )
    preds = pd.read_csv(path)
    required = {"customer_id", "true_treatment", "true_outcome", "predicted_cate"}
    missing = required - set(preds.columns)
    if missing:
        raise ValueError(f"{model_name} predictions missing columns: {missing}")
    return preds


def assign_decile_segments(
    merged: pd.DataFrame,
    decile: float = DECILE,
) -> pd.DataFrame:
    """Rank by predicted CATE; tag top/bottom deciles with segment labels."""
    if not 0 < decile < 0.5:
        raise ValueError(f"decile must be in (0, 0.5), got {decile}")

    out = merged.sort_values("predicted_cate", ascending=False).reset_index(drop=True)
    n = len(out)
    n_top = max(1, int(np.floor(decile * n)))
    # Keep top and bottom the same size
    n_bottom = n_top

    out["rank_by_cate"] = np.arange(1, n + 1)
    out["segment"] = "middle"
    out.loc[: n_top - 1, "segment"] = "top_decile_persuadables"

    bottom_idx = out.index[-n_bottom:]
    bottom_mean_cate = float(out.loc[bottom_idx, "predicted_cate"].mean())
    bottom_neg_share = float((out.loc[bottom_idx, "predicted_cate"] < 0).mean())

    if bottom_mean_cate < 0:
        bottom_label = "bottom_decile_sleeping_dogs"
    else:
        bottom_label = "bottom_decile_low_no_uplift"
    out.loc[bottom_idx, "segment"] = bottom_label

    # Attach group-level metadata as columns for the summary export
    out.attrs["n_top"] = n_top
    out.attrs["n_bottom"] = n_bottom
    out.attrs["bottom_label"] = bottom_label
    out.attrs["bottom_mean_cate"] = bottom_mean_cate
    out.attrs["bottom_neg_share"] = bottom_neg_share
    return out


def _observed_uplift(group: pd.DataFrame) -> dict[str, float]:
    """Empirical visit rates by arm inside a segment (RCT check)."""
    treated = group[group["true_treatment"] == 1]
    control = group[group["true_treatment"] == 0]
    visit_t = float(treated["true_outcome"].mean()) if len(treated) else float("nan")
    visit_c = float(control["true_outcome"].mean()) if len(control) else float("nan")
    return {
        "n": float(len(group)),
        "n_treated": float(len(treated)),
        "n_control": float(len(control)),
        "mean_predicted_cate": float(group["predicted_cate"].mean()),
        "median_predicted_cate": float(group["predicted_cate"].median()),
        "obs_visit_rate_treated": visit_t,
        "obs_visit_rate_control": visit_c,
        "obs_uplift": visit_t - visit_c,
        "share_negative_cate": float((group["predicted_cate"] < 0).mean()),
    }


def profile_segment(group: pd.DataFrame) -> dict[str, float | str]:
    """Mean/median (and categorical shares) for one model × segment."""
    stats: dict[str, float | str] = {}
    stats.update(_observed_uplift(group))

    for col in NUMERIC_FEATURES:
        stats[f"{col}_mean"] = float(group[col].mean())
        stats[f"{col}_median"] = float(group[col].median())

    for col in BINARY_FEATURES:
        stats[f"{col}_rate"] = float(group[col].mean())

    for cat in ("history_segment", "zip_code", "channel"):
        counts = group[cat].value_counts(normalize=True)
        mode = str(counts.index[0])
        stats[f"{cat}_mode"] = mode
        stats[f"{cat}_mode_share"] = float(counts.iloc[0])
        # Keep full distribution as a compact string for the CSV
        dist = "; ".join(f"{k}={v:.1%}" for k, v in counts.items())
        stats[f"{cat}_distribution"] = dist

    return stats


def profile_model(
    model_name: str,
    preds: pd.DataFrame,
    test_df: pd.DataFrame,
    decile: float = DECILE,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (long summary rows for this model, scored frame with segment tags)."""
    feat_cols = [
        "customer_id",
        "recency",
        "history",
        "mens",
        "womens",
        "newbie",
        "history_segment",
        "zip_code",
        "channel",
        "treatment",
        "visit",
    ]
    missing = [c for c in feat_cols if c not in test_df.columns]
    if missing:
        raise ValueError(f"test_df missing columns after reconstruction: {missing}")

    merged = preds.merge(
        test_df[feat_cols],
        on="customer_id",
        how="inner",
        validate="one_to_one",
    )
    if len(merged) != len(preds):
        raise ValueError(
            f"{model_name}: merge dropped rows "
            f"(preds={len(preds)}, merged={len(merged)})."
        )

    scored = assign_decile_segments(merged, decile=decile)
    rows: list[dict[str, float | str]] = []
    for segment, group in scored.groupby("segment", sort=False):
        if segment == "middle":
            continue
        row = profile_segment(group)
        row["model"] = model_name
        row["segment"] = str(segment)
        rows.append(row)

    summary = pd.DataFrame(rows)
    return summary, scored


def top_decile_overlap(
    scored_a: pd.DataFrame,
    scored_b: pd.DataFrame,
    name_a: str,
    name_b: str,
) -> dict[str, float | str]:
    """Customer-id overlap between the two models' top-decile persuadables."""
    top_a = set(
        scored_a.loc[
            scored_a["segment"] == "top_decile_persuadables", "customer_id"
        ]
    )
    top_b = set(
        scored_b.loc[
            scored_b["segment"] == "top_decile_persuadables", "customer_id"
        ]
    )
    inter = top_a & top_b
    union = top_a | top_b
    # Equal-sized deciles → share of each model's top 10% also in the other
    overlap_of_top = len(inter) / len(top_a) if top_a else float("nan")
    jaccard = len(inter) / len(union) if union else float("nan")

    if overlap_of_top < 0.4:
        agreement = (
            "Low overlap. The models disagree a lot on who sits in the top 10%. "
            "I would not treat segment membership as stable across estimators."
        )
    elif overlap_of_top < 0.7:
        agreement = (
            "Moderate overlap. Some shared persuadables, but each model still has "
            "a big unique slice. I would not treat either top-decile list as the "
            "final answer on its own."
        )
    else:
        agreement = (
            "High overlap. The models mostly agree on who is in the top decile."
        )

    return {
        "model_a": name_a,
        "model_b": name_b,
        "n_top_a": float(len(top_a)),
        "n_top_b": float(len(top_b)),
        "n_intersection": float(len(inter)),
        "overlap_share_of_top_decile": float(overlap_of_top),
        "jaccard": float(jaccard),
        "agreement_flag": agreement,
    }


def _fmt_pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def _profile_sentence(row: pd.Series) -> str:
    """One plain-English sentence from a summary row."""
    return (
        f"recency mean/median {row['recency_mean']:.1f}/{row['recency_median']:.1f} months, "
        f"history ${row['history_mean']:.0f}/${row['history_median']:.0f} (mean/median), "
        f"mens={_fmt_pct(float(row['mens_rate']))}, "
        f"womens={_fmt_pct(float(row['womens_rate']))}, "
        f"newbie={_fmt_pct(float(row['newbie_rate']))}; "
        f"modal history_segment={row['history_segment_mode']} "
        f"({_fmt_pct(float(row['history_segment_mode_share']))}), "
        f"zip_code={row['zip_code_mode']} "
        f"({_fmt_pct(float(row['zip_code_mode_share']))}), "
        f"channel={row['channel_mode']} "
        f"({_fmt_pct(float(row['channel_mode_share']))}); "
        f"observed visit treated/control="
        f"{_fmt_pct(float(row['obs_visit_rate_treated']))}/"
        f"{_fmt_pct(float(row['obs_visit_rate_control']))} "
        f"(obs uplift={float(row['obs_uplift']):+.3f})"
    )


def build_narrative(
    summary: pd.DataFrame,
    overlap: dict[str, float | str],
) -> str:
    """Markdown narrative for Persuadables / Sleeping Dogs / model agreement."""
    lines: list[str] = [
        "# Segment profile narrative (Phase 1 Hillstrom)",
        "",
        "Built from saved test predictions only - no retraining.",
        "",
    ]

    # Persuadables across models
    lines.append("## Persuadables (top decile by predicted CATE)")
    lines.append("")
    top_rows = summary[summary["segment"] == "top_decile_persuadables"]
    for _, row in top_rows.iterrows():
        lines.append(f"**{row['model']}:** Persuadables in this data tend to look like: "
                     f"{_profile_sentence(row)}.")
        lines.append("")

    # Bottom segments
    lines.append("## Sleeping Dogs / low-uplift (bottom decile by predicted CATE)")
    lines.append("")
    bottom_rows = summary[summary["segment"].astype(str).str.startswith("bottom_decile")]
    for _, row in bottom_rows.iterrows():
        label = str(row["segment"])
        if "sleeping_dogs" in label:
            headline = "Sleeping Dogs / low-uplift customers tend to look like"
            note = (
                f"Bottom-decile mean predicted CATE is negative "
                f"({float(row['mean_predicted_cate']):.4f}); "
                f"{_fmt_pct(float(row['share_negative_cate']))} of this decile has CATE < 0."
            )
        else:
            headline = "Low/no-uplift customers (bottom decile; CATE still non-negative) tend to look like"
            note = (
                f"Bottom-decile mean predicted CATE is still non-negative "
                f"({float(row['mean_predicted_cate']):.4f}); "
                f"labeling as low/no uplift rather than Sleeping Dogs. "
                f"Share with CATE < 0: {_fmt_pct(float(row['share_negative_cate']))}."
            )
        lines.append(f"**{row['model']}:** {headline}: {_profile_sentence(row)}. {note}")
        lines.append("")

    # Cross-model agreement
    lines.append("## Do the two models agree on who is in the top 10%?")
    lines.append("")
    ov = float(overlap["overlap_share_of_top_decile"])
    lines.append(
        f"Top-decile customer_id overlap between {overlap['model_a']} and "
        f"{overlap['model_b']}: **{_fmt_pct(ov)}** "
        f"({int(float(overlap['n_intersection']))} of "
        f"{int(float(overlap['n_top_a']))} customers; "
        f"Jaccard={float(overlap['jaccard']):.3f})."
    )
    lines.append("")
    lines.append(f"**Agreement flag:** {overlap['agreement_flag']}")
    lines.append("")

    if ov < 0.5:
        lines.append(
            "This is a real disagreement worth noting: metric tables can look similar "
            "while the *people* each model would mail first differ a lot. For Phase 2 "
            "design, prefer features that show a consistent direction across both "
            "estimators rather than over-fitting to one model's top-decile list."
        )
    else:
        lines.append(
            "Where the models agree on membership, shared feature tilts are the safer "
            "reference for designing heterogeneity in a synthetic Phase 2 dataset."
        )

    return "\n".join(lines) + "\n"


def print_console_summary(
    summary: pd.DataFrame,
    overlap: dict[str, float | str],
    narrative: str,
) -> None:
    """Print a compact table plus the narrative."""
    display_cols = [
        "model",
        "segment",
        "n",
        "mean_predicted_cate",
        "obs_visit_rate_treated",
        "obs_visit_rate_control",
        "obs_uplift",
        "recency_mean",
        "history_mean",
        "mens_rate",
        "womens_rate",
        "newbie_rate",
        "history_segment_mode",
        "zip_code_mode",
        "channel_mode",
    ]
    print("\n=== Segment profile summary (key columns) ===")
    print(
        summary[display_cols].to_string(
            index=False,
            float_format=lambda x: f"{x:.4f}",
        )
    )
    print("\n=== Top-decile overlap ===")
    for k, v in overlap.items():
        print(f"  {k}: {v}")
    print("\n=== Narrative ===")
    print(narrative)


def run_segment_profile(
    processed_dir: Path = PROCESSED_DIR,
    t_path: Path = T_LEARNER_PREDS,
    cf_path: Path = CAUSAL_FOREST_PREDS,
    summary_csv: Path = SUMMARY_CSV,
    narrative_md: Path = NARRATIVE_MD,
    decile: float = DECILE,
) -> tuple[pd.DataFrame, dict[str, float | str], str]:
    """End-to-end segment profiling from saved artifacts only."""
    test_df = load_test_with_features(processed_dir)
    t_preds = load_predictions(t_path, "T-learner")
    cf_preds = load_predictions(cf_path, "CausalForestDML")

    t_summary, t_scored = profile_model("T-learner", t_preds, test_df, decile=decile)
    cf_summary, cf_scored = profile_model(
        "CausalForestDML", cf_preds, test_df, decile=decile
    )
    summary = pd.concat([t_summary, cf_summary], ignore_index=True)

    overlap = top_decile_overlap(
        t_scored, cf_scored, "T-learner", "CausalForestDML"
    )
    # Keep segment rows clean; append one explicit overlap meta-row with named fields
    summary["row_type"] = "segment_profile"
    summary["top_decile_overlap_share"] = np.nan
    summary["top_decile_jaccard"] = np.nan
    summary["top_decile_n_intersection"] = np.nan
    summary["agreement_flag"] = ""

    overlap_row = {col: np.nan for col in summary.columns}
    overlap_row.update(
        {
            "row_type": "overlap_meta",
            "model": "BOTH",
            "segment": "top_decile_customer_id_overlap",
            "n": float(overlap["n_intersection"]),
            "n_treated": float(overlap["n_top_a"]),
            "n_control": float(overlap["n_top_b"]),
            "top_decile_overlap_share": float(overlap["overlap_share_of_top_decile"]),
            "top_decile_jaccard": float(overlap["jaccard"]),
            "top_decile_n_intersection": float(overlap["n_intersection"]),
            "agreement_flag": str(overlap["agreement_flag"]),
            "history_segment_distribution": str(overlap["agreement_flag"]),
        }
    )
    summary_out = pd.concat([summary, pd.DataFrame([overlap_row])], ignore_index=True)

    narrative = build_narrative(summary, overlap)

    summary_csv.parent.mkdir(parents=True, exist_ok=True)
    summary_out.to_csv(summary_csv, index=False)
    narrative_md.write_text(narrative, encoding="utf-8")
    print(f"Wrote {summary_csv}")
    print(f"Wrote {narrative_md}")
    print_console_summary(summary, overlap, narrative)
    return summary_out, overlap, narrative


if __name__ == "__main__":
    run_segment_profile()
