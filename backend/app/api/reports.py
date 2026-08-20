from fastapi import APIRouter, Query, Response, HTTPException
from typing import List
from datetime import datetime
from ..models.reports import MLRAuditEntry
from ..services.ai_orchestrator import generate_strategic_brand_plan, generate_commercial_assets
from ..services.forecast_service import calculate_market_forecast
from ..services.pubchem_service import fetch_molecule_intelligence
from ..services.export_service import generate_brand_plan_docx, generate_pitch_deck_pptx, generate_financial_model_xlsx
from ..db import database as db

router = APIRouter(prefix="/api/reports", tags=["Report Center & MLR Audit"])


@router.get("/audit-trail", response_model=List[MLRAuditEntry])
async def get_audit_trail():
    rows = db.db_list_mlr_audit_logs()
    # If DB empty, seed with a few sentinel entries
    if not rows:
        seed_entries = [
            {
                "id": "AUD-001",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "action_type": "CLAIM_REVIEW_REQUIRED",
                "item_reference": "EMPA-REG OUTCOME (38% CV Mortality Reduction)",
                "verified_source": "NEJM 2015; PMID: 26378978",
                "status": "NEEDS_REVIEW",
                "auditor": "System Seed - not human approved"
            },
            {
                "id": "AUD-002",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "action_type": "LABEL_SOURCE_CANDIDATE",
                "item_reference": "DailyMed US FDA Structured Product Labeling",
                "verified_source": "NDA 204629 / S-033",
                "status": "NEEDS_REVIEW",
                "auditor": "System Seed - not human approved"
            }
        ]
        for e in seed_entries:
            db.db_save_mlr_audit_log(e)
        rows = db.db_list_mlr_audit_logs()
    return [MLRAuditEntry(**r) for r in rows]


@router.post("/audit-trail", response_model=MLRAuditEntry)
async def create_audit_entry(entry: MLRAuditEntry):
    # Persist the audit entry
    db.db_save_mlr_audit_log(entry.model_dump() if hasattr(entry, 'model_dump') else entry.dict())
    return entry

@router.get("/export/docx")
async def export_brand_plan_docx(
    molecule: str = Query(..., description="Molecule name"),
    brand_name: str = Query(..., description="Brand name"),
    therapy_area: str = Query("Cardiometabolic", description="Therapy area"),
    indication: str = Query("Heart Failure & CKD in T2D", description="Indication")
):
    plan = generate_strategic_brand_plan(
        project_id="export-temp",
        molecule_name=molecule,
        brand_name=brand_name,
        therapy_area=therapy_area,
        indication=indication
    )
    buffer = generate_brand_plan_docx(plan)
    filename = f"{brand_name.replace(' ', '_')}_Brand_Plan.docx"
    
    return Response(
        content=buffer.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/export/pptx")
async def export_pitch_deck_pptx(
    molecule: str = Query(..., description="Molecule name"),
    brand_name: str = Query(..., description="Brand name"),
    therapy_area: str = Query("Cardiometabolic", description="Therapy area"),
    indication: str = Query("Heart Failure & CKD in T2D", description="Indication")
):
    plan = generate_strategic_brand_plan(
        project_id="export-temp",
        molecule_name=molecule,
        brand_name=brand_name,
        therapy_area=therapy_area,
        indication=indication
    )
    assets = generate_commercial_assets(
        molecule_name=molecule,
        brand_name=brand_name,
        indication=indication
    )
    buffer = generate_pitch_deck_pptx(plan, assets)
    filename = f"{brand_name.replace(' ', '_')}_Executive_Deck.pptx"
    
    return Response(
        content=buffer.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/export/xlsx")
async def export_financial_model_xlsx(
    brand_name: str = Query(..., description="Brand name"),
    therapy_area: str = Query("Cardiometabolic", description="Therapy area")
):
    forecast = calculate_market_forecast(therapy_area=therapy_area)
    buffer = generate_financial_model_xlsx(forecast, brand_name)
    filename = f"{brand_name.replace(' ', '_')}_Financial_Model.xlsx"
    
    return Response(
        content=buffer.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
