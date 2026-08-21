import asyncio

from fastapi import APIRouter, Query

from ..models.lifecycle import MoleculeLifecycle
from ..services.lifecycle_service import build_lifecycle

router = APIRouter(prefix="/api/lifecycle", tags=["Patent, Exclusivity & Competitive Entry"])


@router.get("/molecule", response_model=MoleculeLifecycle)
async def get_molecule_lifecycle(
    molecule: str = Query(..., description="Molecule or fixed-dose combination, e.g. 'Empagliflozin + Metformin'")
):
    """Innovator, patents and expiry, exclusivity, and approved generic entrants.

    Sourced from the FDA Orange Book. Parsing runs off the event loop because
    the first call builds an index over ~49k product rows.
    """
    return await asyncio.get_event_loop().run_in_executor(None, build_lifecycle, molecule)
