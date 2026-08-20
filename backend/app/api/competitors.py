from fastapi import APIRouter, Query
from typing import Optional
from ..models.competitor import CompetitorIntelligence
from ..services.competitor_service import generate_competitor_intelligence

router = APIRouter(prefix="/api/competitors", tags=["Competitor Intelligence"])

@router.get("/landscape", response_model=CompetitorIntelligence)
async def get_competitor_landscape(
    molecule: str = Query(..., description="Molecule name"),
    indication: Optional[str] = Query(None, description="Indication filter")
):
    return generate_competitor_intelligence(molecule, indication)
