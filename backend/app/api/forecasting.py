from fastapi import APIRouter, Query
from ..models.forecast import MarketForecast
from ..services.forecast_service import calculate_market_forecast

router = APIRouter(prefix="/api/forecasting", tags=["Market Sizing & Forecasting"])

@router.get("/model", response_model=MarketForecast)
async def get_market_forecast(
    therapy_area: str = Query("Cardiometabolic", description="Therapeutic area"),
    target_geography: str = Query("Global", description="Target market"),
    total_population: int = Query(330000000, ge=1, le=10_000_000_000, description="Total target population"),
    prevalence_rate: float = Query(0.105, gt=0, le=1, description="Prevalence rate (0 to 1)"),
    diagnosed_rate: float = Query(0.72, gt=0, le=1, description="Diagnosis rate (0 to 1)"),
    treated_rate: float = Query(0.60, gt=0, le=1, description="Treatment rate (0 to 1)"),
    brand_adoption_rate_y1: float = Query(0.04, gt=0, le=1, description="Brand market share Year 1 (0 to 1)"),
    annual_cost_per_patient_usd: float = Query(3600.0, gt=0, le=10_000_000, description="Net brand price per patient per year in USD")
):
    return calculate_market_forecast(
        therapy_area=therapy_area,
        target_geography=target_geography,
        total_population=total_population,
        prevalence_rate=prevalence_rate,
        diagnosed_rate=diagnosed_rate,
        treated_rate=treated_rate,
        brand_adoption_rate_y1=brand_adoption_rate_y1,
        annual_cost_per_patient_usd=annual_cost_per_patient_usd
    )
