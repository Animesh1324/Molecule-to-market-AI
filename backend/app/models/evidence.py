from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ResearchPaper(BaseModel):
    id: str
    pmid: Optional[str] = None
    pmcid: Optional[str] = None
    doi: Optional[str] = None
    title: str
    authors: List[str] = []
    journal: str
    publication_year: int
    study_type: str # 'Meta-Analysis', 'Systematic Review', 'Randomized Controlled Trial', 'Cohort Study', 'Review', 'Guideline'
    evidence_level: str # 'Level 1 (Highest)', 'Level 2', 'Level 3'
    sample_size: Optional[int] = None
    primary_endpoint_result: Optional[str] = None
    hazard_ratio: Optional[str] = None
    relative_risk_reduction: Optional[str] = None
    p_value: Optional[str] = None
    key_findings: str
    limitations: str
    claim_support_potential: str
    relevance_score: float = 0.95
    url: Optional[str] = None

class ClaimEvidenceMapping(BaseModel):
    claim_text: str
    category: str # 'Efficacy', 'Cardiovascular', 'Renal', 'Safety', 'Dosing'
    strength_of_evidence: str # 'High', 'Moderate', 'Emerging'
    supported_by_papers: List[ResearchPaper]
    label_status: str # 'On-Label Approved', 'Supported by Clinical Trials', 'Exploratory'
