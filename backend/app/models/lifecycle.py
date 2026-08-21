from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class PatentRecord(BaseModel):
    patent_number: str
    expiry_date: str
    submission_date: Optional[str] = None
    drug_substance: bool = False
    drug_product: bool = False
    use_code: Optional[str] = None


class ExclusivityRecord(BaseModel):
    code: str
    expiry_date: str
    description: Optional[str] = None


class MarketedProduct(BaseModel):
    trade_name: str
    applicant: str
    applicant_full_name: Optional[str] = None
    strength: Optional[str] = None
    dosage_form_route: Optional[str] = None
    application_type: str          # "NDA" (innovator) or "ANDA" (generic)
    application_number: str
    approval_date: Optional[str] = None
    is_reference_listed_drug: bool = False
    therapeutic_equivalence_code: Optional[str] = None


class MoleculeLifecycle(BaseModel):
    """Patent, exclusivity, and competitive-entry picture for a molecule or FDC."""

    query: str
    display_name: str
    components: List[str] = []
    is_combination: bool = False

    innovator_company: Optional[str] = None
    innovator_brand: Optional[str] = None
    innovator_application: Optional[str] = None
    first_approval_date: Optional[str] = None

    patents: List[PatentRecord] = []
    latest_patent_expiry: Optional[str] = None
    exclusivity: List[ExclusivityRecord] = []

    generic_entrants: List[MarketedProduct] = []
    generic_entrant_count: int = 0
    first_generic_approval_date: Optional[str] = None
    all_products: List[MarketedProduct] = []

    data_sources: List[str] = []
    coverage_note: str = ""
    unavailable: List[str] = []
