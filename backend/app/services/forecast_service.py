import math
from typing import Dict, Any, List
from ..models.forecast import MarketForecast, ScenarioProjections, DoctorSpecialtySegment

def calculate_market_forecast(
    therapy_area: str = "Cardiometabolic",
    target_geography: str = "Global",
    total_population: int = 330000000, # e.g., US adult population proxy
    prevalence_rate: float = 0.105, # 10.5% prevalence (e.g., T2DM/CKD/HF)
    diagnosed_rate: float = 0.72,   # 72% diagnosis rate
    treated_rate: float = 0.60,     # 60% of diagnosed receiving treatment
    brand_adoption_rate_y1: float = 0.04, # 4% initial brand market share
    annual_cost_per_patient_usd: float = 3600.0, # Net brand price per patient-year ($300/month)
) -> MarketForecast:
    """Computes pure mathematical epidemiological patient funnel and 5-year multi-scenario revenue projections."""
    
    # 1. Patient Funnel Mathematics
    prevalent_pool = int(total_population * prevalence_rate)
    diagnosed_pool = int(prevalent_pool * diagnosed_rate)
    treated_pool = int(diagnosed_pool * treated_rate)
    
    # Total available treated therapy market value
    therapy_market_size = treated_pool * annual_cost_per_patient_usd
    
    # 2. Scenario 1: Conservative Projection
    # Assumptions: Slower uptake, strong generic resistance, modest market share peaking at 7.5%
    c_y1 = treated_pool * (brand_adoption_rate_y1 * 0.75) * annual_cost_per_patient_usd
    c_y2 = treated_pool * (brand_adoption_rate_y1 * 1.15) * annual_cost_per_patient_usd
    c_y3 = treated_pool * (brand_adoption_rate_y1 * 1.55) * annual_cost_per_patient_usd
    c_y4 = treated_pool * (brand_adoption_rate_y1 * 1.85) * annual_cost_per_patient_usd
    c_y5 = treated_pool * (brand_adoption_rate_y1 * 2.10) * annual_cost_per_patient_usd
    c_cagr = ((c_y5 / c_y1) ** (1/4) - 1) * 100 if c_y1 > 0 else 0.0
    
    conservative = ScenarioProjections(
        year_1=round(c_y1, 2),
        year_2=round(c_y2, 2),
        year_3=round(c_y3, 2),
        year_4=round(c_y4, 2),
        year_5=round(c_y5, 2),
        cagr_percentage=round(c_cagr, 2)
    )
    
    # 3. Scenario 2: Realistic (Base-Case) Projection
    # Assumptions: Solid guideline endorsement, standard field force execution, peaking at 14%
    r_y1 = treated_pool * brand_adoption_rate_y1 * annual_cost_per_patient_usd
    r_y2 = treated_pool * (brand_adoption_rate_y1 * 1.85) * annual_cost_per_patient_usd
    r_y3 = treated_pool * (brand_adoption_rate_y1 * 2.65) * annual_cost_per_patient_usd
    r_y4 = treated_pool * (brand_adoption_rate_y1 * 3.25) * annual_cost_per_patient_usd
    r_y5 = treated_pool * (brand_adoption_rate_y1 * 3.75) * annual_cost_per_patient_usd
    r_cagr = ((r_y5 / r_y1) ** (1/4) - 1) * 100 if r_y1 > 0 else 0.0
    
    realistic = ScenarioProjections(
        year_1=round(r_y1, 2),
        year_2=round(r_y2, 2),
        year_3=round(r_y3, 2),
        year_4=round(r_y4, 2),
        year_5=round(r_y5, 2),
        cagr_percentage=round(r_cagr, 2)
    )
    
    # 4. Scenario 3: Aggressive Projection
    # Assumptions: Rapid first-line guideline adoption, best-in-class digital & KOL execution, peaking at 22%
    a_y1 = treated_pool * (brand_adoption_rate_y1 * 1.35) * annual_cost_per_patient_usd
    a_y2 = treated_pool * (brand_adoption_rate_y1 * 2.60) * annual_cost_per_patient_usd
    a_y3 = treated_pool * (brand_adoption_rate_y1 * 3.90) * annual_cost_per_patient_usd
    a_y4 = treated_pool * (brand_adoption_rate_y1 * 4.90) * annual_cost_per_patient_usd
    a_y5 = treated_pool * (brand_adoption_rate_y1 * 5.60) * annual_cost_per_patient_usd
    a_cagr = ((a_y5 / a_y1) ** (1/4) - 1) * 100 if a_y1 > 0 else 0.0
    
    aggressive = ScenarioProjections(
        year_1=round(a_y1, 2),
        year_2=round(a_y2, 2),
        year_3=round(a_y3, 2),
        year_4=round(a_y4, 2),
        year_5=round(a_y5, 2),
        cagr_percentage=round(a_cagr, 2)
    )
    
    # 5. Doctor Specialty Segments
    doctor_segments = [
        DoctorSpecialtySegment(
            specialty="Cardiologists & Heart Failure Specialists",
            estimated_pool_size=32000,
            tier="Tier A+ (Key Opinion Leaders)",
            priority_level="Very High",
            expected_reach_rate=0.85,
            prescription_potential_per_month=140
        ),
        DoctorSpecialtySegment(
            specialty="Endocrinologists & Diabetologists",
            estimated_pool_size=28000,
            tier="Tier A (High Volume Prescribers)",
            priority_level="Very High",
            expected_reach_rate=0.90,
            prescription_potential_per_month=220
        ),
        DoctorSpecialtySegment(
            specialty="Nephrologists",
            estimated_pool_size=14000,
            tier="Tier A (Specialist Target)",
            priority_level="High",
            expected_reach_rate=0.75,
            prescription_potential_per_month=95
        ),
        DoctorSpecialtySegment(
            specialty="Consultant Internal Medicine & Primary Care",
            estimated_pool_size=180000,
            tier="Tier B (Broad Maintenance Volume)",
            priority_level="Moderate",
            expected_reach_rate=0.55,
            prescription_potential_per_month=45
        )
    ]
    
    region_breakdown = {
        "North America (US/Canada)": "48% of global revenue opportunity; premium reimbursement with focus on commercial payer formulary coverage.",
        "Europe (EU5 + UK)": "24% of revenue; statutory health insurance pricing negotiations with strong health economics (HTA) evidence requirements.",
        "Asia-Pacific (India, China, Japan)": "22% of revenue; high patient volume with emerging middle-class out-of-pocket & private insurance growth.",
        "Latin America & MEA": "6% of revenue; tender-based hospital supply and key private medical centers."
    }
    
    channel_strategy = {
        "Direct Field Force Detailing": "60% of commercial budget; focused face-to-face scientific calls on Tier A/A+ cardiologists and diabetologists.",
        "Omnichannel Digital Detailing & Webinars": "20% of budget; on-demand digital medical education, interactive case simulators, and clinical trial podcasts.",
        "Hospital & Institutional Tenders": "15% of budget; formulary inclusion in top 500 tertiary cardiac and renal teaching hospitals.",
        "Patient Adherence & Co-Pay Programs": "5% of budget; digital companion app, dosage reminder SMS, and co-pay assistance cards."
    }
    
    return MarketForecast(
        therapy_area=therapy_area,
        target_geography=target_geography,
        total_population=total_population,
        prevalence_rate=prevalence_rate,
        diagnosed_rate=diagnosed_rate,
        treated_rate=treated_rate,
        brand_adoption_rate_y1=brand_adoption_rate_y1,
        annual_cost_per_patient_usd=annual_cost_per_patient_usd,
        prevalent_patient_pool=prevalent_pool,
        diagnosed_patient_pool=diagnosed_pool,
        treated_patient_pool=treated_pool,
        current_therapy_market_size_usd=round(therapy_market_size, 2),
        therapy_market_cagr=6.8,
        conservative_scenario=conservative,
        realistic_scenario=realistic,
        aggressive_scenario=aggressive,
        doctor_specialties=doctor_segments,
        region_wise_opportunity=region_breakdown,
        channel_strategy_breakdown=channel_strategy
    )
