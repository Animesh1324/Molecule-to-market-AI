# Final Audit & Deployment Checklist — Pharma BrandPlan AI

This checklist helps finalize the MVP before production deployment.

## 1) Functional Checklist
- [ ] Verify all API routers registered in `backend/app/main.py` are reachable.
- [ ] Confirm CORS policy in `backend/app/main.py` is acceptable for your environment (currently `allow_origins=['*']`).
- [ ] Test core endpoints manually or via automated tests:
  - `GET /` and `GET /health`
  - `GET /api/projects` and `POST /api/projects`
  - `GET /api/brand-plan/generate` and `GET /api/brand-plan/{project_id}`
  - `GET /api/reports/audit-trail` and `POST /api/reports/audit-trail`
  - Export endpoints: `/api/reports/export/docx`, `/api/reports/export/pptx`, `/api/reports/export/xlsx`

## 2) Data & Persistence
- [ ] Confirm `backend/app/db/database.py` is creating the SQLite DB and seed data on startup (`init_db`).
- [ ] Verify `db_save_brand_plan` and `db_get_brand_plan` store and return `CompleteBrandPlan` content including `mission` and `vision`.
- [ ] Confirm `MLRAuditLogORM` persistence works (create + list).

## 3) Security & Compliance
- [ ] Ensure PHI/PII is not logged or stored inadvertently.
- [ ] Confirm MLR audit workflow enforces sign-off before claims are exported (manual step in MVP).

## 4) Testing
- [ ] Run backend tests: `pytest -q` (see `backend/tests/test_api.py`).
- [ ] Run frontend tests: `cd frontend && npm ci && npm test`.

## 5) Deployment
- [ ] GitHub Actions CI builds and tests pass on PRs.
- [ ] Docker images pushed to GHCR via `.github/workflows/publish-images.yml`.
- [ ] Decide deployment target (Render / DigitalOcean App / Kubernetes / VM). For quick deploy, pull images and use `docker-compose.yml` locally or on a host.

## 6) Environment Variables
- `DATABASE_URL` (optional) — File path or connection string for SQLite / other DB.
- `OPENAI_API_KEY` (if using live LLM APIs) — store in secrets at runtime.
- `NEXT_PUBLIC_API_BASE` — frontend config for backend URL (default `http://localhost:8000`).

## 7) Post-deploy Checks
- [ ] Smoke test main flows: create project → generate brand plan → export docx → view audit trail.
- [ ] Validate asset generation and exports open correctly in Office apps.

---
Record progress and any production-only secrets in your deployment platform's secrets manager.
