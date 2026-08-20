from fastapi import APIRouter, Query
from ..models.trademark import TrademarkIntelligence
from ..services.trademark_service import generate_trademark_intelligence

router = APIRouter(prefix="/api/trademark", tags=["Trademark & Brand Naming"])

@router.get("/analyze", response_model=TrademarkIntelligence)
async def analyze_trademark(
    molecule: str = Query(..., description="Molecule name"),
    therapy_area: str = Query("Cardiometabolic", description="Therapy area")
):
    return generate_trademark_intelligence(molecule, therapy_area)
