# Causal Credit Uplift

Portfolio project on **uplift / causal inference** for credit decisions — not a risk-score classifier.

**Live dashboard:** [DASHBOARD_URL_HERE]  
*(Deploy `dashboard/` to Vercel, then replace this placeholder.)*

| Phase | What | Why |
|---|---|---|
| **1** | Hillstrom MineThatData email RCT | Prove T-learner + CausalForestDML + Qini methodology on real randomized data |
| **2** | Synthetic credit-limit RCT | Recover known ground-truth CATE; operational top-decile targeting vs Sleeping Dogs |
| **Dashboard** | Next.js 14 presentation | Static JSON visualization of results (no retraining) |

## The four-quadrant framework

Uplift targets **who changes because of treatment**, not who looks “good” on an outcome model:

| Segment | Effect of treatment | Intuition |
|---|---|---|
| **Persuadables** | CATE > 0 | Respond *because* of the action — the targeting prize |
| **Sure Things** | CATE ≈ 0 | Succeed either way — risk models love them; uplift does not |
| **Lost Causes** | CATE ≈ 0 | Fail either way — low outcome rank, still ~zero incremental effect |
| **Sleeping Dogs** | CATE < 0 | Treatment backfires — the costly mistake in a treated list |

Classification metrics (accuracy / AUC) collapse these into one ranking of predicted outcomes. That prefers Sure Things and misses both Persuadables and Sleeping Dogs.

## Phase 1 — Hillstrom (real RCT)

Real randomized email marketing data (Mens E-Mail vs No E-Mail; outcome = visit) used to prove the methodology before touching synthetic credit data.

| Model | Qini | Uplift@10% | Uplift@30% | Uplift@50% |
|---|---|---|---|---|
| **T-learner** | **7.74** | 0.116 | **0.094** | 0.080 |
| CausalForestDML | 6.26 | **0.153** | 0.086 | 0.081 |

- **Ranking vs tight budget:** T-learner wins overall Qini; CausalForestDML is stronger at a very tight top-10% budget.
- **Model disagreement:** only **58.1%** top-decile customer overlap between models (Jaccard **0.409**) — CATE lists are less stable than typical risk rankings.
- **Sleeping Dogs candidate:** concentrated negative predicted CATE in **1.4%** of the test set (high-spend / Rural / Multichannel) — treated as a plausible low-sample signal, not a confirmed population effect; it informed Phase 2’s contact-saturation Sleeping Dogs design.

## Phase 2 — Synthetic credit RCT

Synthetic credit-limit RCT with known latent segments and true CATE, grounded in Phase 1’s findings (outcome = `good_standing` at 3 months).

| Segment | Mean true CATE | Role |
|---|---|---|
| Persuadables | **+0.175** | Benefit from limit increase |
| Sure Things | ~0 | Succeed either way |
| Lost Causes | ~0 | Fail either way |
| Sleeping Dogs | **−0.125** | Treatment backfires (contact saturation) |

| Model | PEHE (↓ better) | corr(pred, true CATE) |
|---|---|---|
| T-learner | 0.0037 | 0.847 |
| **CausalForestDML** | **0.0015** | **0.927** |

**If you target the top decile by predicted CATE, who do you actually reach?**

| Model | % true Persuadables | % true Sleeping Dogs |
|---|---|---|
| T-learner | 95.5% | 0.1% |
| **CausalForestDML** | **100%** | **0.0%** |

**Tradeoff (no single winner):** T-learner wins **Qini ranking** (targeting-list / approval-curve quality). CausalForestDML wins **PEHE** and **Sleeping Dogs contamination safety** (individual effect-size estimation and harm avoidance in the treated list).

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

## Repo structure

| Path | Contents |
|---|---|
| `src/` | Phase 1 prep, models, evaluation |
| `phase2_synthetic_credit/` | Synthetic DGP, models, CATE recovery |
| `dashboard/` | Next.js results UI |
| `notebooks/` | End-to-end walkthroughs |
| `outputs/` | Phase 1 summary artifacts |
