"""Patient experience, brand-name generation, and India regulatory endpoints."""
import asyncio
from typing import List

from fastapi import APIRouter, Query
from pydantic import BaseModel

from ..models.cdsco import CDSCOIntelligence
from ..models.patient_experience import PatientExperience
from ..services.brand_name_generator import generate_ai_candidates, generate_candidates
from ..services.cdsco_service import build_cdsco_intelligence
from ..services.patient_experience_service import build_patient_experience

router = APIRouter(prefix="/api/intelligence", tags=["Patient, Naming & India Intelligence"])


class BrandNameCandidates(BaseModel):
    molecule: str
    therapy_area: str
    indication: str
    candidates: List[dict]
    screening_basis: str
    next_step: str
    ai_generated: bool = False
    requirement_applied: str = ""


@router.get("/patient-experience", response_model=PatientExperience)
async def patient_experience(
    molecule: str = Query(..., description="Molecule or fixed-dose combination")
):
    """Real-world reported problems and adherence signal, from FDA FAERS."""
    return await build_patient_experience(molecule)


@router.get("/brand-names", response_model=BrandNameCandidates)
async def brand_names(
    molecule: str = Query(..., description="Molecule or fixed-dose combination"),
    therapy_area: str = Query("", description="Therapy area, to steer the naming roots"),
    indication: str = Query("", description="Indication, to steer the naming roots"),
    count: int = Query(10, ge=1, le=30, description="How many candidates to return"),
    requirement: str = Query("", description="Free-text naming brief for AI-drafted candidates, e.g. 'should evoke once-weekly convenience'"),
):
    """Novel brand-name candidates screened against marketed FDA brand names.

    With a `requirement`, candidates are AI-drafted to that brief (when an
    Anthropic key is configured) but still screened through the same Orange
    Book collision check as the algorithmic candidates — an AI suggestion is
    never trusted on its own judgment about collision risk.
    """
    if requirement.strip():
        candidates = await generate_ai_candidates(molecule, therapy_area, indication, requirement, count)
        ai_used = any(c.get("ai_generated") for c in candidates)
    else:
        candidates = await asyncio.get_event_loop().run_in_executor(
            None, generate_candidates, molecule, therapy_area, indication, count
        )
        ai_used = False
    return BrandNameCandidates(
        molecule=molecule,
        therapy_area=therapy_area,
        indication=indication,
        candidates=candidates,
        screening_basis=(
            "Each candidate is rejected if it matches, or is within a small edit "
            "distance of, any of the ~49,000 trade names in the FDA Orange Book."
        ),
        next_step=(
            "Run the shortlist through IP India (class 5) yourself — the public search "
            "needs a CAPTCHA and cannot be automated. Each candidate carries its "
            "IP India, USPTO, and WIPO search links."
        ),
        ai_generated=ai_used,
        requirement_applied=requirement.strip(),
    )


@router.get("/cdsco", response_model=CDSCOIntelligence)
async def cdsco(
    molecule: str = Query(..., description="Molecule or fixed-dose combination"),
    indication: str = Query("", description="Indication, used for the CTRI search"),
):
    """India regulatory checklist with direct links to each CDSCO register."""
    return build_cdsco_intelligence(molecule, indication)
