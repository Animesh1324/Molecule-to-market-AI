import asyncio
import logging

from fastapi import APIRouter, Query
from typing import Optional
from ..models.assets import CreativeCommercialAssets, VisualAidBrief
from ..services.ai_orchestrator import generate_commercial_assets
from ..services.pubchem_service import fetch_molecule_intelligence
from ..services.pubmed_service import search_pubmed_evidence
from ..services.regulatory_service import fetch_regulatory_intelligence
from ..services.visual_aid_drafting import draft_visual_aid_brief

logger = logging.getLogger(__name__)

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


@router.get("/visual-aid-brief", response_model=VisualAidBrief)
async def get_visual_aid_brief(
    molecule: str = Query(..., description="Molecule name"),
    brand_name: Optional[str] = Query(None, description="Brand name"),
    indication: str = Query("Heart Failure & Chronic Kidney Disease in Type 2 Diabetes", description="Clinical Indication"),
):
    """The 8-element single-page detail-aid brief, plus a ready-to-paste image-generation prompt."""
    profile_result, evidence_result, regulatory_result = await asyncio.gather(
        fetch_molecule_intelligence(molecule),
        search_pubmed_evidence(molecule, indication),
        fetch_regulatory_intelligence(molecule),
        return_exceptions=True,
    )
    molecule_profile = None
    if isinstance(profile_result, Exception):
        logger.warning("Molecule grounding unavailable for %s: %s", molecule, profile_result)
    elif profile_result is not None:
        molecule_profile = profile_result.model_dump() if hasattr(profile_result, "model_dump") else profile_result.dict()

    evidence = []
    if isinstance(evidence_result, Exception):
        logger.warning("Evidence grounding unavailable for %s: %s", molecule, evidence_result)
    elif evidence_result:
        evidence = [p.model_dump() if hasattr(p, "model_dump") else p.dict() for p in evidence_result]

    regulatory = None
    if isinstance(regulatory_result, Exception):
        logger.warning("Regulatory grounding unavailable for %s: %s", molecule, regulatory_result)
    elif regulatory_result is not None:
        regulatory = regulatory_result.model_dump() if hasattr(regulatory_result, "model_dump") else regulatory_result.dict()

    return await draft_visual_aid_brief(
        molecule_name=molecule,
        brand_name=brand_name or f"{molecule.title()} Brand",
        indication=indication,
        molecule=molecule_profile,
        regulatory=regulatory,
        evidence=evidence,
    )
