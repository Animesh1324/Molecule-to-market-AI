from fastapi import APIRouter, Query, HTTPException
from ..models.molecule import MoleculeProfile
from ..services.molecule_dossier import build_dossier
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
