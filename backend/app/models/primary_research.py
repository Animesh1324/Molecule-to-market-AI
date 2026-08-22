from typing import Dict, Optional

from pydantic import BaseModel


class RCPAEntry(BaseModel):
    id: str
    project_id: str
    pharmacy_name: str
    location: Optional[str] = None
    molecule_awareness: bool
    active_prescribing: bool
    rx_frequency_note: Optional[str] = None
    potential_rating: Optional[str] = None
    signal_note: str
    action_note: Optional[str] = None
    recorded_by: str
    recorded_at: str


class HCPQuestionnaire(BaseModel):
    id: str
    project_id: str
    specialty: str
    respondent_code: Optional[str] = None
    cost_barrier_rating: Optional[int] = None
    molecule_preference_rating: Optional[int] = None
    efficacy_rating: Optional[int] = None
    switch_intent: Optional[bool] = None
    key_quote: Optional[str] = None
    recorded_by: str
    recorded_at: str


class PrimaryResearchSummary(BaseModel):
    has_data: bool
    rcpa_total: int
    hcp_total: int
    rcpa_aware_count: Optional[int] = None
    rcpa_aware_percent: Optional[float] = None
    rcpa_active_count: Optional[int] = None
    rcpa_active_percent: Optional[float] = None
    rcpa_high_potential_count: Optional[int] = None
    hcp_avg_cost_barrier_rating: Optional[float] = None
    hcp_cost_barrier_respondents: Optional[int] = None
    hcp_avg_preference_rating: Optional[float] = None
    hcp_avg_efficacy_rating: Optional[float] = None
    hcp_switch_intent_count: Optional[int] = None
    hcp_switch_intent_percent: Optional[float] = None
    hcp_switch_intent_respondents: Optional[int] = None
    hcp_specialty_breakdown: Optional[Dict[str, int]] = None
