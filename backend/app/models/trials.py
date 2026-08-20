from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ClinicalTrial(BaseModel):
    nct_id: str
    title: str
    acronym: Optional[str] = None
    sponsor: str
    sponsor_type: str = "Industry" # 'Industry', 'NIH', 'Academic/Other'
    phase: str # 'Phase 1', 'Phase 2', 'Phase 3', 'Phase 4', 'Phase 1/Phase 2', 'Phase 2/Phase 3'
    status: str # 'RECRUITING', 'ACTIVE_NOT_RECRUITING', 'COMPLETED', 'TERMINATED', 'WITHDRAWN'
    indication: str
    study_design: Dict[str, Any] = {} # { allocation, intervention_model, masking, primary_purpose }
    interventions: List[str] = []
    primary_endpoints: List[str] = []
    secondary_endpoints: List[str] = []
    enrollment: Optional[int] = None
    geography: List[str] = []
    start_date: Optional[str] = None
    completion_date: Optional[str] = None
    results_available: bool = False
    results_summary: Optional[str] = None
    competitor_molecules: List[str] = []
    url: str

class ClinicalTrialLandscape(BaseModel):
    total_trials_found: int
    phase_distribution: Dict[str, int] = {}
    status_distribution: Dict[str, int] = {}
    landmark_trials: List[ClinicalTrial] = []
    all_trials: List[ClinicalTrial] = []
