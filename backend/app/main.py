import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import (
    brand_plan,
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
from .db.database import init_db

logger = logging.getLogger("pharma_brandplan")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
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
    allow_origins=settings["cors_origins"] or ["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
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


@app.get("/")
async def root():
    return {
        "system": "Pharma BrandPlan AI Engine",
        "status": "Operational",
        "version": "1.0.0",
        "modules_active": 10,
        "compliance_mode": "FDA OPDP / CDSCO UCPMP / EMA Fair Balance Active",
        "environment": settings["app_env"],
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "environment": settings["app_env"],
        "database": "connected",
    }
