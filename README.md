# Molecule to Market AI

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

Set `ANTHROPIC_API_KEY` to have Claude draft the brand plan's strategy narrative,
the AI Co-Pilot chat, AI-drafted brand-name candidates (Modules 12/13), and the
visual aid brief's punchline/messaging (Module 15). Without a key, every one of
these degrades honestly to a labeled deterministic template or an explicit
"needs an API key" message — never a fabricated stand-in for real AI output.

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

## Drug Intelligence module

Normalised drug records — identity, clinical narrative, interactions,
comparison, and a separated PMT analysis layer — served from the same FastAPI
backend. Cache-first: a search hits the database and only reaches an upstream
when nothing is stored.

Sources go through an adapter interface (`backend/app/data_sources/`), so the
application keeps working when any one upstream is unavailable:

| Source | Status |
| --- | --- |
| openFDA | Enabled — public FDA API, plus bulk corpus load |
| Drugs.com | Disabled without a licensed feed (`DRUGS_COM_API_KEY`) |
| Manual import | Enabled — team-entered records |

**Drugs.com is never scraped.** It returns HTTP 403 to programmatic requests,
its terms prohibit automated extraction, and its content is copyrighted — and
scraped text could not be cited in an MLR-reviewed plan regardless. The adapter
targets the licensed Drugs.com/DrugBank feed and activates on configuration.
For patient-reported problems the application uses FDA FAERS instead.

The catalogue can be bulk-loaded from openFDA's published partitions — the
live API caps `skip` at 25,000 records and cannot reach the ~137k marketed
products or ~262k labels the FDA publishes:

```bash
cd backend && ./.venv/bin/python scripts/ingest_openfda_bulk.py --limit 5000
```

Full documentation: [docs/DRUG_INTELLIGENCE.md](docs/DRUG_INTELLIGENCE.md).

## Research evidence (PubMed)

Module 2 answers "what has been published on this molecule" — the whole
bibliography, not a sample of it.

The literature is paged through NCBI's E-utilities history server and cached
locally, so a molecule loads instantly on every subsequent visit and keeps
working when NCBI is briefly unreachable. Abstracts are fetched alongside the
bibliographic record, so a reviewer can judge relevance without leaving the app.

**Two counts, never merged.** The header shows what PubMed indexes next to what
is loaded — `5,158 indexed in PubMed · 100 shown`. A partial fetch can never
read as the whole literature. **Fetch entire corpus** pulls the rest in the
background; **Load more** pages through what is already cached.

By default the search is the whole molecule. The project's indication is an
opt-in narrowing (the `whole molecule` / `narrowed to indication` toggle) —
filtering rosuvastatin to "Dyslipidaemia" takes 5,158 papers down to 76, which
is a different question and should be asked deliberately.

Combinations are searched as an AND of their components, and every term is
matched against both title/abstract and MeSH, so papers indexed only under the
MeSH heading are not silently dropped.

### What is never inferred

- An unparseable publication date is stored as NULL and rendered `n.d.` — never
  defaulted to a year.
- Evidence tiers stay labelled *candidate*. PubMed's publication type is a
  cataloguing decision, not a methodological appraisal.
- Endpoints, effect sizes, and p-values are not machine-extracted from PubMed
  metadata. Cards say so rather than showing an empty field as a result.

### Rate limits

NCBI allows 3 requests/second anonymously, 10 with a free API key. The key only
changes how fast the literature loads, never how much of it is available. Set
`NCBI_API_KEY` to use one — get it from your NCBI account settings.

```bash
# Optional. Roughly triples corpus fetch speed.
NCBI_API_KEY=...
```

## Regulatory intelligence (openFDA)

Module 4 reads live from openFDA rather than a curated table, so the US block is
populated for essentially any molecule marketed in the States: innovator brand,
first approval year, application numbers, indications, boxed warnings, warnings,
and contraindications — all quoted from the FDA structured product label.

India has no machine-readable approvals API. Where an Indian market extract is
loaded, the CDSCO block reports measured market presence from it — *"Marketed in
India — 573 brand(s) recorded, 149 companies, 3,258.67 INR Cr, MAT AUG'24"* —
worded as **marketed**, not **approved**, because only CDSCO can say the latter.

An agency with no connected source says exactly that and links its register.
That is deliberately not the same as "not approved": the application does not
assert a regulatory status it cannot source.

```bash
# Optional. Raises the openFDA request ceiling from 1,000/day to 120,000/day.
# It does NOT lift the skip=25,000 paging cap — whole-corpus loading comes from
# the bulk partitions instead (see the Drug Intelligence module).
OPENFDA_API_KEY=...
```

## Market Intelligence (secondary data)

Public sources answer *what molecules exist*. They do not answer *who am I
competing against in this market* — that lives in a syndicated audit extract a
brand team licenses. Drop one in and the competitor module works for every
molecule it covers.

**What it gives you, per molecule:** every marketed brand with its company,
value, market share, and growth; corporate share of the molecule; and rival
molecules in the same therapeutic group.

### Loading an extract

Two routes, same result:

* **Drag it into a project** under *Secondary Data*. Any `.xlsx`/`.csv` whose
  header carries molecule, brand, and a MAT value column is parsed automatically
  in the background; the file stays downloadable either way. Nothing else to do.
* **Point the API at a file already on the server** — better for a large base
  extract that is impractical to push through a browser:

```bash
curl -X POST http://localhost:8000/api/market/ingest/path \
  -H 'Content-Type: application/json' \
  -d '{"path":"~/Reports/IMS TSA base file.xlsx","source_label":"IQVIA/IMS TSA","market":"India","value_unit":"INR Cr"}'
```

Column names are matched against alias lists (`MOLECULE_DESC`/`MOLECULE`,
`BRANDS`/`BRAND`, `COMPANY`/`CORPORATE`, …), so IQVIA/IMS, PharmaTrac, and AWACS
layouts all load without configuration. Salt forms are normalised
(`ROSUVASTATIN CALCIUM` → `ROSUVASTATIN`) and combinations stay searchable from
either ingredient, so `EMPAGLIFLOZIN + LINAGLIPTIN` shows up as a competitor for
Empagliflozin.

### Rules that keep the numbers honest

* **One period answers a molecule.** Figures are never aggregated across
  datasets — MAT JUN'26 plus MAT AUG'24 is not a market, it is a double-count.
  Each molecule reads from the most recent extract that carries it, and the
  panel states which file and period that was. Older extracts still answer
  molecules the newer one does not cover.
* **Re-uploading a file replaces it.** Same filename, newer period, one
  transaction — a refresh never leaves two periods live at once.
* **Sales facts and strategy stay separate.** Market rows carry value, share,
  growth, and company. They leave positioning, claims, and messaging blank,
  because an audit extract measures what sold, not how it was detailed. The 2×2
  positioning quadrant plots only curated rows for the same reason.
* **No data means no data.** A molecule absent from every extract returns an
  explicit empty state, never an estimate.

### What does not load

Chart-heavy report decks (IPM/PharmaTrac monthly PDFs, IQVIA MFR) carry
market context, not brand-level tables. Store them as project attachments for
citation — they are not parsed into competitor rows, because numbers scraped
off a chart image cannot be traced back to a source row under MLR review.

### Endpoints

| Endpoint | Returns |
| --- | --- |
| `GET /api/market/datasets` | Every ingested extract with row/brand/company counts |
| `GET /api/market/molecule?molecule=` | Size, brands, companies, and class rivals in one call |
| `GET /api/market/brands?molecule=` | Brand table with share and growth |
| `GET /api/market/companies?molecule=` | Corporate share |
| `GET /api/market/class?molecule=` | Rival molecules in the same therapeutic group |
| `GET /api/market/search?q=` | Free-text lookup across brand, molecule, company |
| `POST /api/market/ingest/path` | Ingest a file already on the server |
| `DELETE /api/market/datasets/{id}` | Remove a dataset and its rows |

## Known limitations

Read these before using output in a real brand plan.

- **Authentication is a shared token, not user accounts.** Setting `API_ACCESS_TOKEN` requires every request (except `/health` and `/`) to carry it via `X-API-Key` or `Authorization: Bearer`. The deployed instance generates one automatically (`render.yaml`'s `generateValue: true`) and **refuses to start in production without one** (`security.py:enforce_startup_policy`). Left unset, every endpoint is open — acceptable on localhost only. This is a single shared secret, not per-user identity: adequate for one brand team behind a token, not for distinguishing who did what. Add SSO or per-user accounts before this serves more than one team.
- **Claude drafts strategy only, never clinical claims.** With `ANTHROPIC_API_KEY` set, Claude Opus 5 drafts the plan's narrative sections grounded in the molecule and evidence data the app already fetched. It is instructed never to produce effect sizes, p-values, hazard ratios, comparative superiority, safety assurances, or dosing — and every generated field is screened by `services/compliance.py` before it reaches the plan. Text that trips the screen is withheld, the template text is kept, and a review flag is raised. Without a key the app uses the deterministic template and every other module works unchanged. `mlr_compliance_signoff_ready` stays `false` either way.
- **Curated *strategy* depth covers four molecules.** Empagliflozin, Semaglutide, Pembrolizumab, and Apixaban have hand-checked evidence, trials, and label data. Other molecules fall back to live PubChem/PubMed/ClinicalTrials.gov lookups, which return bibliographic records rather than claim-ready endpoint data. Curated *strategy* narratives (positioning, claims, messaging) exist only for Empagliflozin — but the measured competitor set now comes from ingested market data for any molecule the extract covers (see Market Intelligence below).
- **Market figures are only as current as the extract you loaded.** Share, growth, and market size come from the newest ingested file that covers the molecule — the panel names that file and period. Nothing is extrapolated forward from it.
- **Forecast defaults are planning heuristics, not market research.** Prescriber pool sizes, regional revenue splits, scenario uptake multipliers, and the 6.8% therapy CAGR are illustrative defaults. Replace them with sourced assumptions before the numbers inform a decision.
- **Nothing here is MLR-approved.** `mlr_compliance_signoff_ready` is always `false`. Every claim needs evidence mapping, label verification, and fair-balance review before external use.

## CI

The repo includes GitHub Actions workflows under `.github/workflows` for CI and image publishing.

## Developer

Built by [Animesh Mishra](https://github.com/Animesh1324) — [animesh.pm17@iihmr.in](mailto:animesh.pm17@iihmr.in) — [LinkedIn](https://www.linkedin.com/in/animeshmishra-pm17).

