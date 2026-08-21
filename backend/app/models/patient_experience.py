from pydantic import BaseModel
from typing import List, Optional


class ReportedProblem(BaseModel):
    term: str
    report_count: int
    share_of_reports: float


class DemographicSplit(BaseModel):
    label: str
    count: int


class PatientExperience(BaseModel):
    """Real-world tolerability and adherence signal for a molecule or FDC."""

    query: str
    display_name: str
    components: List[str] = []
    is_combination: bool = False

    total_reports: int = 0
    serious_reports: int = 0
    non_serious_reports: int = 0

    top_reported_problems: List[ReportedProblem] = []
    discontinuation_signals: List[ReportedProblem] = []
    off_label_use_reports: int = 0

    age_distribution: List[DemographicSplit] = []
    sex_distribution: List[DemographicSplit] = []

    patient_counselling_from_label: List[str] = []
    adherence_considerations: List[str] = []

    data_sources: List[str] = []
    coverage_note: str = ""
    interpretation_caveat: str = ""
