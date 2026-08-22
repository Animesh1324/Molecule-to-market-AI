from typing import Optional

from fastapi import APIRouter, Query
from ..models.trademark import TrademarkIntelligence
from ..services.trademark_service import generate_trademark_intelligence

router = APIRouter(prefix="/api/trademark", tags=["Trademark & Brand Naming"])

@router.get("/analyze", response_model=TrademarkIntelligence)
async def analyze_trademark(
    molecule: str = Query(..., description="Molecule name"),
    therapy_area: str = Query("Cardiometabolic", description="Therapy area"),
    indication: Optional[str] = Query(None, description="Clinical indication, for AI-drafted naming context"),
    requirement: Optional[str] = Query(None, description="Free-text naming brief for AI-drafted suggestions"),
    count: int = Query(8, ge=3, le=20, description="How many name candidates to return"),
    exclude: Optional[str] = Query(None, description="Comma-separated names already shown, to fetch fresh options"),
):
    exclude_list = [n.strip() for n in exclude.split(",") if n.strip()] if exclude else []
    return await generate_trademark_intelligence(
        molecule, therapy_area, indication=indication, requirement=requirement,
        count=count, exclude=exclude_list,
    )
