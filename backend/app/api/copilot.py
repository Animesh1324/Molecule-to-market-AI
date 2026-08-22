import asyncio
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from ..services.ai_copilot import answer_copilot_question
from ..services.competitor_service import generate_competitor_intelligence
from ..services.pubchem_service import fetch_molecule_intelligence
from ..services.pubmed_service import search_pubmed_evidence
from ..services.regulatory_service import fetch_regulatory_intelligence

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/copilot", tags=["AI Co-Pilot"])


class CoPilotTurn(BaseModel):
    sender: str  # 'user' | 'ai'
    text: str


class CoPilotRequest(BaseModel):
    molecule: str
    brand_name: str
    therapy_area: str = ""
    indication: str = ""
    question: str
    history: List[CoPilotTurn] = []


class CoPilotResponse(BaseModel):
    reply: str
    ai_answered: bool


@router.post("/ask", response_model=CoPilotResponse)
async def ask_copilot(request: CoPilotRequest):
    """Answer a brand-team question grounded in this molecule's verified facts.

    Best-effort grounding: a PubChem/PubMed/regulatory outage degrades the
    context the model sees, not the request itself.
    """
    molecule_profile: Optional[Dict[str, Any]] = None
    evidence: List[Dict[str, Any]] = []
    regulatory: Optional[Dict[str, Any]] = None
    competitor_data: Optional[Dict[str, Any]] = None

    profile_result, evidence_result, regulatory_result = await asyncio.gather(
        fetch_molecule_intelligence(request.molecule),
        search_pubmed_evidence(request.molecule, request.indication),
        fetch_regulatory_intelligence(request.molecule),
        return_exceptions=True,
    )
    if isinstance(profile_result, Exception):
        logger.warning("Co-pilot molecule grounding unavailable for %s: %s", request.molecule, profile_result)
    elif profile_result is not None:
        molecule_profile = profile_result.model_dump() if hasattr(profile_result, "model_dump") else profile_result.dict()

    if isinstance(evidence_result, Exception):
        logger.warning("Co-pilot evidence grounding unavailable for %s: %s", request.molecule, evidence_result)
    elif evidence_result:
        evidence = [p.model_dump() if hasattr(p, "model_dump") else p.dict() for p in evidence_result]

    if isinstance(regulatory_result, Exception):
        logger.warning("Co-pilot regulatory grounding unavailable for %s: %s", request.molecule, regulatory_result)
    elif regulatory_result is not None:
        regulatory = regulatory_result.model_dump() if hasattr(regulatory_result, "model_dump") else regulatory_result.dict()

    try:
        competitor_result = generate_competitor_intelligence(request.molecule, request.indication)
        competitor_data = competitor_result.model_dump() if hasattr(competitor_result, "model_dump") else competitor_result.dict()
    except Exception:
        logger.warning("Co-pilot competitor grounding unavailable for %s", request.molecule, exc_info=True)

    result = await answer_copilot_question(
        molecule=request.molecule,
        brand_name=request.brand_name,
        therapy_area=request.therapy_area,
        indication=request.indication,
        question=request.question,
        history=[t.model_dump() if hasattr(t, "model_dump") else t.dict() for t in request.history],
        molecule_profile=molecule_profile,
        evidence=evidence,
        regulatory=regulatory,
        competitor_data=competitor_data,
    )
    return CoPilotResponse(**result)
