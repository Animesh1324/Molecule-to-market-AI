import re
from urllib.parse import quote

from fastapi import APIRouter, Query, Response, HTTPException, Request
from . import auth
from typing import List, Optional
from datetime import datetime
from ..models.brand_plan import CompleteBrandPlan
from ..models.reports import MLRAuditEntry
from ..services.ai_orchestrator import generate_strategic_brand_plan, generate_commercial_assets
from ..services.competitor_service import generate_competitor_intelligence
from ..services.forecast_service import calculate_market_forecast
from ..services.pubchem_service import fetch_molecule_intelligence
from ..services.regulatory_service import fetch_regulatory_intelligence
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

def _load_or_generate_plan(
    project_id: Optional[str], molecule: str, brand_name: str, therapy_area: str, indication: str,
) -> CompleteBrandPlan:
    """Export the project's own saved plan when one exists, not a disposable fresh one.

    Without a matching saved plan, an export previously always regenerated the
    bare deterministic template from scratch — discarding any AI-drafted
    content, edits, or competitor/forecast data already built up for that
    project. A `project_id` that resolves to a saved plan takes precedence
    over the query-string molecule/brand fields, which then only label a
    freshly generated fallback plan.
    """
    if project_id:
        existing = db.db_get_brand_plan(project_id)
        if existing:
            try:
                return CompleteBrandPlan(**existing)
            except Exception:
                pass
    return generate_strategic_brand_plan(
        project_id=project_id or "export-temp",
        molecule_name=molecule,
        brand_name=brand_name,
        therapy_area=therapy_area,
        indication=indication,
    )


@router.get("/export/docx")
async def export_brand_plan_docx(
    molecule: str = Query(..., description="Molecule name"),
    brand_name: str = Query(..., description="Brand name"),
    therapy_area: str = Query("Cardiometabolic", description="Therapy area"),
    indication: str = Query("Heart Failure & CKD in T2D", description="Indication"),
    project_id: Optional[str] = Query(None, description="Export this project's own saved plan, if one exists"),
):
    plan = _load_or_generate_plan(project_id, molecule, brand_name, therapy_area, indication)
    molecule_profile = None
    try:
        molecule_profile = await fetch_molecule_intelligence(molecule)
    except Exception:
        pass
    buffer = generate_brand_plan_docx(plan, molecule_profile)

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
    indication: str = Query("Heart Failure & CKD in T2D", description="Indication"),
    project_id: Optional[str] = Query(None, description="Export this project's own saved plan, if one exists"),
    prevalence_rate: Optional[float] = Query(None, gt=0, le=1, description="Current forecast assumption, to keep the export in sync with the on-screen model"),
    diagnosed_rate: Optional[float] = Query(None, gt=0, le=1),
    treated_rate: Optional[float] = Query(None, gt=0, le=1),
    brand_adoption_rate_y1: Optional[float] = Query(None, gt=0, le=1),
    annual_cost_per_patient_usd: Optional[float] = Query(None, gt=0, le=10_000_000),
    mrp_per_patient_year_inr: Optional[float] = Query(None, gt=0, le=100_000_000),
    ptr_per_patient_year_inr: Optional[float] = Query(None, gt=0, le=100_000_000),
    pts_per_patient_year_inr: Optional[float] = Query(None, gt=0, le=100_000_000),
):
    plan = _load_or_generate_plan(project_id, molecule, brand_name, therapy_area, indication)
    assets = generate_commercial_assets(
        molecule_name=molecule,
        brand_name=brand_name,
        indication=indication
    )

    molecule_profile = None
    regulatory = None
    competitor_data = None
    forecast = None
    try:
        profile_result = await fetch_molecule_intelligence(molecule)
        if profile_result is not None:
            molecule_profile = profile_result.model_dump() if hasattr(profile_result, "model_dump") else profile_result.dict()
    except Exception:
        pass
    try:
        regulatory_result = await fetch_regulatory_intelligence(molecule)
        if regulatory_result is not None:
            regulatory = regulatory_result.model_dump() if hasattr(regulatory_result, "model_dump") else regulatory_result.dict()
    except Exception:
        pass
    try:
        competitor_result = generate_competitor_intelligence(molecule, indication)
        competitor_data = competitor_result.model_dump() if hasattr(competitor_result, "model_dump") else competitor_result.dict()
    except Exception:
        pass
    # Only forecast when at least one assumption was supplied — an export
    # with no forecast context on screen should say so, not silently invent
    # a forecast from default epidemiology assumptions the user never set.
    if any(v is not None for v in (prevalence_rate, diagnosed_rate, treated_rate, brand_adoption_rate_y1, annual_cost_per_patient_usd)):
        try:
            forecast = calculate_market_forecast(
                therapy_area=therapy_area,
                prevalence_rate=prevalence_rate if prevalence_rate is not None else 0.105,
                diagnosed_rate=diagnosed_rate if diagnosed_rate is not None else 0.72,
                treated_rate=treated_rate if treated_rate is not None else 0.60,
                brand_adoption_rate_y1=brand_adoption_rate_y1 if brand_adoption_rate_y1 is not None else 0.04,
                annual_cost_per_patient_usd=annual_cost_per_patient_usd if annual_cost_per_patient_usd is not None else 3600.0,
                mrp_per_patient_year_inr=mrp_per_patient_year_inr,
                ptr_per_patient_year_inr=ptr_per_patient_year_inr,
                pts_per_patient_year_inr=pts_per_patient_year_inr,
            )
        except ValueError:
            pass

    buffer = generate_pitch_deck_pptx(
        plan, assets,
        competitor_data=competitor_data, regulatory=regulatory, molecule=molecule_profile, forecast=forecast,
    )

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
