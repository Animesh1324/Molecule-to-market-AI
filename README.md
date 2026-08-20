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

## AI drafting (optional)

Set `ANTHROPIC_API_KEY` to have Claude draft the brand plan's strategy narrative.

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

What Claude is and is not allowed to write:

| Claude drafts | Claude never writes |
| --- | --- |
| Positioning rationale, segmentation, launch sequencing, KOL and channel strategy, the open questions a brand team must close | Effect sizes, p-values, hazard/odds ratios, confidence intervals, comparative superiority, safety assurances, dose/strength/route |

Three layers keep that boundary:

1. **Grounding** — the prompt carries only facts the app already fetched (PubChem molecule profile, PubMed citations on file). Claude is told to work from those and flag gaps as `[SOURCE NEEDED: ...]` rather than filling them from memory.
2. **Screening** — every drafted field is scanned by `services/compliance.py`. A field containing a clinical claim is discarded, the template text is kept, and a flag appears in `ai_review_flags` and in the UI.
3. **No signoff** — `mlr_compliance_signoff_ready` is forced to `false` on every drafted plan.

Drafting degrades safely. A missing key, rate limit, refusal, or timeout returns the deterministic template with `ai_status: "drafting_failed"` — the endpoint never errors. Disable it with `AI_DRAFTING=off`, or per request with `?ai=false`.

Check whether drafting is live:

```bash
curl -s http://localhost:8000/ | python3 -m json.tool
```

## Known limitations

Read these before using output in a real brand plan.

- **No authentication.** Every endpoint is open. Anyone who can reach the URL can read, create, and overwrite every project and brand plan. Put it behind SSO, a VPN, or an authenticating proxy before exposing it beyond your own machine.
- **Claude drafts strategy only, never clinical claims.** With `ANTHROPIC_API_KEY` set, Claude Opus 5 drafts the plan's narrative sections grounded in the molecule and evidence data the app already fetched. It is instructed never to produce effect sizes, p-values, hazard ratios, comparative superiority, safety assurances, or dosing — and every generated field is screened by `services/compliance.py` before it reaches the plan. Text that trips the screen is withheld, the template text is kept, and a review flag is raised. Without a key the app uses the deterministic template and every other module works unchanged. `mlr_compliance_signoff_ready` stays `false` either way.
- **Curated depth covers four molecules.** Empagliflozin, Semaglutide, Pembrolizumab, and Apixaban have hand-checked evidence, trials, and label data. Other molecules fall back to live PubChem/PubMed/ClinicalTrials.gov lookups, which return bibliographic records rather than claim-ready endpoint data. Competitor landscapes exist only for Empagliflozin; others return an explicit gap.
- **Forecast defaults are planning heuristics, not market research.** Prescriber pool sizes, regional revenue splits, scenario uptake multipliers, and the 6.8% therapy CAGR are illustrative defaults. Replace them with sourced assumptions before the numbers inform a decision.
- **Nothing here is MLR-approved.** `mlr_compliance_signoff_ready` is always `false`. Every claim needs evidence mapping, label verification, and fair-balance review before external use.

## CI

The repo includes GitHub Actions workflows under `.github/workflows` for CI and image publishing.

