"""Phase 1 data prep for Hillstrom MineThatData uplift modeling.

Loads the Hillstrom email experiment, filters to Mens E-Mail vs No E-Mail,
encodes categoricals, splits train/test with joint treatment+outcome
stratification, and writes processed parquet files.
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

import pandas as pd
from sklearn.model_selection import train_test_split

RANDOM_SEED: int = 42
TEST_SIZE: float = 0.2
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
RAW_PATH: Path = PROJECT_ROOT / "data" / "raw" / "hillstrom.csv"
PROCESSED_DIR: Path = PROJECT_ROOT / "data" / "processed"

NUMERIC_FEATURES: list[str] = ["recency", "history", "mens", "womens", "newbie"]
CATEGORICAL_FEATURES: list[str] = ["history_segment", "zip_code", "channel"]
OUTCOME_COLS: list[str] = ["visit", "conversion", "spend"]


def download_hillstrom(raw_path: Path = RAW_PATH) -> Path:
    """Download Hillstrom via scikit-uplift and save as CSV if missing.

    sklift's fetch_hillstrom returns one target at a time via target_col.
    We fetch visit/conversion/spend and join them so Phase 2-ready columns
    (spend, conversion) stay in the processed files even though Phase 1
    only models visit.
    """
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    if raw_path.exists():
        print(f"Raw data already present: {raw_path}")
        return raw_path

    from sklift.datasets import fetch_hillstrom

    print("Downloading Hillstrom dataset via sklift.datasets.fetch_hillstrom()...")
    visit_bundle = fetch_hillstrom(target_col="visit")
    df = visit_bundle.data.copy()
    df["visit"] = visit_bundle.target.values
    df["segment"] = visit_bundle.treatment.values

    for outcome in ("conversion", "spend"):
        bundle = fetch_hillstrom(target_col=outcome)
        # Row order matches across fetches (same underlying file)
        df[outcome] = bundle.target.values

    df.to_csv(raw_path, index=False)
    print(f"Saved raw Hillstrom CSV to {raw_path} ({len(df):,} rows)")
    return raw_path


def load_raw(raw_path: Path = RAW_PATH) -> pd.DataFrame:
    """Load hillstrom.csv and attach a stable 0-based customer_id."""
    if not raw_path.exists():
        download_hillstrom(raw_path)
    df = pd.read_csv(raw_path)
    df = df.reset_index(drop=True)
    df.insert(0, "customer_id", df.index.astype(int))
    return df


def filter_binary_treatment(df: pd.DataFrame) -> pd.DataFrame:
    """Keep Mens E-Mail (treatment=1) and No E-Mail (treatment=0); drop Womens."""
    mask = df["segment"].isin(["Mens E-Mail", "No E-Mail"])
    out = df.loc[mask].copy()
    out["treatment"] = (out["segment"] == "Mens E-Mail").astype(int)
    return out


def encode_features(df: pd.DataFrame) -> pd.DataFrame:
    """One-hot encode categoricals; keep numeric features and labels."""
    missing_cats = [c for c in CATEGORICAL_FEATURES if c not in df.columns]
    missing_nums = [c for c in NUMERIC_FEATURES if c not in df.columns]
    if missing_cats or missing_nums:
        raise ValueError(
            f"Missing expected columns. categoricals={missing_cats}, numerics={missing_nums}"
        )

    encoded = pd.get_dummies(
        df,
        columns=CATEGORICAL_FEATURES,
        drop_first=False,
        dtype=int,
    )
    # Drop original segment (replaced by treatment); keep outcomes for later use
    if "segment" in encoded.columns:
        encoded = encoded.drop(columns=["segment"])
    return encoded


def train_test_split_stratified(
    df: pd.DataFrame,
    test_size: float = TEST_SIZE,
    random_state: int = RANDOM_SEED,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Stratify jointly on treatment and visit via a combined key."""
    if "visit" not in df.columns:
        raise ValueError("Outcome column 'visit' is required for stratified split.")
    strat_key = df["treatment"].astype(str) + "_" + df["visit"].astype(str)
    train_df, test_df = train_test_split(
        df,
        test_size=test_size,
        random_state=random_state,
        stratify=strat_key,
    )
    return train_df.reset_index(drop=True), test_df.reset_index(drop=True)


def randomization_check(train_df: pd.DataFrame) -> None:
    """Print diagnostics confirming RCT balance and outcome rates by arm."""
    print("\n=== Randomization / Sanity Check (TRAIN) ===")
    n = len(train_df)
    treat_rate = train_df["treatment"].mean()
    print(f"Train n = {n:,}")
    print(f"Treatment share = {treat_rate:.4f} (expect ~0.50 for binary Mens vs No E-Mail)")

    treated = train_df[train_df["treatment"] == 1]
    control = train_df[train_df["treatment"] == 0]
    print(
        f"mean(visit) | treated = {treated['visit'].mean():.4f} | "
        f"control = {control['visit'].mean():.4f} | "
        f"ATE (naive) = {treated['visit'].mean() - control['visit'].mean():.4f}"
    )

    print("\nCovariate balance (randomization check - means should be similar):")
    for col in ["recency", "history"]:
        t_mean = treated[col].mean()
        c_mean = control[col].mean()
        print(
            f"  {col:10s}  treated={t_mean:.4f}  control={c_mean:.4f}  "
            f"diff={t_mean - c_mean:.4f}"
        )
    print("=== End Sanity Check ===\n")


def feature_columns(df: pd.DataFrame) -> list[str]:
    """Return model feature column names (exclude id, treatment, outcomes)."""
    exclude = {"customer_id", "treatment", *OUTCOME_COLS}
    # Only exclude outcome cols that exist
    exclude = {c for c in exclude if c in df.columns or c == "customer_id" or c == "treatment"}
    exclude = {"customer_id", "treatment"} | set(OUTCOME_COLS)
    return [c for c in df.columns if c not in exclude]


def save_processed(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    processed_dir: Path = PROCESSED_DIR,
) -> Tuple[Path, Path]:
    """Write train/test parquet files."""
    processed_dir.mkdir(parents=True, exist_ok=True)
    train_path = processed_dir / "train.parquet"
    test_path = processed_dir / "test.parquet"
    train_df.to_parquet(train_path, index=False)
    test_df.to_parquet(test_path, index=False)
    print(f"Wrote {train_path} ({len(train_df):,} rows)")
    print(f"Wrote {test_path} ({len(test_df):,} rows)")
    return train_path, test_path


def run_data_prep(
    raw_path: Path = RAW_PATH,
    processed_dir: Path = PROCESSED_DIR,
    test_size: float = TEST_SIZE,
    random_state: int = RANDOM_SEED,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Full Phase 1 prep pipeline: download → filter → encode → split → save."""
    df = load_raw(raw_path)
    print(f"Loaded raw: {len(df):,} rows, columns={list(df.columns)}")

    df = filter_binary_treatment(df)
    print(
        f"After binary filter (Mens vs No E-Mail): {len(df):,} rows | "
        f"treatment rate={df['treatment'].mean():.4f}"
    )

    # Ensure conversion/spend exist for later phases even if unused now
    for col in ("conversion", "spend"):
        if col not in df.columns:
            print(f"WARNING: '{col}' missing from raw data; filling with 0 for schema stability.")
            df[col] = 0

    df = encode_features(df)
    train_df, test_df = train_test_split_stratified(
        df, test_size=test_size, random_state=random_state
    )
    randomization_check(train_df)
    save_processed(train_df, test_df, processed_dir)
    return train_df, test_df


if __name__ == "__main__":
    run_data_prep()
