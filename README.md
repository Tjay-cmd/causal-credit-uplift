# Causal Credit Uplift

Portfolio project on **uplift / causal inference** for credit decisions — not a risk-score classifier.

| Phase | What | Why |
|---|---|---|
| **1** | Hillstrom MineThatData email RCT | Prove T-learner + CausalForestDML + Qini methodology on real randomized data |
| **2** | Synthetic credit-limit RCT | Recover known ground-truth CATE; operational top-decile targeting vs Sleeping Dogs |
| **Dashboard** | Next.js 14 presentation | Static JSON visualization of results (no retraining) |

## Quick start (analysis)

```bash
# Python 3.11
uv venv --python 3.11 .venv
# or: python -m venv .venv
.venv\Scripts\activate          # Windows
uv pip install -r requirements.txt

# Phase 1
$env:PYTHONPATH = "$PWD\src"
python src\data_prep.py
python src\models\t_learner.py
python src\models\causal_forest.py
python src\evaluation\uplift_metrics.py
python src\evaluation\segment_profile.py

# Phase 2
python phase2_synthetic_credit\src\generate_data.py
python phase2_synthetic_credit\src\validate_generation.py
$env:PYTHONPATH = "$PWD\phase2_synthetic_credit\src"
python phase2_synthetic_credit\src\data_prep.py
python phase2_synthetic_credit\src\models\t_learner.py
python phase2_synthetic_credit\src\models\causal_forest.py
python phase2_synthetic_credit\src\evaluation\uplift_metrics.py
python phase2_synthetic_credit\src\evaluation\cate_recovery.py
python phase2_synthetic_credit\src\evaluation\segment_recovery_check.py
```

## Dashboard

```bash
python export_dashboard_data.py
cd dashboard
npm install
npm run dev
```

Open http://localhost:3000 — data from `dashboard/public/data/*.json` only.

## Repo

https://github.com/Tjay-cmd/causal-credit-uplift
