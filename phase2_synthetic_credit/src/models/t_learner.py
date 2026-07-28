"""T-learner for Phase 2 synthetic credit good_standing outcome."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Literal, Tuple

import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression

_SRC_DIR = Path(__file__).resolve().parent.parent
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from data_prep import OUTCOME_COL, PROCESSED_DIR, PROJECT_ROOT, feature_columns

OUTPUT_PATH: Path = PROJECT_ROOT / "outputs" / "t_learner_predictions.csv"
ModelName = Literal["gbm", "logistic"]


def _make_base_model(model_name: ModelName, random_state: int = 42):
    if model_name == "gbm":
        return GradientBoostingClassifier(
            n_estimators=100,
            max_depth=3,
            learning_rate=0.1,
            random_state=random_state,
        )
    if model_name == "logistic":
        return LogisticRegression(max_iter=2000, random_state=random_state)
    raise ValueError(f"Unknown model_name={model_name!r}; use 'gbm' or 'logistic'.")


def load_processed(
    processed_dir: Path = PROCESSED_DIR,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    train_path = processed_dir / "train.parquet"
    test_path = processed_dir / "test.parquet"
    if not train_path.exists() or not test_path.exists():
        raise FileNotFoundError(
            f"Missing processed data. Run data_prep.py first. "
            f"Expected {train_path} and {test_path}."
        )
    return pd.read_parquet(train_path), pd.read_parquet(test_path)


def fit_t_learner(
    train_df: pd.DataFrame,
    model_name: ModelName = "gbm",
    random_state: int = 42,
) -> Tuple[object, object, list[str]]:
    feats = feature_columns(train_df)
    treated = train_df[train_df["treatment"] == 1]
    control = train_df[train_df["treatment"] == 0]
    if treated.empty or control.empty:
        raise ValueError("Train set must contain both treatment and control units.")

    mu1 = _make_base_model(model_name, random_state=random_state)
    mu0 = _make_base_model(model_name, random_state=random_state)
    mu1.fit(treated[feats], treated[OUTCOME_COL])
    mu0.fit(control[feats], control[OUTCOME_COL])
    return mu1, mu0, feats


def predict_cate(
    mu1: object,
    mu0: object,
    test_df: pd.DataFrame,
    feature_names: list[str],
) -> pd.DataFrame:
    p1 = mu1.predict_proba(test_df[feature_names])[:, 1]
    p0 = mu0.predict_proba(test_df[feature_names])[:, 1]
    return pd.DataFrame(
        {
            "customer_id": test_df["customer_id"].values,
            "true_treatment": test_df["treatment"].values,
            "true_outcome": test_df[OUTCOME_COL].values,
            "predicted_cate": p1 - p0,
            "p_outcome_treated": p1,
            "p_outcome_control": p0,
        }
    )


def run_t_learner(
    processed_dir: Path = PROCESSED_DIR,
    output_path: Path = OUTPUT_PATH,
    model_name: ModelName = "gbm",
    random_state: int = 42,
) -> pd.DataFrame:
    train_df, test_df = load_processed(processed_dir)
    mu1, mu0, feats = fit_t_learner(
        train_df, model_name=model_name, random_state=random_state
    )
    preds = predict_cate(mu1, mu0, test_df, feats)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    preds.to_csv(output_path, index=False)
    print(
        f"T-learner ({model_name}) predictions saved to {output_path} "
        f"({len(preds):,} rows)"
    )
    print(
        f"  predicted_cate mean={preds['predicted_cate'].mean():.4f} "
        f"std={preds['predicted_cate'].std():.4f}"
    )
    return preds


if __name__ == "__main__":
    import sys as _sys

    name: ModelName = "gbm"
    if len(_sys.argv) > 1:
        arg = _sys.argv[1].lower()
        if arg not in ("gbm", "logistic"):
            raise SystemExit("Usage: python t_learner.py [gbm|logistic]")
        name = arg  # type: ignore[assignment]
    run_t_learner(model_name=name)
