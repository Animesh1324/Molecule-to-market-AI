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

class TradePriceStructure(BaseModel):
    """India trade price structure: MRP flows down to the manufacturer's own
    realization through two margins. Figures are per patient-year, matching
    the granularity of the rest of the forecast, in INR.

    MRP (Maximum Retail Price) is what the patient pays. PTR (Price to
    Retailer) is what the retailer pays the stockist/distributor. PTS (Price
    to Stockist) is what the stockist pays the company — the manufacturer's
    actual realization per patient-year, and the correct basis for a revenue
    forecast. A forecast built on MRP overstates manufacturer revenue by the
    full retailer and stockist margin; PTS is what the company keeps.
    """
    mrp_per_patient_year: float
    ptr_per_patient_year: float
    pts_per_patient_year: float
    retailer_margin_amount: float       # mrp - ptr
    retailer_margin_percent: float      # retailer_margin_amount / mrp * 100
    stockist_margin_amount: float       # ptr - pts
    stockist_margin_percent: float      # stockist_margin_amount / ptr * 100
    manufacturer_realization_percent_of_mrp: float  # pts / mrp * 100


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

    # India trade pricing. None unless mrp/ptr/pts were supplied — a forecast
    # built for a market with no trade-price input must not imply one exists.
    trade_price_structure: Optional[TradePriceStructure] = None
    # treated_patient_pool x pts_per_patient_year — the manufacturer's actual
    # addressable revenue at trade price, distinct from a patient-facing,
    # MRP-based market size which overstates what the company itself earns.
    therapy_market_size_inr_at_trade_price: Optional[float] = None
