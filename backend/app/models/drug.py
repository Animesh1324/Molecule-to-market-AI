"""Request/response schemas for the Drug Intelligence module."""
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class DrugSourceOut(BaseModel):
    """Provenance for one fact set. Present on every drug the API returns."""

    id: Optional[str] = None
    source_name: str
    source_url: Optional[str] = None
    source_identifier: Optional[str] = None
    data_version: Optional[str] = None
    published_at: Optional[str] = None
    attribution: Optional[str] = None
    confidence: str = "unverified"
    retrieved_at: Optional[str] = None


class DrugOut(BaseModel):
    id: str
    generic_name: str
    brand_name: Optional[str] = None
    active_ingredients: List[str] = []
    drug_class: Optional[str] = None
    therapeutic_class: Optional[str] = None
    dosage_forms: List[str] = []
    strengths: List[str] = []
    routes: List[str] = []
    manufacturer: Optional[str] = None

    indications: Optional[str] = None
    dosage: Optional[str] = None
    contraindications: Optional[str] = None
    warnings: Optional[str] = None
    precautions: Optional[str] = None
    adverse_effects: Optional[str] = None
    drug_interactions: Optional[str] = None
    pregnancy_information: Optional[str] = None
    lactation_information: Optional[str] = None
    mechanism: Optional[str] = None

    status: str = "active"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    sources: List[DrugSourceOut] = []


class DrugPage(BaseModel):
    """Paginated envelope shared by list and search."""

    items: List[DrugOut] = []
    total: int = 0
    page: int = 1
    page_size: int = 25
    has_more: bool = False


class DrugSearchResult(DrugPage):
    query: str = ""
    matched_on: str = ""
    ingested_on_demand: bool = False
    note: str = ""


class InteractionOut(BaseModel):
    id: Optional[str] = None
    drug_a: str
    drug_b: str
    severity: str = "unknown"
    description: Optional[str] = None
    management: Optional[str] = None
    source_name: str = "unknown"
    source_url: Optional[str] = None
    retrieved_at: Optional[str] = None


class InteractionReport(BaseModel):
    drug: str
    interactions: List[InteractionOut] = []
    total: int = 0
    coverage_note: str = ""


class CompareRequest(BaseModel):
    drug_a: str = Field(..., min_length=1, max_length=200)
    drug_b: str = Field(..., min_length=1, max_length=200)
    ingest_if_missing: bool = True


class ComparisonField(BaseModel):
    field: str
    label: str
    drug_a_value: Optional[str] = None
    drug_b_value: Optional[str] = None
    both_available: bool = False
    differs: bool = False


class DrugComparison(BaseModel):
    drug_a: Optional[DrugOut] = None
    drug_b: Optional[DrugOut] = None
    fields: List[ComparisonField] = []
    shared_interactions: List[InteractionOut] = []
    fields_missing_for_both: List[str] = []
    comparison_note: str = ""
    caveat: str = ""


class ManualDrugIn(BaseModel):
    """Payload for a hand-entered drug record."""

    generic_name: str = Field(..., min_length=1, max_length=200)
    brand_name: Optional[str] = Field(None, max_length=200)
    active_ingredients: Optional[List[str]] = None
    drug_class: Optional[str] = None
    therapeutic_class: Optional[str] = None
    dosage_forms: Optional[List[str]] = None
    strengths: Optional[List[str]] = None
    routes: Optional[List[str]] = None
    indications: Optional[str] = None
    dosage: Optional[str] = None
    contraindications: Optional[str] = None
    warnings: Optional[str] = None
    precautions: Optional[str] = None
    adverse_effects: Optional[str] = None
    drug_interactions: Optional[str] = None
    pregnancy_information: Optional[str] = None
    lactation_information: Optional[str] = None
    mechanism: Optional[str] = None
    manufacturer: Optional[str] = None
    source_note: Optional[str] = Field(None, max_length=500)
    entered_by: Optional[str] = Field(None, max_length=120)


class RefreshRequest(BaseModel):
    queries: List[str] = Field(..., min_length=1, max_length=25)
    sources: Optional[List[str]] = None


class SourceOutcome(BaseModel):
    source_name: str
    query: str
    succeeded: bool
    records_written: int = 0
    message: str = ""


class RefreshReport(BaseModel):
    outcomes: List[SourceOutcome] = []
    total_records_written: int = 0
    sources_available: List[Dict[str, Any]] = []


# --- PMT analysis layer (generated, never source fact) -----------------------

class PMTProductProfile(BaseModel):
    brand: Optional[str] = None
    generic: Optional[str] = None
    molecule: Optional[str] = None
    company: Optional[str] = None
    drug_class: Optional[str] = None
    indication_summary: Optional[str] = None
    dosage_summary: Optional[str] = None


class PMTAnalysis(BaseModel):
    """Software-generated strategic reading. Never presented as source fact."""

    analysis_type: str = "AI/Software Analysis"
    disclaimer: str = (
        "Generated by this application from the source records shown alongside it. "
        "Not a statement from any regulator or data provider, and not a clinical "
        "claim. Verify every point before external use."
    )
    product_profile: PMTProductProfile = PMTProductProfile()
    competitive_products: List[PMTProductProfile] = []
    positioning_observations: List[str] = []
    differentiation_candidates: List[str] = []
    competitive_advantages: List[str] = []
    competitive_disadvantages: List[str] = []
    target_patient_segment: List[str] = []
    target_physician_segment: List[str] = []
    evidence_gaps: List[str] = []
    source_records_used: List[str] = []
