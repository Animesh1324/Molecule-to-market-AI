# Pharma BrandPlan AI

This project is a FastAPI + Next.js application for pharmaceutical brand planning, scientific intelligence, competitor analysis, and launch planning.

## Architecture

- Backend: FastAPI application in `backend/app`
- Frontend: Next.js app in `frontend/src`
- Database: SQLite file stored in `backend/data/brandplan.db`
- Test stack: `pytest` for backend, `jest` for frontend

## Local setup

1. Create the backend virtual environment and install dependencies:

```bash
cd /Users/animeshmishra/Molecule\ to\ market\ AI
python3 -m venv backend/.venv
source backend/.venv/bin/activate
pip install -r backend/requirements.txt
```

2. Copy environment examples if you want custom settings:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

3. Start the backend:

```bash
cd backend
python run.py
```

The API runs at `http://localhost:8000` by default.

4. In a second terminal, start the frontend:

```bash
cd frontend
npm install
npm run dev
```

The app runs at `http://localhost:3000` and uses `NEXT_PUBLIC_API_BASE` to reach the backend.

## Environment variables

Backend:

- `APP_ENV` (`development`/`production`)
- `PORT` (default `8000`)
- `CORS_ORIGINS` (comma-separated allowed frontend origins). **Must be set in production** — the localhost fallback will block your deployed frontend.
- `DATABASE_URL` (optional). Blank uses the local SQLite file at `backend/app/data/brandplan.db`. Set a PostgreSQL URL for any host with an ephemeral filesystem, or all saved projects and brand plans are lost on restart.

Frontend:

- `NEXT_PUBLIC_API_BASE` (default `http://localhost:8000`)
- `NEXT_PUBLIC_APP_ENV`

`NEXT_PUBLIC_*` values are inlined into the client bundle **at build time**, not
read at runtime. They must be set before `npm run build` runs — the Docker image
takes them as build args.

## Core workflows

- Create a project from the home page
- Open a project workspace
- Review molecule intelligence, evidence, trials, regulatory, trademark, competitor, and forecast modules
- Generate a brand plan and creative assets
- Export DOCX/PPTX/XLSX artifacts from the report center

## Testing

```bash
cd backend
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q

cd ../frontend
npm test
npm run build
```

Tests run against a temporary database (see `backend/tests/conftest.py`), so
they never touch your working `brandplan.db`.

## Docker

This repository includes Dockerfiles for both services. The local compose file is set up for development:

```bash
cd /Users/animeshmishra/Molecule\ to\ market\ AI
docker compose up --build
```

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:3000`

## Staging deployment (Render)

The blueprint in [render.yaml](render.yaml) provisions a managed Postgres
instance plus both services. Connect the repo in Render and deploy the
blueprint; the backend's `DATABASE_URL` is wired to the database automatically.

After the first deploy, update these to your real service hostnames:

- backend `CORS_ORIGINS` → your frontend URL
- frontend `NEXT_PUBLIC_API_BASE` → your backend URL

Then redeploy the frontend, since `NEXT_PUBLIC_API_BASE` is baked in at build time.

## Deployment notes

- Set `DATABASE_URL` to managed PostgreSQL for any real deployment. The SQLite fallback lives on the container filesystem and is wiped on every restart.
- Keep secrets in the deployment platform's secrets manager instead of committing them.
- Set `CORS_ORIGINS` to the exact production frontend host(s) rather than wildcard origins.
- Use a production build of the Next.js app and run it behind a reverse proxy or container orchestration layer.

## Known limitations

Read these before using output in a real brand plan.

- **No authentication.** Every endpoint is open. Anyone who can reach the URL can read, create, and overwrite every project and brand plan. Put it behind SSO, a VPN, or an authenticating proxy before exposing it beyond your own machine.
- **The brand plan generator is a template, not an AI.** `ai_orchestrator.py` fills a fixed 12-section scaffold with your molecule and indication. It deliberately emits `SOURCE_NEEDED` placeholders instead of claims. No model is called; `services/prompts.py` is an unused prompt library kept for future work.
- **Curated depth covers four molecules.** Empagliflozin, Semaglutide, Pembrolizumab, and Apixaban have hand-checked evidence, trials, and label data. Other molecules fall back to live PubChem/PubMed/ClinicalTrials.gov lookups, which return bibliographic records rather than claim-ready endpoint data. Competitor landscapes exist only for Empagliflozin; others return an explicit gap.
- **Forecast defaults are planning heuristics, not market research.** Prescriber pool sizes, regional revenue splits, scenario uptake multipliers, and the 6.8% therapy CAGR are illustrative defaults. Replace them with sourced assumptions before the numbers inform a decision.
- **Nothing here is MLR-approved.** `mlr_compliance_signoff_ready` is always `false`. Every claim needs evidence mapping, label verification, and fair-balance review before external use.

## CI

The repo includes GitHub Actions workflows under `.github/workflows` for CI and image publishing.

