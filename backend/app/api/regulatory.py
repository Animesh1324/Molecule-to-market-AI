from fastapi import APIRouter, Query
from ..models.regulatory import RegulatoryIntelligence
from ..services.regulatory_service import fetch_regulatory_intelligence

router = APIRouter(prefix="/api/regulatory", tags=["Regulatory Intelligence"])

@router.get("/labels", response_model=RegulatoryIntelligence)
async def get_regulatory_labels(
    molecule: str = Query(..., description="Molecule name")
):
    return await fetch_regulatory_intelligence(molecule)
