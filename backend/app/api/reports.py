import re
from urllib.parse import quote

from fastapi import APIRouter, Query, Response, HTTPException, Request
from . import auth
from typing import List, Optional
from datetime import datetime
from ..models.reports import MLRAuditEntry
from ..services.ai_orchestrator import generate_strategic_brand_plan, generate_commercial_assets
from ..services.forecast_service import calculate_market_forecast
from ..services.pubchem_service import fetch_molecule_intelligence
from ..services.export_service import generate_brand_plan_docx, generate_pitch_deck_pptx, generate_financial_model_xlsx
from ..db import database as db

router = APIRouter(prefix="/api/reports", tags=["Report Center & MLR Audit"])


def _content_disposition(brand_name: str, suffix: str) -> str:
    """Build a Content-Disposition header that survives any brand name.

    Brand names reach this endpoint straight from user input, so they may carry
    non-Latin-1 characters (Devanagari, curly quotes pasted from Word) that
    cannot be encoded into an HTTP header, or path/CRLF characters that would
    let a caller steer the download filename. The ASCII fallback keeps old
    clients working; the RFC 5987 form carries the original name.
    """
    # Strip only what is unsafe in a filename or header (path separators,
    # reserved characters, control characters) so non-Latin scripts survive.
    stem = re.sub(r"[\\/:*?\"<>|\x00-\x1f\x7f]", "", brand_name).strip().replace(" ", "_")
    stem = re.sub(r"\.{2,}", ".", stem).strip("._") or "BrandPlan"
    stem = stem[:80]

    full = f"{stem}_{suffix}"
    ascii_fallback = full.encode("ascii", "ignore").decode("ascii").strip("._") or f"Export_{suffix}"
    return f"attachment; filename=\"{ascii_fallback}\"; filename*=UTF-8''{quote(full)}"


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


@router.post("/audit-trail", response_model=MLRAuditEntry, status_code=201)
async def create_audit_entry(entry: MLRAuditEntry, request: Request):
    """Record a new audit entry. Write-once — reusing an existing id is
    rejected rather than silently overwriting what it already recorded.

    Requires a logged-in session. `auditor` is always overwritten with the
    authenticated user's own name and email, never trusted from the request
    body — an audit trail whose "who did this" field is whatever the caller
    typed is exactly the unsourced claim this table exists to prevent.
    """
    user = auth.get_current_user(request)
    payload = entry.model_dump() if hasattr(entry, 'model_dump') else entry.dict()
    payload["auditor"] = f"{user.name} <{user.email}>"
    try:
        db.db_save_mlr_audit_log(payload)
    except db.AuditLogAlreadyExists as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return MLRAuditEntry(**payload)

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

    return Response(
        content=buffer.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": _content_disposition(brand_name, "Brand_Plan.docx")}
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

    return Response(
        content=buffer.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": _content_disposition(brand_name, "Executive_Deck.pptx")}
    )

@router.get("/export/xlsx")
async def export_financial_model_xlsx(
    brand_name: str = Query(..., description="Brand name"),
    therapy_area: str = Query("Cardiometabolic", description="Therapy area"),
    mrp_per_patient_year_inr: Optional[float] = Query(None, gt=0, le=100_000_000,
        description="India trade pricing (optional, supply all three or none): MRP per patient-year, INR."),
    ptr_per_patient_year_inr: Optional[float] = Query(None, gt=0, le=100_000_000,
        description="Price to Retailer per patient-year, INR."),
    pts_per_patient_year_inr: Optional[float] = Query(None, gt=0, le=100_000_000,
        description="Price to Stockist per patient-year, INR — manufacturer's own realization."),
):
    try:
        forecast = calculate_market_forecast(
            therapy_area=therapy_area,
            mrp_per_patient_year_inr=mrp_per_patient_year_inr,
            ptr_per_patient_year_inr=ptr_per_patient_year_inr,
            pts_per_patient_year_inr=pts_per_patient_year_inr,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    buffer = generate_financial_model_xlsx(forecast, brand_name)

    return Response(
        content=buffer.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": _content_disposition(brand_name, "Financial_Model.xlsx")}
    )
