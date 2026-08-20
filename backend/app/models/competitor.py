from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class CompetitorProfile(BaseModel):
    id: str
    molecule: str
    brand_name: str
    company: str
    indication: str
    strengths_available: List[str] = []
    dosage_form: str
    price_per_month_usd: Optional[float] = None
    key_claims: List[str] = []
    positioning: str
    packaging_direction: str
    visual_aid_angle: str
    doctor_messaging: str
    patient_promise: str
    strengths: List[str] = []
    weaknesses: List[str] = []
    market_share_percentage: float = 0.0
    quadrant_x_efficacy: float = 0.0 # -10 to +10
    quadrant_y_safety_convenience: float = 0.0 # -10 to +10

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
