from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ScenarioProjections(BaseModel):
    year_1: float
    year_2: float
    year_3: float
    year_4: float
    year_5: float
    cagr_percentage: float

class DoctorSpecialtySegment(BaseModel):
    specialty: str # 'Cardiologists', 'Endocrinologists/Diabetologists', 'Nephrologists', 'Consultant Physicians'
    estimated_pool_size: int
    tier: str # 'Tier A+ (Key Opinion Leaders)', 'Tier A (High Volume Prescribers)', 'Tier B (Core Practice)'
    priority_level: str # 'Very High', 'High', 'Moderate'
    expected_reach_rate: float
    prescription_potential_per_month: int

class MarketForecast(BaseModel):
    therapy_area: str
    target_geography: str
    total_population: int
    prevalence_rate: float # e.g. 0.08 (8%)
    diagnosed_rate: float # e.g. 0.65 (65%)
    treated_rate: float # e.g. 0.50 (50%)
    brand_adoption_rate_y1: float # e.g. 0.05 (5%)
    annual_cost_per_patient_usd: float
    
    # Calculated patient pools
    prevalent_patient_pool: int
    diagnosed_patient_pool: int
    treated_patient_pool: int
    
    # Financial projections
    current_therapy_market_size_usd: float
    therapy_market_cagr: float
    
    # 3 Scenario 5-Year Forecasts
    conservative_scenario: ScenarioProjections
    realistic_scenario: ScenarioProjections
    aggressive_scenario: ScenarioProjections
    
    doctor_specialties: List[DoctorSpecialtySegment] = []
    region_wise_opportunity: Dict[str, str] = {}
    channel_strategy_breakdown: Dict[str, str] = {}
