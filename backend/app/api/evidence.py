"""Research evidence endpoints.

The paper list is paged rather than truncated, and every response carries
`total_available` — what PubMed says exists — next to `fetched_count`, what is
cached locally. Those two numbers are deliberately separate: a partial fetch
must never be presentable as the whole literature.
"""
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Query

from ..models.evidence import ClaimEvidenceMapping, ResearchPaper
from ..services.pubmed_service import (
    fetch_pubmed_corpus,
    get_evidence_page,
    map_claims_to_evidence,
    search_pubmed_evidence,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/evidence", tags=["Research Papers & Evidence"])


@router.get("/papers", response_model=List[ResearchPaper])
async def get_evidence_papers(
    molecule: str = Query(..., description="Molecule name"),
    indication: Optional[str] = Query(None, description="Indication filter"),
    limit: int = Query(100, ge=1, le=1000, description="Papers per page"),
):
    """First page of the molecule's literature. Kept for existing callers."""
    return await search_pubmed_evidence(molecule, indication, limit=limit)


@router.get("/library")
async def get_evidence_library(
    molecule: str = Query(..., description="Molecule name"),
    indication: Optional[str] = Query(None, description="Indication filter"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    refresh: bool = Query(False, description="Re-query PubMed instead of using the cache"),
) -> Dict[str, Any]:
    """A page of papers plus the true corpus size and cache state."""
    return await get_evidence_page(molecule, indication, limit=limit,
                                   offset=offset, refresh=refresh)


@router.post("/library/fetch-all")
async def fetch_entire_corpus(
    background: BackgroundTasks,
    molecule: str = Query(..., description="Molecule name"),
    indication: Optional[str] = Query(None),
    max_records: int = Query(20000, ge=1, le=100000,
                             description="Ceiling for this pass"),
) -> Dict[str, Any]:
    """Pull the molecule's whole PubMed bibliography into the local cache.

    Runs in the background: NCBI is rate-limited to 3 requests/second without an
    API key, so a five-thousand-paper corpus takes minutes. Poll `/library` and
    watch `fetched_count` climb toward `total_available`.
    """
    background.add_task(_fetch_all, molecule, indication, max_records)
    return {
        "molecule": molecule,
        "status": "fetching",
        "detail": "Poll GET /api/evidence/library to watch fetched_count rise.",
    }


async def _fetch_all(molecule: str, indication: Optional[str], max_records: int) -> None:
    try:
        result = await fetch_pubmed_corpus(molecule, indication, max_records=max_records)
        logger.info("Full corpus for %s: %d of %d", molecule,
                    result["fetched_count"], result["total_available"])
    except Exception:
        logger.exception("Full corpus fetch failed for %s", molecule)


@router.get("/claims", response_model=List[ClaimEvidenceMapping])
async def get_claim_mappings(
    molecule: str = Query(..., description="Molecule name"),
    indication: Optional[str] = Query(None, description="Indication filter"),
):
    papers = await search_pubmed_evidence(molecule, indication, limit=25)
    return map_claims_to_evidence(papers)
