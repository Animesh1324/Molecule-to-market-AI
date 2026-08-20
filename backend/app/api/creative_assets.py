from fastapi import APIRouter, Query
from typing import Optional
from ..models.assets import CreativeCommercialAssets
from ..services.ai_orchestrator import generate_commercial_assets

router = APIRouter(prefix="/api/assets", tags=["Creative & Commercial Assets"])

@router.get("/generate", response_model=CreativeCommercialAssets)
async def get_creative_assets(
    molecule: str = Query(..., description="Molecule name"),
    brand_name: Optional[str] = Query(None, description="Brand name"),
    indication: str = Query("Heart Failure & Chronic Kidney Disease in Type 2 Diabetes", description="Clinical Indication")
):
    return generate_commercial_assets(
        molecule_name=molecule,
        brand_name=brand_name,
        indication=indication
    )
