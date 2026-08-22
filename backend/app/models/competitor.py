from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class CompetitorProfile(BaseModel):
    id: str
    molecule: str
    brand_name: str
    company: str
    indication: str = ""
    strengths_available: List[str] = []
    dosage_form: str = ""
    price_per_month_usd: Optional[float] = None
    key_claims: List[str] = []
    positioning: str = ""
    packaging_direction: str = ""
    visual_aid_angle: str = ""
    doctor_messaging: str = ""
    patient_promise: str = ""
    strengths: List[str] = []
    weaknesses: List[str] = []
    market_share_percentage: float = 0.0
    quadrant_x_efficacy: float = 0.0  # -10 to +10
    quadrant_y_safety_convenience: float = 0.0  # -10 to +10

    # Provenance. "curated" rows carry hand-checked strategy text; "secondary_market"
    # rows are measured sales facts from an ingested audit extract and deliberately
    # leave the strategy fields blank rather than inventing them.
    data_source: str = "curated"
    source_label: Optional[str] = None

    # Measured market facts. Present only on secondary_market rows.
    market_value: Optional[float] = None          # in `value_unit` of the dataset
    value_unit: Optional[str] = None
    market_value_prev: Optional[float] = None
    market_growth_percent: Optional[float] = None
    units_latest: Optional[float] = None
    ownership: Optional[str] = None               # INDIAN / MNC
    pack_count: Optional[int] = None
    period: Optional[str] = None
    is_combination: bool = False
    therapy_group: Optional[str] = None
    subgroup: Optional[str] = None


class ClassRival(BaseModel):
    """A different molecule competing in the same therapeutic group."""
    molecule_desc: str
    molecule_key: Optional[str] = None
    value_latest: float = 0.0
    growth_percent: Optional[float] = None
    brand_count: int = 0
    class_share_percent: float = 0.0


class CompanyShare(BaseModel):
    company: str
    ownership: Optional[str] = None
    value_latest: float = 0.0
    growth_percent: Optional[float] = None
    brand_count: int = 0
    market_share_percent: float = 0.0


class MarketSummary(BaseModel):
    """Measured size of the molecule's market, straight from an extract."""
    has_data: bool = False
    market: Optional[str] = None
    period: Optional[str] = None
    value_unit: Optional[str] = None
    market_size: Optional[float] = None
    market_size_prev: Optional[float] = None
    market_growth_percent: Optional[float] = None
    total_brands: int = 0
    total_companies: int = 0
    therapy_group: Optional[str] = None
    group_value: Optional[float] = None
    source_files: List[str] = []


class SWOTAnalysis(BaseModel):
    strengths: List[str] = []
    weaknesses: List[str] = []
    opportunities: List[str] = []
    threats: List[str] = []


class CompetitorIntelligence(BaseModel):
    molecule: str
    competitors: List[CompetitorProfile] = []
    swot_analysis: SWOTAnalysis
    positioning_gap_summary: str
    head_to_head_differentiators: List[str] = []

    # Secondary-data layer. Empty when no extract covers this molecule.
    market_summary: MarketSummary = Field(default_factory=MarketSummary)
    company_leaderboard: List[CompanyShare] = []
    class_rivals: List[ClassRival] = []
    data_sources: List[str] = []
