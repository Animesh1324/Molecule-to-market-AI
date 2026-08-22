from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class BrandPlanSection(BaseModel):
    section_id: str
    section_title: str
    section_category: str
    content_markdown: str
    key_takeaways: List[str] = []
    citations: List[Dict[str, str]] = [] # [{ "ref": "PMID:32970396", "note": "DAPA-CKD Trial" }]

class KPIMetric(BaseModel):
    kpi_name: str
    category: str # 'Commercial', 'Medical/Clinical', 'Prescriber Reach', 'Digital Adoption'
    target_q1: str
    target_q2: str
    target_q4: str
    target_year1: str

class MonthlyTacticalMilestone(BaseModel):
    month_number: int
    month_name: str
    activity: str
    responsible_team: str # 'Brand Team', 'Medical Affairs', 'Field Force', 'Regulatory', 'Digital Marketing'
    status: str = "Planned"

class CompleteBrandPlan(BaseModel):
    project_id: str
    molecule_name: str
    brand_name: str
    therapy_area: str
    indication: str
    target_geography: str
    
    # 12 Core Strategic Sections
    mission: str
    vision: str
    brand_objective: str
    therapy_area_opportunity: str
    target_customer_and_patient_profile: str
    doctor_and_market_insights: str
    competitor_gap_and_differentiation: str
    positioning_statement: str
    brand_promise_and_rtb: str # Reasons to Believe
    key_messages_and_claim_strategy: str
    commercial_launch_strategy: str
    kol_and_cme_strategy: str
    digital_and_sales_force_strategy: str
    
    sections: List[BrandPlanSection] = []
    monthly_action_plan: List[MonthlyTacticalMilestone] = []
    kpi_scorecard: List[KPIMetric] = []
    # Never defaults true. A plan is signoff-ready only when a human reviewer
    # has cleared it, and nothing in this application can make that assertion —
    # so an omitted field must mean "not ready", not "ready".
    mlr_compliance_signoff_ready: bool = False
    last_updated: str

    # Drafting provenance. `ai_drafted` marks text a model wrote rather than the
    # deterministic template, so a reviewer can tell the two apart on sight.
    ai_drafted: bool = False
    ai_model: Optional[str] = None
    ai_review_flags: List[str] = []
    ai_status: str = "template"  # template | drafted | drafting_failed
