import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api import (
    brand_plan,
    copilot,
    intelligence,
    lifecycle,
    competitors,
    market,
    auth,
    drugs,
    creative_assets,
    evidence,
    forecasting,
    molecules,
    primary_research,
    projects,
    regulatory,
    reports,
    uploads,
    trademark,
    trials,
)
from .config import get_settings
from .db.database import init_db, db_healthy
from .security import (
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    auth_required,
    enforce_startup_policy,
    require_access,
)
from .services.claude_client import is_configured as ai_configured

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("molecule_to_market")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    enforce_startup_policy()
    init_db()
    if settings["app_env"] == "production" and not settings["cors_origins_configured"]:
        logger.warning(
            "CORS_ORIGINS is not set in production; falling back to localhost origins. "
            "The deployed frontend will be blocked until this is configured."
        )
    logger.info("Application startup complete for env=%s", settings["app_env"])
    yield


# The interactive docs and OpenAPI schema enumerate every route and field.
# They are built-in FastAPI routes, so a router-level dependency never covers
# them — the only reliable way to protect them is not to mount them at all in
# production. Locally they stay on, because that is where they are useful.
_is_production = settings["app_env"] == "production"

app = FastAPI(
    title="Molecule to Market AI — Core API Engine",
    description="Enterprise pharmaceutical brand planning, clinical evidence synthesis, and commercialization platform.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None if _is_production else "/docs",
    redoc_url=None if _is_production else "/redoc",
    openapi_url=None if _is_production else "/openapi.json",
)

app.add_middleware(RateLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings["cors_origins"],
    # No cookie is ever set by this API — every protected route authenticates
    # off a header (X-API-Key / X-Session-Token), never a cookie the browser
    # would attach automatically. allow_credentials only matters for cookies;
    # leaving it on here is pure unused risk, not a real requirement.
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Surface invalid modelling inputs as 400s rather than opaque 500s."""
    logger.warning("Invalid input on %s: %s", request.url.path, exc)
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Log the failure server-side and return a generic message to the caller."""
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. The incident has been logged."},
    )


app.include_router(projects.router, dependencies=[Depends(require_access)])
app.include_router(molecules.router, dependencies=[Depends(require_access)])
app.include_router(evidence.router, dependencies=[Depends(require_access)])
app.include_router(trials.router, dependencies=[Depends(require_access)])
app.include_router(regulatory.router, dependencies=[Depends(require_access)])
app.include_router(trademark.router, dependencies=[Depends(require_access)])
app.include_router(competitors.router, dependencies=[Depends(require_access)])
app.include_router(forecasting.router, dependencies=[Depends(require_access)])
app.include_router(brand_plan.router, dependencies=[Depends(require_access)])
app.include_router(creative_assets.router, dependencies=[Depends(require_access)])
app.include_router(reports.router, dependencies=[Depends(require_access)])
app.include_router(lifecycle.router, dependencies=[Depends(require_access)])
app.include_router(uploads.router, dependencies=[Depends(require_access)])
app.include_router(intelligence.router, dependencies=[Depends(require_access)])
app.include_router(drugs.router, dependencies=[Depends(require_access)])
app.include_router(market.router, dependencies=[Depends(require_access)])
app.include_router(auth.router, dependencies=[Depends(require_access)])
app.include_router(copilot.router, dependencies=[Depends(require_access)])
app.include_router(primary_research.router, dependencies=[Depends(require_access)])


@app.get("/")
async def root():
    return {
        "system": "Molecule to Market AI Engine",
        "status": "Operational",
        "version": "1.0.0",
        "modules_active": 16,
        "compliance_mode": "FDA OPDP / CDSCO UCPMP / EMA Fair Balance Active",
        "environment": settings["app_env"],
        "authentication": "required" if auth_required() else "open (no API_ACCESS_TOKEN set)",
        "ai_drafting": {
            "enabled": ai_configured(),
            "model": settings["claude_model"] if ai_configured() else None,
            "note": "Drafts internal strategy only. Clinical claims stay sourced from the evidence and label modules.",
        },
    }


@app.get("/health")
async def health(response: Response):
    """Report real readiness so a platform health check can act on it."""
    db_ok = db_healthy()
    if not db_ok:
        response.status_code = 503
    return {
        "status": "healthy" if db_ok else "degraded",
        "environment": settings["app_env"],
        "database": "connected" if db_ok else "unavailable",
    }
