from fastapi import APIRouter, Query
from typing import Optional
from ..models.trials import ClinicalTrialLandscape
from ..services.trials_service import fetch_clinical_trial_landscape

router = APIRouter(prefix="/api/trials", tags=["Clinical Trials Intelligence"])

@router.get("/landscape", response_model=ClinicalTrialLandscape)
async def get_clinical_trials(
    molecule: str = Query(..., description="Molecule name"),
    indication: Optional[str] = Query(None, description="Clinical indication")
):
    return await fetch_clinical_trial_landscape(molecule, indication)
