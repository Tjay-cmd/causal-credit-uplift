# Causal Credit Uplift

Portfolio project on **uplift / causal inference** for credit decisions, not a risk-score classifier.

**Live dashboard:** [https://causal-credit-uplift-ten.vercel.app](https://causal-credit-uplift-ten.vercel.app)

| Phase | What | Why |
|---|---|---|
| **1** | Hillstrom MineThatData email RCT | Try T-learner + CausalForestDML + Qini on real randomized data first |
| **2** | Synthetic credit-limit RCT | Check whether models recover known true CATE, including Sleeping Dogs |
| **Dashboard** | Next.js 14 presentation | Shows the saved results (does not retrain anything) |

## The four-quadrant framework

Uplift is about **who changes because of treatment**, not who already looks good on an outcome model:

| Segment | Effect of treatment | Intuition |
|---|---|---|
| **Persuadables** | CATE > 0 | Only improve *because* you treated them. These are the people you want. |
| **Sure Things** | CATE ≈ 0 | Do well either way. A risk model loves them. Uplift mostly ignores them. |
| **Lost Causes** | CATE ≈ 0 | Do poorly either way. Low outcome score, but treatment still does almost nothing. |
| **Sleeping Dogs** | CATE < 0 | Treatment makes things worse. Bad people to put on a treated list. |

Accuracy and AUC squash all of this into one ranking of predicted outcomes. That ranking pushes Sure Things to the top and usually misses both Persuadables and Sleeping Dogs.

## Phase 1 - Hillstrom (real RCT)

I started with real randomized email data (Mens E-Mail vs No E-Mail, outcome = visit) so I could check the methods before building synthetic credit data.

| Model | Qini | Uplift@10% | Uplift@30% | Uplift@50% |
|---|---|---|---|---|
| **T-learner** | **7.74** | 0.116 | **0.094** | 0.080 |
| CausalForestDML | 6.26 | **0.153** | 0.086 | 0.081 |

- **Ranking vs tight budget:** T-learner wins overall Qini. CausalForestDML does better if you only treat the top 10%.
- **Model disagreement:** the two models only share **58.1%** of their top-decile customers (Jaccard **0.409**). So CATE rankings are less stable than a normal risk score ranking.
- **Sleeping Dogs candidate:** about **1.4%** of the test set got a negative predicted CATE, and those people were concentrated in high-spend / Rural / Multichannel groups. Small sample, so I treat it as a clue rather than a hard fact. That idea shaped Phase 2 Sleeping Dogs (too much contact / channel saturation).

## Phase 2 - Synthetic credit RCT

Then I built a synthetic credit-limit RCT with known segments and true CATE, using what Phase 1 suggested (outcome = `good_standing` at 3 months).

| Segment | Mean true CATE | Role |
|---|---|---|
| Persuadables | **+0.175** | Benefit from a limit increase |
| Sure Things | ~0 | Fine either way |
| Lost Causes | ~0 | Struggle either way |
| Sleeping Dogs | **-0.125** | Treatment backfires (contact saturation) |

| Model | PEHE (lower is better) | corr(pred, true CATE) |
|---|---|---|
| T-learner | 0.0037 | 0.847 |
| **CausalForestDML** | **0.0015** | **0.927** |

**If you target the top decile by predicted CATE, who do you actually hit?**

| Model | % true Persuadables | % true Sleeping Dogs |
|---|---|---|
| T-learner | 95.5% | 0.1% |
| **CausalForestDML** | **100%** | **0.0%** |

**There is no single winner.** T-learner is better on **Qini** (overall ranking / who to put on a list). CausalForestDML is better on **PEHE** and keeps more **Sleeping Dogs** out of the top decile (safer if you care about effect size and not harming people).

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

Open http://localhost:3000. The UI reads `dashboard/public/data/*.json` only.

## Repo structure

| Path | Contents |
|---|---|
| `src/` | Phase 1 prep, models, evaluation |
| `phase2_synthetic_credit/` | Synthetic DGP, models, CATE recovery |
| `dashboard/` | Next.js results UI |
| `notebooks/` | End-to-end walkthroughs |
| `outputs/` | Phase 1 summary artifacts |
