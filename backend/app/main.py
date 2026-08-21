import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api import (
    brand_plan,
    lifecycle,
    competitors,
    creative_assets,
    evidence,
    forecasting,
    molecules,
    projects,
    regulatory,
    reports,
    trademark,
    trials,
)
from .config import get_settings
from .db.database import init_db, db_healthy
from .services.claude_client import is_configured as ai_configured

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("pharma_brandplan")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    if settings["app_env"] == "production" and not settings["cors_origins_configured"]:
        logger.warning(
            "CORS_ORIGINS is not set in production; falling back to localhost origins. "
            "The deployed frontend will be blocked until this is configured."
        )
    logger.info("Application startup complete for env=%s", settings["app_env"])
    yield


app = FastAPI(
    title="Pharma BrandPlan AI — Core API Engine",
    description="Enterprise pharmaceutical brand planning, clinical evidence synthesis, and commercialization platform.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings["cors_origins"],
    allow_credentials=True,
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


app.include_router(projects.router)
app.include_router(molecules.router)
app.include_router(evidence.router)
app.include_router(trials.router)
app.include_router(regulatory.router)
app.include_router(trademark.router)
app.include_router(competitors.router)
app.include_router(forecasting.router)
app.include_router(brand_plan.router)
app.include_router(creative_assets.router)
app.include_router(reports.router)
app.include_router(lifecycle.router)


@app.get("/")
async def root():
    return {
        "system": "Pharma BrandPlan AI Engine",
        "status": "Operational",
        "version": "1.0.0",
        "modules_active": 11,
        "compliance_mode": "FDA OPDP / CDSCO UCPMP / EMA Fair Balance Active",
        "environment": settings["app_env"],
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
