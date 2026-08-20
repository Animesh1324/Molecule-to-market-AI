from fastapi import APIRouter, Query, Body, HTTPException
from typing import Optional, Dict, Any
from ..models.brand_plan import CompleteBrandPlan
from ..services.ai_orchestrator import generate_strategic_brand_plan
from ..db import database as db

router = APIRouter(prefix="/api/brand-plan", tags=["Brand Plan Builder"])


@router.get("/generate", response_model=CompleteBrandPlan)
async def get_or_generate_brand_plan(
    project_id: str = Query(..., description="Project ID"),
    molecule: str = Query(..., description="Molecule name"),
    brand_name: Optional[str] = Query(None, description="Brand name"),
    therapy_area: str = Query("Cardiometabolic", description="Therapy area"),
    indication: str = Query("Heart Failure & Chronic Kidney Disease in Type 2 Diabetes", description="Clinical Indication"),
    target_geography: str = Query("Global", description="Geography")
):
    # Check persistent store first
    existing = db.db_get_brand_plan(project_id)
    if existing:
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
