# Causal Credit Uplift — Dashboard

Next.js 14 presentation layer for Phase 1 (Hillstrom) and Phase 2 (synthetic credit) results. Reads static JSON only — does not train models.

## Accent

**Electric amber (`#F5B942`)** on near-black: uplift work is about spotting a hidden incremental signal that risk scoring alone would miss. Used sparingly (active nav, key charts, Sleeping Dogs / Persuadables callouts).

## Refresh data

From the repo root (Python 3.11 venv):

```bash
python export_dashboard_data.py
```

Writes `dashboard/public/data/phase1.json` and `phase2.json` (and mirrors under `dashboard/data/`).

## Run locally

```bash
cd dashboard
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Deploy

Static-friendly App Router pages. Deploy the `dashboard/` folder to Vercel (Root Directory = `dashboard`). Re-run the export script before deploy so JSON is current.

GitHub link on the Methodology page points to
[Tjay-cmd/causal-credit-uplift](https://github.com/Tjay-cmd/causal-credit-uplift).
