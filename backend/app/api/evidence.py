from fastapi import APIRouter, Query
from typing import List, Dict, Any, Optional
from ..models.evidence import ResearchPaper, ClaimEvidenceMapping
from ..services.pubmed_service import search_pubmed_evidence, map_claims_to_evidence

router = APIRouter(prefix="/api/evidence", tags=["Research Papers & Evidence"])

@router.get("/papers", response_model=List[ResearchPaper])
async def get_evidence_papers(
    molecule: str = Query(..., description="Molecule name"),
    indication: Optional[str] = Query(None, description="Indication filter")
):
    return await search_pubmed_evidence(molecule, indication)

@router.get("/claims", response_model=List[ClaimEvidenceMapping])
async def get_claim_mappings(
    molecule: str = Query(..., description="Molecule name"),
    indication: Optional[str] = Query(None, description="Indication filter")
):
    papers = await search_pubmed_evidence(molecule, indication)
    return map_claims_to_evidence(papers)
