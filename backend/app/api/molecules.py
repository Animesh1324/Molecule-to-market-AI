from typing import Optional

from fastapi import APIRouter, Query, HTTPException
from ..models.molecule import MoleculeProfile
from ..services.claude_client import ClaudeUnavailable
from ..services.molecule_dossier import build_dossier
from ..services.molecule_answer import answer_molecule
from ..services.pubchem_service import fetch_molecule_intelligence

router = APIRouter(prefix="/api/molecules", tags=["Molecule Intelligence"])

@router.get("/search", response_model=MoleculeProfile)
async def search_molecule(name: str = Query(..., description="Generic or INN molecule name")):
    if not name or len(name.strip()) == 0:
        raise HTTPException(status_code=400, detail="Molecule name is required")
    return await fetch_molecule_intelligence(name)


@router.get("/dossier")
def molecule_dossier(
    name: str = Query(..., description="Generic or INN molecule name"),
    paper_limit: int = Query(25, ge=1, le=200, description="Cached papers to return"),
):
    """Every stored fact about one molecule, in a single call.

    Identity and label text, approval history, patents and exclusivity, recalls
    and shortages, and cached literature — each section naming its source and a
    URL a reviewer can open. Reads only local tables, so it does not depend on
    an upstream being reachable; run the bulk loaders and the PubMed fetch to
    populate it.
    """
    if not name.strip():
        raise HTTPException(status_code=400, detail="Molecule name is required")
    return build_dossier(name, paper_limit=paper_limit)


@router.get("/ask")
async def ask_molecule(
    name: str = Query(..., description="Generic or INN molecule name"),
    question: Optional[str] = Query(None, description="Optional specific question"),
):
    """Answer a molecule query with Claude, grounded in the stored FDA record.

    Every returned field is marked `source` fda or model, and `mlr_citable` is
    False for anything the model supplied — a model-sourced clinical statement
    cannot be traced to a regulatory document. Output is screened by the same
    compliance rules that guard AI-drafted plan text.

    Requires ANTHROPIC_API_KEY; returns 503 when unconfigured rather than
    falling back silently to a source the caller did not ask for.
    """
    if not name.strip():
        raise HTTPException(status_code=400, detail="Molecule name is required")
    try:
        return await answer_molecule(name, question)
    except ClaudeUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
