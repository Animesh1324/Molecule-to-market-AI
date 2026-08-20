from fastapi import APIRouter, Query, HTTPException
from ..models.molecule import MoleculeProfile
from ..services.pubchem_service import fetch_molecule_intelligence

router = APIRouter(prefix="/api/molecules", tags=["Molecule Intelligence"])

@router.get("/search", response_model=MoleculeProfile)
async def search_molecule(name: str = Query(..., description="Generic or INN molecule name")):
    if not name or len(name.strip()) == 0:
        raise HTTPException(status_code=400, detail="Molecule name is required")
    return await fetch_molecule_intelligence(name)
