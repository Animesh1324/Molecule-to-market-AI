from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..models.primary_research import HCPQuestionnaire, PrimaryResearchSummary, RCPAEntry
from ..services import primary_research_service as research

router = APIRouter(prefix="/api/primary-research", tags=["Primary Research: RCPA & HCP Survey"])


class RCPAEntryRequest(BaseModel):
    project_id: str = Field(..., min_length=1)
    pharmacy_name: str = Field(..., min_length=1, max_length=200)
    signal_note: str = Field(..., min_length=3, max_length=1000,
        description="What was actually observed at this visit — mandatory")
    recorded_by: str = Field(..., min_length=1, max_length=120)
    location: Optional[str] = Field(None, max_length=200)
    molecule_awareness: bool = False
    active_prescribing: bool = False
    rx_frequency_note: Optional[str] = Field(None, max_length=120)
    potential_rating: Optional[str] = Field(None, max_length=20, description="'High' | 'Medium' | 'Low'")
    action_note: Optional[str] = Field(None, max_length=1000)


class HCPQuestionnaireRequest(BaseModel):
    project_id: str = Field(..., min_length=1)
    specialty: str = Field(..., min_length=1, max_length=120)
    recorded_by: str = Field(..., min_length=1, max_length=120)
    respondent_code: Optional[str] = Field(None, max_length=60,
        description="An anonymized/coded label — not necessarily the respondent's real name")
    cost_barrier_rating: Optional[int] = Field(None, ge=0, le=10)
    molecule_preference_rating: Optional[int] = Field(None, ge=0, le=5)
    efficacy_rating: Optional[int] = Field(None, ge=0, le=5)
    switch_intent: Optional[bool] = None
    key_quote: Optional[str] = Field(None, max_length=1000)


@router.get("/rcpa", response_model=List[RCPAEntry])
async def get_rcpa_entries(project_id: str = Query(..., description="Project this audit belongs to")):
    return research.list_rcpa_entries(project_id)


@router.post("/rcpa", response_model=RCPAEntry)
async def add_rcpa_entry(request: RCPAEntryRequest):
    try:
        return research.add_rcpa_entry(
            project_id=request.project_id,
            pharmacy_name=request.pharmacy_name,
            signal_note=request.signal_note,
            recorded_by=request.recorded_by,
            location=request.location,
            molecule_awareness=request.molecule_awareness,
            active_prescribing=request.active_prescribing,
            rx_frequency_note=request.rx_frequency_note,
            potential_rating=request.potential_rating,
            action_note=request.action_note,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.delete("/rcpa/{entry_id}")
async def remove_rcpa_entry(entry_id: str):
    if not research.delete_rcpa_entry(entry_id):
        raise HTTPException(status_code=404, detail="No RCPA entry with that id.")
    return {"deleted": entry_id}


@router.get("/questionnaire", response_model=List[HCPQuestionnaire])
async def get_hcp_questionnaires(project_id: str = Query(..., description="Project this survey belongs to")):
    return research.list_hcp_questionnaires(project_id)


@router.post("/questionnaire", response_model=HCPQuestionnaire)
async def add_hcp_questionnaire(request: HCPQuestionnaireRequest):
    try:
        return research.add_hcp_questionnaire(
            project_id=request.project_id,
            specialty=request.specialty,
            recorded_by=request.recorded_by,
            respondent_code=request.respondent_code,
            cost_barrier_rating=request.cost_barrier_rating,
            molecule_preference_rating=request.molecule_preference_rating,
            efficacy_rating=request.efficacy_rating,
            switch_intent=request.switch_intent,
            key_quote=request.key_quote,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.delete("/questionnaire/{entry_id}")
async def remove_hcp_questionnaire(entry_id: str):
    if not research.delete_hcp_questionnaire(entry_id):
        raise HTTPException(status_code=404, detail="No questionnaire entry with that id.")
    return {"deleted": entry_id}


@router.get("/summary", response_model=PrimaryResearchSummary)
async def get_primary_research_summary(project_id: str = Query(..., description="Project to summarize")):
    """Real aggregates computed only from entries on file for this project."""
    return research.summarize_primary_research(project_id)
