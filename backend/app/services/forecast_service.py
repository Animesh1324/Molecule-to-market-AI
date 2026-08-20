import math
from typing import Dict, Any, List, Optional
from ..models.forecast import MarketForecast, ScenarioProjections, DoctorSpecialtySegment

# Share multipliers applied to the Year-1 adoption rate, per scenario.
# These are planning heuristics, not sourced market data — the caller is
# expected to replace them with validated uptake assumptions before the
# forecast is used in a real brand plan.
SCENARIO_CURVES: Dict[str, List[float]] = {
    "conservative": [0.75, 1.15, 1.55, 1.85, 2.10],
    "realistic": [1.00, 1.85, 2.65, 3.25, 3.75],
    "aggressive": [1.35, 2.60, 3.90, 4.90, 5.60],
}


def _build_scenario(treated_pool: int, adoption_y1: float, price: float, curve: List[float]) -> ScenarioProjections:
    """Project 5 years of revenue, clamping brand share to a possible range.

    Share is capped at 100% of the treated pool: a high Year-1 adoption input
    multiplied by the later-year curve can otherwise imply a brand holding more
    patients than exist in the market.
    """
    revenues = []
    for multiplier in curve:
        share = min(adoption_y1 * multiplier, 1.0)
        revenues.append(treated_pool * share * price)

    cagr = 0.0
    if revenues[0] > 0 and revenues[4] > 0:
        cagr = ((revenues[4] / revenues[0]) ** (1 / 4) - 1) * 100

    return ScenarioProjections(
        year_1=round(revenues[0], 2),
        year_2=round(revenues[1], 2),
        year_3=round(revenues[2], 2),
        year_4=round(revenues[3], 2),
        year_5=round(revenues[4], 2),
        cagr_percentage=round(cagr, 2),
    )


# Prescriber panels keyed by therapy area. Pool sizes are US-scale planning
# defaults and must be replaced with sourced prescriber counts for the actual
# target geography before the forecast is used commercially.
SPECIALTY_PANELS: Dict[str, List[Dict[str, Any]]] = {
    "cardiometabolic": [
        {"specialty": "Cardiologists & Heart Failure Specialists", "estimated_pool_size": 32000, "tier": "Tier A+ (Key Opinion Leaders)", "priority_level": "Very High", "expected_reach_rate": 0.85, "prescription_potential_per_month": 140},
        {"specialty": "Endocrinologists & Diabetologists", "estimated_pool_size": 28000, "tier": "Tier A (High Volume Prescribers)", "priority_level": "Very High", "expected_reach_rate": 0.90, "prescription_potential_per_month": 220},
        {"specialty": "Nephrologists", "estimated_pool_size": 14000, "tier": "Tier A (Specialist Target)", "priority_level": "High", "expected_reach_rate": 0.75, "prescription_potential_per_month": 95},
        {"specialty": "Consultant Internal Medicine & Primary Care", "estimated_pool_size": 180000, "tier": "Tier B (Broad Maintenance Volume)", "priority_level": "Moderate", "expected_reach_rate": 0.55, "prescription_potential_per_month": 45},
    ],
    "oncology": [
        {"specialty": "Medical Oncologists", "estimated_pool_size": 13000, "tier": "Tier A+ (Key Opinion Leaders)", "priority_level": "Very High", "expected_reach_rate": 0.88, "prescription_potential_per_month": 22},
        {"specialty": "Thoracic & Surgical Oncologists", "estimated_pool_size": 4500, "tier": "Tier A (Specialist Target)", "priority_level": "High", "expected_reach_rate": 0.70, "prescription_potential_per_month": 9},
        {"specialty": "Hematologist-Oncologists", "estimated_pool_size": 9000, "tier": "Tier A (High Volume Prescribers)", "priority_level": "High", "expected_reach_rate": 0.75, "prescription_potential_per_month": 14},
        {"specialty": "Hospital Pharmacy & Tumour Board Committees", "estimated_pool_size": 2200, "tier": "Tier B (Formulary Gatekeepers)", "priority_level": "Moderate", "expected_reach_rate": 0.60, "prescription_potential_per_month": 0},
    ],
    "immunology": [
        {"specialty": "Rheumatologists", "estimated_pool_size": 6500, "tier": "Tier A+ (Key Opinion Leaders)", "priority_level": "Very High", "expected_reach_rate": 0.85, "prescription_potential_per_month": 35},
        {"specialty": "Dermatologists", "estimated_pool_size": 12500, "tier": "Tier A (High Volume Prescribers)", "priority_level": "Very High", "expected_reach_rate": 0.80, "prescription_potential_per_month": 40},
        {"specialty": "Gastroenterologists", "estimated_pool_size": 15000, "tier": "Tier A (Specialist Target)", "priority_level": "High", "expected_reach_rate": 0.72, "prescription_potential_per_month": 28},
    ],
    "neurology": [
        {"specialty": "Neurologists", "estimated_pool_size": 18000, "tier": "Tier A+ (Key Opinion Leaders)", "priority_level": "Very High", "expected_reach_rate": 0.82, "prescription_potential_per_month": 45},
        {"specialty": "Psychiatrists", "estimated_pool_size": 38000, "tier": "Tier A (High Volume Prescribers)", "priority_level": "High", "expected_reach_rate": 0.68, "prescription_potential_per_month": 60},
        {"specialty": "Consultant Internal Medicine & Primary Care", "estimated_pool_size": 180000, "tier": "Tier B (Broad Maintenance Volume)", "priority_level": "Moderate", "expected_reach_rate": 0.50, "prescription_potential_per_month": 20},
    ],
    "respiratory": [
        {"specialty": "Pulmonologists", "estimated_pool_size": 12000, "tier": "Tier A+ (Key Opinion Leaders)", "priority_level": "Very High", "expected_reach_rate": 0.85, "prescription_potential_per_month": 70},
        {"specialty": "Allergists & Immunologists", "estimated_pool_size": 5000, "tier": "Tier A (Specialist Target)", "priority_level": "High", "expected_reach_rate": 0.75, "prescription_potential_per_month": 50},
        {"specialty": "Consultant Internal Medicine & Primary Care", "estimated_pool_size": 180000, "tier": "Tier B (Broad Maintenance Volume)", "priority_level": "Moderate", "expected_reach_rate": 0.55, "prescription_potential_per_month": 35},
    ],
    "infectious_disease": [
        {"specialty": "Infectious Disease Specialists", "estimated_pool_size": 9500, "tier": "Tier A+ (Key Opinion Leaders)", "priority_level": "Very High", "expected_reach_rate": 0.85, "prescription_potential_per_month": 30},
        {"specialty": "Hospital Antimicrobial Stewardship Committees", "estimated_pool_size": 3000, "tier": "Tier A (Formulary Gatekeepers)", "priority_level": "High", "expected_reach_rate": 0.70, "prescription_potential_per_month": 0},
        {"specialty": "Consultant Internal Medicine & Primary Care", "estimated_pool_size": 180000, "tier": "Tier B (Broad Maintenance Volume)", "priority_level": "Moderate", "expected_reach_rate": 0.50, "prescription_potential_per_month": 25},
    ],
}

# Keywords are matched against the free-text therapy area supplied by the user.
PANEL_KEYWORDS: List[tuple] = [
    ("cardiometabolic", ("cardio", "metabolic", "diabet", "renal", "nephro", "heart", "obesity", "lipid", "hematolog", "thrombo")),
    ("oncology", ("oncolog", "cancer", "tumor", "tumour", "nsclc", "carcinoma", "immuno-onc", "leukemia", "lymphoma", "myeloma")),
    ("immunology", ("immunolog", "rheumat", "dermatolog", "psoria", "arthrit", "gastro", "colitis", "crohn", "autoimmun")),
    ("neurology", ("neuro", "cns", "psychiatr", "alzheim", "parkinson", "epilep", "migraine", "multiple sclerosis")),
    ("respiratory", ("respirat", "pulmon", "asthma", "copd", "allerg")),
    ("infectious_disease", ("infect", "antivir", "antibiot", "antimicrob", "vaccine", "hiv", "hepatitis")),
]


def _doctor_segments_for(therapy_area: str) -> List[DoctorSpecialtySegment]:
    """Pick the prescriber panel matching the therapy area.

    An unrecognised therapy area returns an explicit placeholder rather than a
    default panel: silently handing back cardiology targets for an oncology
    brand plan is worse than showing the gap.
    """
    lowered = (therapy_area or "").lower()

    for panel_key, keywords in PANEL_KEYWORDS:
        if any(keyword in lowered for keyword in keywords):
            return [DoctorSpecialtySegment(**seg) for seg in SPECIALTY_PANELS[panel_key]]

    return [
        DoctorSpecialtySegment(
            specialty=f"Target specialties for '{therapy_area}' not yet defined — add sourced prescriber segments",
            estimated_pool_size=0,
            tier="Not verified",
            priority_level="Moderate",
            expected_reach_rate=0.0,
            prescription_potential_per_month=0,
        )
    ]


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
    """Computes pure mathematical epidemiological patient funnel and 5-year multi-scenario revenue projections.

    Rates are validated at the API boundary, but this function is also called
    directly by the export endpoints, so it re-checks its own inputs rather than
    trusting the caller.
    """

    for label, rate in (
        ("prevalence_rate", prevalence_rate),
        ("diagnosed_rate", diagnosed_rate),
        ("treated_rate", treated_rate),
        ("brand_adoption_rate_y1", brand_adoption_rate_y1),
    ):
        if not 0 < rate <= 1:
            raise ValueError(f"{label} must be greater than 0 and at most 1, got {rate}")
    if total_population < 1:
        raise ValueError(f"total_population must be at least 1, got {total_population}")
    if annual_cost_per_patient_usd <= 0:
        raise ValueError(f"annual_cost_per_patient_usd must be positive, got {annual_cost_per_patient_usd}")

    # 1. Patient Funnel Mathematics
    prevalent_pool = int(total_population * prevalence_rate)
    diagnosed_pool = int(prevalent_pool * diagnosed_rate)
    treated_pool = int(diagnosed_pool * treated_rate)

    # Total available treated therapy market value
    therapy_market_size = treated_pool * annual_cost_per_patient_usd

    # 2. Five-year revenue under three uptake scenarios
    conservative = _build_scenario(treated_pool, brand_adoption_rate_y1, annual_cost_per_patient_usd, SCENARIO_CURVES["conservative"])
    realistic = _build_scenario(treated_pool, brand_adoption_rate_y1, annual_cost_per_patient_usd, SCENARIO_CURVES["realistic"])
    aggressive = _build_scenario(treated_pool, brand_adoption_rate_y1, annual_cost_per_patient_usd, SCENARIO_CURVES["aggressive"])

    # 3. Prescriber segments matched to the therapy area
    doctor_segments = _doctor_segments_for(therapy_area)

    lead_specialty = doctor_segments[0].specialty if doctor_segments else "priority specialists"

    region_breakdown = {
        "North America (US/Canada)": "Planning default: premium reimbursement with focus on commercial payer formulary coverage. Replace the revenue split with sourced regional market data.",
        "Europe (EU5 + UK)": "Planning default: statutory health insurance pricing negotiations with strong health economics (HTA) evidence requirements.",
        "Asia-Pacific (India, China, Japan)": "Planning default: high patient volume with emerging middle-class out-of-pocket & private insurance growth.",
        "Latin America & MEA": "Planning default: tender-based hospital supply and key private medical centers."
    }

    channel_strategy = {
        "Direct Field Force Detailing": f"60% of commercial budget; focused face-to-face scientific calls on Tier A/A+ {lead_specialty.lower()}.",
        "Omnichannel Digital Detailing & Webinars": "20% of budget; on-demand digital medical education, interactive case simulators, and clinical trial podcasts.",
        "Hospital & Institutional Tenders": f"15% of budget; formulary inclusion in leading tertiary {therapy_area.lower()} centres of excellence.",
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
