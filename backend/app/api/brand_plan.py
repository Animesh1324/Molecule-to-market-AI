from fastapi import APIRouter, Query, Body, HTTPException
from typing import Optional, Dict, Any
from ..models.brand_plan import CompleteBrandPlan
from ..services.ai_orchestrator import generate_strategic_brand_plan
from ..db import database as db

router = APIRouter(prefix="/api/brand-plan", tags=["Brand Plan Builder"])


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
    refresh: bool = Query(False, description="Discard any saved plan and rebuild from the supplied inputs")
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
    db.db_save_brand_plan(project_id, updated_plan.model_dump() if hasattr(updated_plan, 'model_dump') else updated_plan.dict())
    return updated_plan
