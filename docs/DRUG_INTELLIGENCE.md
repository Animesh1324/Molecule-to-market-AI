# Drug Intelligence Module

Adds normalised drug information — identity, clinical narrative, interactions,
comparison, and a separated PMT analysis layer — to the existing FastAPI
application. **FastAPI remains the backend.** Nothing was migrated, replaced,
or rewritten; this module is additive and every pre-existing route, model, and
test still works.

## Architecture

```
                 ┌──────────────── FastAPI (unchanged core) ────────────────┐
                 │                                                          │
  HTTP  ───────► │  api/drugs.py                                            │
  (token-        │      │                                                   │
   protected)    │      ├── services/drug_search_service.py   ── search      │
                 │      ├── services/drug_compare_service.py  ── compare     │
                 │      ├── services/drug_pmt_service.py      ── PMT layer   │
                 │      └── services/drug_ingestion_service.py               │
                 │                    │                                     │
                 │                    │  timeout · circuit breaker           │
                 │                    ▼                                     │
                 │           data_sources/  (adapter interface)              │
                 │             ├── OpenFDASource      enabled                │
                 │             ├── DrugsComSource     licensed feed only     │
                 │             └── ManualImportSource enabled                │
                 │                    │                                     │
                 │                    ▼                                     │
                 │           repositories/drug_repository.py                 │
                 │                    │                                     │
                 │                    ▼                                     │
                 │      db/drug_models.py → same Base / engine / session     │
                 │      drugs · drug_sources · drug_interactions · log       │
                 └──────────────────────────────────────────────────────────┘
                                      │
                              Next.js frontend (unchanged design system)
```

Request flow is **cache-first**: a search hits the database, and only reaches an
upstream when nothing is stored. Ingested records are persisted, so the second
search for the same drug makes no outbound call.

## Data source policy

| Source | Status | Access |
|---|---|---|
| **openFDA** | Enabled | Public FDA API (`api.fda.gov`). No key required. Supplies label narrative and product identity. |
| **Drugs.com** | **Disabled without a licence** | Licensed data feed only. See below. |
| **Manual import** | Enabled | Records entered by the team, stamped `confidence: user-entered`. |

### Why Drugs.com is not scraped

Drugs.com returns **HTTP 403** to programmatic requests — an explicit technical
access control. Its terms prohibit automated extraction, and its monographs and
user reviews are copyrighted. Independently of the legal position, content
copied from a consumer drug site cannot be cited in an MLR-reviewed brand plan,
so scraped text would fail review even if it were obtained.

The adapter is therefore written against the **licensed Drugs.com / DrugBank
feed**. It stays disabled until `DRUGS_COM_API_KEY` is set, at which point
ingestion becomes a configuration change rather than a rewrite. `fetch()`
without a key raises `SourceNotPermitted`, which the ingestion service records
as a permanent skip. No configuration causes the website to be scraped.

For patient-reported problems and adherence signal, the application uses **FDA
FAERS** (`/api/intelligence/patient-experience`) — structured, free, citable,
and it covers combinations.

## Database schema

| Table | Purpose |
|---|---|
| `drugs` | One normalised drug. Unique on `(generic_name, brand_name)`, both case-canonicalised. `search_blob` is a maintained lower-cased haystack so search is one indexed `LIKE`. |
| `drug_sources` | Provenance, one row per source per drug. Carries `source_url`, `source_identifier`, `data_version`, `published_at`, `confidence`, `retrieved_at`. |
| `drug_interactions` | Pairwise interactions, stored alphabetically ordered so A–B and B–A cannot both exist. |
| `drug_ingestion_log` | Every refresh attempt, so a silently failing source is visible. |

List-valued fields (ingredients, strengths, forms, routes) are JSON columns:
they are always read and written whole, so join tables would add cost without
buying anything.

**Merge policy:** a newly fetched non-empty value wins; an empty one never
erases a value another source supplied. Re-ingesting from a thin label cannot
blank good data.

## API

All routes sit behind the existing `require_access` token dependency.

| Method | Path | Notes |
|---|---|---|
| `GET` | `/api/drugs` | Paginated list; `drug_class` filter |
| `GET` | `/api/drugs/search?q=` | Cache-first, ingests on demand |
| `GET` | `/api/drugs/{id}` | Single drug |
| `GET` | `/api/drugs/{id}/sources` | Provenance rows |
| `GET` | `/api/drugs/{id}/interactions` | Pairwise interactions |
| `GET` | `/api/drugs/by-brand/{name}` | |
| `GET` | `/api/drugs/by-generic/{name}` | |
| `GET` | `/api/drugs/class/{drug_class}` | Paginated |
| `POST` | `/api/drugs/compare` | Body: `drug_a`, `drug_b` |
| `POST` | `/api/drugs/manual` | Hand-entered record |
| `POST` | `/api/drugs/refresh` | Re-ingest, max 25 queries per call |
| `GET` | `/api/drugs/refresh/history` | Ingestion audit |
| `GET` | `/api/drugs/sources/registry` | Adapters and access policy |
| `GET` | `/api/drugs/pmt/{molecule}` | Generated analysis, labelled |

Pagination returns `{items, total, page, page_size, has_more}`. Page size is
capped at 100 (422 above it). Unknown ids return 404; an empty `q` returns 422.

Literal paths are declared before the dynamic `/{drug_id}` route so `/search`,
`/compare`, `/manual`, and `/refresh` cannot be captured as drug ids.

## Search

Tolerates case, surrounding whitespace, salt suffixes (`metformin
hydrochloride` → `metformin`), INN/USAN spelling (`paracetamol` →
`acetaminophen`), class shorthand (`GLP-1`, `SGLT2`, `PPI`, `PD-1`), and
fixed-dose combinations, which are searched component-wise.

Results are **relevance-ranked**: exact name → name prefix → name substring →
matched on class/ingredient/strength. Without this, searching `Beta` returned
every beta-blocker ahead of the drug actually named Beta.

## PMT analysis layer

`/api/drugs/pmt/{molecule}` returns observations derived from stored records:
positioning, differentiation candidates, advantages, disadvantages, target
patient and physician segments, and evidence gaps.

Every response carries `analysis_type: "AI/Software Analysis"` and a disclaimer
stating it is generated by the application, is not a statement from any
regulator or data provider, and is not a clinical claim. It is a separate
endpoint from the drug profile precisely so a generated inference can never be
mistaken for a source fact.

## Reliability

Each source is isolated. Per-source timeout (25 s), and a circuit breaker opens
after 3 consecutive failures with a 5-minute cooldown, so a dead upstream is
skipped rather than retried on every request. `SourceNotPermitted` is treated as
permanent — no retry, no breaker.

A source that is down, rate-limited, slow, unlicensed, returns malformed JSON,
or contains a programming bug produces a failed `SourceOutcome` and a log row.
It never raises to the caller and never fails the application. Tests cover each
of those paths.

## Security

Every drug route is protected by the existing shared-token dependency — no new
authentication surface. `POST /api/drugs/refresh` drives outbound requests, so
it is token-protected and capped at 25 queries per call.

Inputs are length-bounded and validated by Pydantic. All queries go through
SQLAlchemy's parameter binding, never string interpolation. Outbound requests
go only to hardcoded upstream hosts — no user-supplied URL is ever fetched, so
there is no SSRF surface. Manual import allow-lists its writable fields, so a
malformed payload cannot inject unexpected columns. Credentials come from
environment variables only.

## Environment variables

| Variable | Required | Purpose |
|---|---|---|
| `API_ACCESS_TOKEN` | Yes in production | Protects every `/api` route |
| `DATABASE_URL` | Recommended | Postgres; SQLite fallback is ephemeral |
| `DRUGS_COM_API_KEY` | No | Enables the Drugs.com licensed-feed adapter |
| `DRUGS_COM_API_BASE` | No | Overrides the feed endpoint |
| `ANTHROPIC_API_KEY` | No | Claude drafting |

## Refresh

```bash
curl -X POST http://localhost:8000/api/drugs/refresh \
  -H "X-API-Key: $API_ACCESS_TOKEN" -H "content-type: application/json" \
  -d '{"queries": ["semaglutide", "tirzepatide"]}'
```

Returns a per-source outcome for each query. Inspect history at
`GET /api/drugs/refresh/history`.

## Bulk catalogue load

The refresh endpoint above fetches one query at a time against the live API.
That cannot fill the catalogue: openFDA caps `skip` at 25,000 records, so
paging the API can never reach the ~137k marketed products or ~262k labels the
FDA publishes. openFDA also publishes the same data as complete downloadable
partitions, with no cap and no rate limit, and
`backend/scripts/ingest_openfda_bulk.py` loads those.

```bash
cd backend

# A representative slice for a dev database (minutes)
./.venv/bin/python scripts/ingest_openfda_bulk.py --limit 5000

# Product identity only, no clinical narrative
./.venv/bin/python scripts/ingest_openfda_bulk.py --datasets ndc

# The full corpus (hours; ~15 GB transient download, deleted as it loads)
./.venv/bin/python scripts/ingest_openfda_bulk.py
```

NDC loads before label by design: NDC establishes product identity across the
catalogue, and the label pass then layers clinical narrative onto those rows
through the repository's existing non-destructive merge. Records are written
via `drug_repository.upsert_drug`, so bulk rows are indistinguishable from
query-loaded ones and carry the same provenance. Re-running is safe — records
upsert on `(generic_name, brand_name)`.

No API key is needed; bulk downloads are unauthenticated. An openFDA key
raises live-API rate limits but does not lift the `skip` cap, which is why
bulk partitions rather than a key are the answer to catalogue coverage.

What to expect from a full load:

| | |
| --- | --- |
| NDC records | ~137k products, deduplicating to fewer drugs |
| Labels read | ~262k |
| Labels usable | ~20% |
| Class coverage | ~50% of NDC rows carry `pharm_class` |

**About 80% of SPL label records carry no `openfda` annotation block**, so they
have no resolvable generic name and cannot become a record without inventing an
identity. Those are dropped and reported as `unidentifiable` in the load
summary rather than silently discarded.

Memory stays flat regardless of corpus size: partitions run to about a gigabyte
of JSON each and are streamed with an incremental decoder, never `json.load`.

## FDA catalogue datasets

Beyond the drug monograph itself, three openFDA datasets load into their own
tables (`db/fda_catalog_models.py`) — an approval application, a recall, and a
supply shortage are different entities from a drug, so they are not forced
onto `DrugORM`:

| Table | Rows | Answers |
| --- | --- | --- |
| `fda_applications` | 29,277 | who holds the NDA/ANDA/BLA |
| `fda_application_products` | 51,660 | what each application covers |
| `fda_submissions` | 188,144 | first approval date, supplement history |
| `drug_recalls` | 17,875 | enforcement actions, Class I/II/III |
| `drug_shortages` | 1,627 | current and resolved supply shortages |

```bash
cd backend
./.venv/bin/python scripts/ingest_openfda_bulk.py --datasets drugsfda,enforcement,shortages
```

Roughly 95 seconds for all three. Re-running merges on natural keys rather
than duplicating.

First-approval lookups verified against the four curated molecules: Eliquis
NDA202155 (2012-12-28), Jardiance NDA204629 (2014-08-01), Ozempic NDA209637
(2017-12-05), Keytruda BLA125514 (2014-09-04).

**Orange Book is deliberately not loaded from openFDA.** `services/orange_book.py`
already ingests FDA's own Orange Book zip, which carries `patent.txt` and
`exclusivity.txt`. openFDA's `orangebook` dataset has neither — it stops at
therapeutic equivalence codes — so loading it would replace a better source
with a worse one. The CLI rejects `--datasets orangebook` and says so.

**FAERS (`drug/event`) is not loaded.** 20.7 million reports, ~114 GB. That
needs a deliberate decision about storage and sampling, not a default load.

## Limitations

- **Structured pairwise interactions require a licensed feed.** openFDA carries
  the label's interactions *narrative* (stored on the drug record), not
  structured pairs. The interactions endpoint says so rather than returning an
  empty list that reads as "no interactions".
- **Coverage is US-centric.** openFDA covers FDA-registered products. An
  India-only molecule or CDSCO-approved combination will not be found; use the
  manual import path for those.
- **No sales, pricing, or trade-margin data.** That is licensed commercial data
  (IQVIA, AIOCD-AWACS) and is not available from any public source.
- **A bulk load is a snapshot, not a subscription.** openFDA republishes
  partitions periodically; the loaded catalogue is only as current as the
  `export_date` recorded on each record's provenance row. Re-run to refresh.

## Testing

```bash
cd backend && ./.venv/bin/python -m pytest -q
```

31 tests cover this module — creation, retrieval, search across every field
type, pagination, comparison, interactions, attribution, invalid ids, empty
search, duplicate handling, constraints, response schemas, and each external
failure mode. They are network-free: the adapter is substituted with a test
double, so CI needs no outbound access.
