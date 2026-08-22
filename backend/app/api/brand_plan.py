import asyncio
import logging

from fastapi import APIRouter, Query, Body, HTTPException
from typing import Optional, Dict, Any, List
from ..models.brand_plan import CompleteBrandPlan
from ..services.ai_orchestrator import generate_strategic_brand_plan
from ..services import ai_drafting
from ..services.claude_client import is_configured as ai_configured
from ..services.pubchem_service import fetch_molecule_intelligence
from ..services.pubmed_service import search_pubmed_evidence
from ..db import database as db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/brand-plan", tags=["Brand Plan Builder"])


async def _grounding_for(molecule: str, indication: str):
    """Fetch the verified facts the drafting model is allowed to build on.

    Best-effort: drafting proceeds with whatever context is available, since a
    PubChem or PubMed outage should degrade the draft, not fail the request.
    """
    molecule_profile: Optional[Dict[str, Any]] = None
    evidence: List[Dict[str, Any]] = []

    profile_result, evidence_result = await asyncio.gather(
        fetch_molecule_intelligence(molecule),
        search_pubmed_evidence(molecule, indication),
        return_exceptions=True,
    )

    if isinstance(profile_result, Exception):
        logger.warning("Molecule grounding unavailable for %s: %s", molecule, profile_result)
    elif profile_result is not None:
        molecule_profile = (
            profile_result.model_dump() if hasattr(profile_result, "model_dump") else profile_result.dict()
        )

    if isinstance(evidence_result, Exception):
        logger.warning("Evidence grounding unavailable for %s: %s", molecule, evidence_result)
    elif evidence_result:
        evidence = [
            p.model_dump() if hasattr(p, "model_dump") else p.dict() for p in evidence_result
        ]

    return molecule_profile, evidence


def _matches_request(stored: Dict[str, Any], molecule: str, brand_name: Optional[str], therapy_area: str, indication: str, target_geography: str) -> bool:
    """Report whether a saved plan was built from the same inputs as this request.

    A stored plan is only reusable if its defining inputs still match. Returning
    it regardless would silently serve an Empagliflozin cardio-renal plan to
    someone who just switched the project to a different molecule or indication.
    """
    if stored.get("molecule_name", "").lower() != molecule.strip().title().lower():
        return False
    if stored.get("therapy_area") != therapy_area:
        return False
    if stored.get("indication") != indication:
        return False
    if stored.get("target_geography") != target_geography:
        return False
    if brand_name and stored.get("brand_name") != brand_name:
        return False
    return True


@router.get("/generate", response_model=CompleteBrandPlan)
async def get_or_generate_brand_plan(
    project_id: str = Query(..., description="Project ID"),
    molecule: str = Query(..., description="Molecule name"),
    brand_name: Optional[str] = Query(None, description="Brand name"),
    therapy_area: str = Query("Cardiometabolic", description="Therapy area"),
    indication: str = Query("Heart Failure & Chronic Kidney Disease in Type 2 Diabetes", description="Clinical Indication"),
    target_geography: str = Query("Global", description="Geography"),
    refresh: bool = Query(False, description="Discard any saved plan and rebuild from the supplied inputs"),
    ai: bool = Query(True, description="Draft narrative sections with Claude when an API key is configured")
):
    # Reuse the saved plan only when it was built from these same inputs, so
    # edits to the project (new molecule, brand, or indication) take effect.
    if not refresh:
        existing = db.db_get_brand_plan(project_id)
        if existing and _matches_request(existing, molecule, brand_name, therapy_area, indication, target_geography):
            try:
                return CompleteBrandPlan(**existing)
            except Exception:
                # If stored data is incompatible, fall through to regenerate
                pass

    plan = generate_strategic_brand_plan(
        project_id=project_id,
        molecule_name=molecule,
        brand_name=brand_name,
        therapy_area=therapy_area,
        indication=indication,
        target_geography=target_geography
    )

    if ai and ai_configured():
        molecule_profile, evidence = await _grounding_for(molecule, indication)
        plan = await ai_drafting.draft_brand_plan(
            plan, molecule=molecule_profile, evidence=evidence
        )

    # persist serialized plan
    db.db_save_brand_plan(project_id, plan.model_dump() if hasattr(plan, 'model_dump') else plan.dict())
    return plan


@router.get("/{project_id}", response_model=CompleteBrandPlan)
async def fetch_brand_plan(project_id: str):
    existing = db.db_get_brand_plan(project_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Brand plan not found")
    return CompleteBrandPlan(**existing)


@router.put("/{project_id}", response_model=CompleteBrandPlan)
async def update_brand_plan(project_id: str, updated_plan: CompleteBrandPlan):
    """Persist an edited plan.

    MLR signoff is forced false on write. This endpoint accepts a whole plan
    from the client, so an omitted or hand-set flag would otherwise let an
    unreviewed plan claim it had cleared medical, legal, and regulatory review.
    Signoff is a human act recorded outside this application.
    """
    payload = updated_plan.model_dump() if hasattr(updated_plan, 'model_dump') else updated_plan.dict()
    payload["mlr_compliance_signoff_ready"] = False
    db.db_save_brand_plan(project_id, payload)
    return CompleteBrandPlan(**payload)
