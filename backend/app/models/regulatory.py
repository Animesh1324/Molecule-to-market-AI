from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class RegulatoryAgencyInfo(BaseModel):
    agency_name: str # 'US FDA', 'CDSCO (India)', 'EMA (European Union)', 'WHO'
    status: str # 'Approved', 'Under Review', 'Investigational', 'Generic Approved'
    approval_year: Optional[int] = None
    innovator_brand_name: Optional[str] = None
    application_numbers: List[str] = []
    approved_indications: List[str] = []
    dosage_and_administration_summary: str = ""
    boxed_warnings: List[str] = []
    warnings_and_precautions: List[str] = []
    contraindications: List[str] = []
    source_spl_or_url: Optional[str] = None

class RegulatoryIntelligence(BaseModel):
    generic_name: str
    us_fda: RegulatoryAgencyInfo
    india_cdsco: RegulatoryAgencyInfo
    eu_ema: RegulatoryAgencyInfo
    generic_vs_innovator_status: str # 'Innovator Exclusivity', 'Genericized / Multi-source', 'Patent Cliff Approaching'
    patent_expiry_timeline: Optional[str] = None
    key_label_claims_verified: List[str] = []
    ai_strategic_interpretation: List[str] = []
    compliance_fair_balance_notes: str
