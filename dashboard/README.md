# Causal Credit Uplift - Dashboard

Next.js 14 UI for Phase 1 (Hillstrom) and Phase 2 (synthetic credit) results. It only reads the exported JSON. It does not train models.

## Accent

Electric amber (`#F5B942`) on a dark background. Used sparingly for nav, charts, and Persuadables / Sleeping Dogs callouts.

## Refresh data

From the repo root (Python 3.11 venv):

```bash
python export_dashboard_data.py
```

Writes `dashboard/public/data/phase1.json` and `phase2.json` (and copies under `dashboard/data/`).

## Run locally

```bash
cd dashboard
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Deploy

Deploy the `dashboard/` folder to Vercel (Root Directory = `dashboard`). Re-run the export script before deploy so the JSON is current.

GitHub link on the Methodology page:
[Tjay-cmd/causal-credit-uplift](https://github.com/Tjay-cmd/causal-credit-uplift).
