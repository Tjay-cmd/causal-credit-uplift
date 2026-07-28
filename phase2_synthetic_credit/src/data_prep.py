"""Phase 2 data prep for synthetic credit-limit uplift modeling.

Loads synthetic_credit_full.parquet only (no ground truth), encodes categoricals,
stratifies train/test by treatment x outcome, writes processed parquet.
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

import pandas as pd
from sklearn.model_selection import train_test_split

RANDOM_SEED: int = 42
TEST_SIZE: float = 0.2
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
RAW_FULL: Path = PROJECT_ROOT / "data" / "synthetic_credit_full.parquet"
PROCESSED_DIR: Path = PROJECT_ROOT / "data" / "processed"

NUMERIC_FEATURES: list[str] = [
    "months_since_account_open",
    "avg_utilization_last_3m",
    "payment_consistency_score",
    "existing_limit",
    "num_active_credit_lines",
]
CATEGORICAL_FEATURES: list[str] = ["income_band", "channel", "region"]
OUTCOME_COL: str = "good_standing"
TREATMENT_COL: str = "treatment"
ID_COL: str = "customer_id"


def load_modeling_table(path: Path = RAW_FULL) -> pd.DataFrame:
    """Load the modeling parquet; refuse files that contain ground-truth columns."""
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Run src/generate_data.py first."
        )
    df = pd.read_parquet(path)
    leak = {"segment", "true_cate", "baseline_prob", "true_prob"} & set(df.columns)
    if leak:
        raise ValueError(
            f"Ground-truth columns present in modeling table (refuse to proceed): {leak}"
        )
    required = {ID_COL, TREATMENT_COL, OUTCOME_COL, *NUMERIC_FEATURES, *CATEGORICAL_FEATURES}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Modeling table missing columns: {missing}")
    return df.copy()


def encode_features(df: pd.DataFrame) -> pd.DataFrame:
    """One-hot encode categoricals; missing income_band becomes its own level."""
    out = df.copy()
    # Explicit missing level so get_dummies does not silently drop NA rows
    out["income_band"] = out["income_band"].astype("string").fillna("<missing>")
    out = pd.get_dummies(
        out,
        columns=CATEGORICAL_FEATURES,
        drop_first=False,
        dtype=int,
    )
    return out


def feature_columns(df: pd.DataFrame) -> list[str]:
    """Model feature names: everything except id / treatment / outcome."""
    exclude = {ID_COL, TREATMENT_COL, OUTCOME_COL}
    return [c for c in df.columns if c not in exclude]


def train_test_split_stratified(
    df: pd.DataFrame,
    test_size: float = TEST_SIZE,
    random_state: int = RANDOM_SEED,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Stratify jointly on treatment and good_standing."""
    strat_key = (
        df[TREATMENT_COL].astype(str) + "_" + df[OUTCOME_COL].astype(str)
    )
    train_df, test_df = train_test_split(
        df,
        test_size=test_size,
        random_state=random_state,
        stratify=strat_key,
    )
    return train_df.reset_index(drop=True), test_df.reset_index(drop=True)


def randomization_check(train_df: pd.DataFrame) -> None:
    """Print treated vs control balance on train (RCT sanity, like Phase 1)."""
    print("\n=== Randomization / Sanity Check (TRAIN) ===")
    print(f"Train n = {len(train_df):,}")
    print(f"Treatment share = {train_df[TREATMENT_COL].mean():.4f}")

    treated = train_df[train_df[TREATMENT_COL] == 1]
    control = train_df[train_df[TREATMENT_COL] == 0]
    print(
        f"mean({OUTCOME_COL}) | treated = {treated[OUTCOME_COL].mean():.4f} | "
        f"control = {control[OUTCOME_COL].mean():.4f} | "
        f"ATE (naive) = {treated[OUTCOME_COL].mean() - control[OUTCOME_COL].mean():.4f}"
    )

    print("\nCovariate balance (means should be similar):")
    for col in [
        "months_since_account_open",
        "avg_utilization_last_3m",
        "payment_consistency_score",
        "existing_limit",
        "num_active_credit_lines",
    ]:
        t_mean = treated[col].mean()
        c_mean = control[col].mean()
        print(
            f"  {col:28s}  treated={t_mean:.4f}  control={c_mean:.4f}  "
            f"diff={t_mean - c_mean:.4f}"
        )
    print("=== End Sanity Check ===\n")


def save_processed(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    processed_dir: Path = PROCESSED_DIR,
) -> Tuple[Path, Path]:
    processed_dir.mkdir(parents=True, exist_ok=True)
    train_path = processed_dir / "train.parquet"
    test_path = processed_dir / "test.parquet"
    train_df.to_parquet(train_path, index=False)
    test_df.to_parquet(test_path, index=False)
    print(f"Wrote {train_path} ({len(train_df):,} rows)")
    print(f"Wrote {test_path} ({len(test_df):,} rows)")
    return train_path, test_path


def run_data_prep(
    raw_path: Path = RAW_FULL,
    processed_dir: Path = PROCESSED_DIR,
    test_size: float = TEST_SIZE,
    random_state: int = RANDOM_SEED,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Full Phase 2 prep: load -> encode -> split -> save."""
    df = load_modeling_table(raw_path)
    print(f"Loaded modeling table: {len(df):,} rows")
    df = encode_features(df)
    train_df, test_df = train_test_split_stratified(
        df, test_size=test_size, random_state=random_state
    )
    randomization_check(train_df)
    save_processed(train_df, test_df, processed_dir)
    print(f"Feature columns ({len(feature_columns(train_df))}): {feature_columns(train_df)}")
    return train_df, test_df


if __name__ == "__main__":
    run_data_prep()
