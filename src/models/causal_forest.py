"""Causal forest uplift estimator via econml CausalForestDML.

Choice of estimator
-------------------
We use CausalForestDML rather than LinearDML because Phase 1 is about
learning *heterogeneous* treatment effects (CATE), not a single ATE /
linear CATE surface. CausalForestDML is the standard econml tool for
nonparametric CATE with a binary treatment; the DML wrapper orthogonalizes
outcome and propensity nuisances so CATE estimation is more robust.

Binary outcome note: visit is {0,1}. CausalForestDML still applies — the
final CATE stage is a forest on residualized outcomes. We keep the model
honest about this in evaluation (Qini / uplift-at-k), not by forcing a
classification metric on the CATE itself.

If econml fails to import or fit, we STOP and raise — no silent fallback
to causalml (per Phase 1 requirements).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor

# Flat src/ layout: allow `from data_prep import ...` when run as a script
_SRC_DIR = Path(__file__).resolve().parent.parent
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from data_prep import PROCESSED_DIR, PROJECT_ROOT, feature_columns

OUTPUT_PATH: Path = PROJECT_ROOT / "outputs" / "causal_forest_predictions.csv"


def _import_causal_forest_dml():
    """Import CausalForestDML or fail loudly with install guidance."""
    try:
        from econml.dml import CausalForestDML
    except ImportError as exc:
        raise ImportError(
            "econml is required for CausalForestDML but could not be imported. "
            "Do NOT silently fall back to causalml. Fix the environment, e.g.:\n"
            "  uv pip install econml\n"
            f"Original error: {exc}"
        ) from exc
    return CausalForestDML


def load_processed(
    processed_dir: Path = PROCESSED_DIR,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load train/test parquet produced by data_prep."""
    train_path = processed_dir / "train.parquet"
    test_path = processed_dir / "test.parquet"
    if not train_path.exists() or not test_path.exists():
        raise FileNotFoundError(
            f"Missing processed data. Run data_prep.py first. "
            f"Expected {train_path} and {test_path}."
        )
    return pd.read_parquet(train_path), pd.read_parquet(test_path)


def fit_causal_forest(
    train_df: pd.DataFrame,
    random_state: int = 42,
    n_estimators: int = 100,
) -> Tuple[object, list[str]]:
    """Fit CausalForestDML on train; return (model, feature_names)."""
    CausalForestDML = _import_causal_forest_dml()
    feats = feature_columns(train_df)
    X = train_df[feats].to_numpy()
    T = train_df["treatment"].to_numpy()
    Y = train_df["visit"].to_numpy()

    # Nuisance models: classifier for propensity (binary T), regressor for Y
    model = CausalForestDML(
        model_y=GradientBoostingRegressor(
            n_estimators=50, max_depth=3, random_state=random_state
        ),
        model_t=GradientBoostingClassifier(
            n_estimators=50, max_depth=3, random_state=random_state
        ),
        n_estimators=n_estimators,
        min_samples_leaf=20,
        max_depth=5,
        discrete_treatment=True,
        cv=3,
        random_state=random_state,
    )
    try:
        model.fit(Y, T, X=X)
    except Exception as exc:
        raise RuntimeError(
            "CausalForestDML.fit failed. Per Phase 1 policy we do not fall back "
            "to causalml. Inspect econml / sklearn version compatibility.\n"
            f"Original error: {exc}"
        ) from exc
    return model, feats


def predict_cate(
    model: object,
    test_df: pd.DataFrame,
    feature_names: list[str],
) -> pd.DataFrame:
    """Score test set CATE with the fitted CausalForestDML."""
    X = test_df[feature_names].to_numpy()
    cate = np.asarray(model.effect(X)).reshape(-1)

    return pd.DataFrame(
        {
            "customer_id": test_df["customer_id"].values,
            "true_treatment": test_df["treatment"].values,
            "true_outcome": test_df["visit"].values,
            "predicted_cate": cate,
        }
    )


def run_causal_forest(
    processed_dir: Path = PROCESSED_DIR,
    output_path: Path = OUTPUT_PATH,
    random_state: int = 42,
    n_estimators: int = 100,
) -> pd.DataFrame:
    """End-to-end causal forest fit, predict, and save predictions CSV."""
    train_df, test_df = load_processed(processed_dir)
    model, feats = fit_causal_forest(
        train_df, random_state=random_state, n_estimators=n_estimators
    )
    preds = predict_cate(model, test_df, feats)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    preds.to_csv(output_path, index=False)
    print(
        f"CausalForestDML predictions saved to {output_path} ({len(preds):,} rows)"
    )
    print(
        f"  predicted_cate mean={preds['predicted_cate'].mean():.4f} "
        f"std={preds['predicted_cate'].std():.4f}"
    )
    return preds


if __name__ == "__main__":
    run_causal_forest()
