from typing import List, Dict, Any, Optional
from ..models.competitor import CompetitorIntelligence, CompetitorProfile, SWOTAnalysis

CURATED_COMPETITORS: Dict[str, Dict[str, Any]] = {
    "empagliflozin": {
        "molecule": "Empagliflozin",
        "competitors": [
            {
                "id": "COMP-1",
                "molecule": "Dapagliflozin",
                "brand_name": "Farxiga / Forxiga",
                "company": "AstraZeneca",
                "indication": "T2D, HFrEF, HFpEF, CKD",
                "strengths_available": ["5 mg", "10 mg"],
                "dosage_form": "Oral Film-Coated Tablet",
                "price_per_month_usd": 540.0,
                "key_claims": ["First SGLT2i approved for HFrEF regardless of diabetes status", "Proven eGFR preservation in DAPA-CKD"],
                "positioning": "The versatile Cardio-Renal first-choice protector",
                "packaging_direction": "Sleek blue/silver blister pack emphasizing modern cardiometabolic leadership",
                "visual_aid_angle": "Focus on DAPA-HF / DAPA-CKD kidney survival curves",
                "doctor_messaging": "Comprehensive protection across Heart Failure and Kidney disease from day one",
                "patient_promise": "Protect your heart and kidneys with once-daily convenience",
                "strengths": ["Extensive nephrology and cardiology mindshare", "Broadest labeled eGFR indications down to 25 mL/min"],
                "weaknesses": ["Comparable mycotic infection rate", "Intense price competition in generic markets"],
                "market_share_percentage": 42.0,
                "quadrant_x_efficacy": 8.5,
                "quadrant_y_safety_convenience": 8.0
            },
            {
                "id": "COMP-2",
                "molecule": "Canagliflozin",
                "brand_name": "Invokana",
                "company": "Johnson & Johnson / Janssen",
                "indication": "T2D, Diabetic Kidney Disease, CV Risk Reduction",
                "strengths_available": ["100 mg", "300 mg"],
                "dosage_form": "Oral Tablet",
                "price_per_month_usd": 510.0,
                "key_claims": ["First-in-class SGLT2 inhibitor in US", "CREDENCE renal outcomes in diabetic nephropathy"],
                "positioning": "The pioneer diabetic nephropathy agent",
                "packaging_direction": "Purple/White clinical packaging",
                "visual_aid_angle": "CREDENCE trial data in overt diabetic proteinuria",
                "doctor_messaging": "Established renal endpoint protection in diabetic nephropathy",
                "patient_promise": "Maintain kidney health and lower blood sugar",
                "strengths": ["Strong early data in diabetic kidney disease"],
                "weaknesses": ["Historical legacy concerns regarding amputation warnings (though subsequently removed)", "Lacks broad HFpEF label"],
                "market_share_percentage": 14.0,
                "quadrant_x_efficacy": 7.0,
                "quadrant_y_safety_convenience": 6.5
            },
            {
                "id": "COMP-3",
                "molecule": "Semaglutide (Oral / SC)",
                "brand_name": "Rybelsus / Ozempic",
                "company": "Novo Nordisk",
                "indication": "T2D, Obesity, CV Risk Reduction",
                "strengths_available": ["0.5 mg", "1.0 mg", "2.0 mg", "3 mg", "7 mg", "14 mg"],
                "dosage_form": "Subcutaneous Pen / Oral Tablet",
                "price_per_month_usd": 930.0,
                "key_claims": ["Unprecedented HbA1c reduction up to 2.0%", "Substantial weight loss benefits (up to 15%)"],
                "positioning": "The supreme metabolic and weight-reduction power engine",
                "packaging_direction": "Premium red/white dial autoinjector pens",
                "visual_aid_angle": "Dual glycemic and substantial weight reduction curves",
                "doctor_messaging": "Achieve glycemic control and clinically meaningful weight loss together",
                "patient_promise": "Transform your metabolic health with proven weight and heart benefits",
                "strengths": ["Unmatched weight loss efficacy", "Huge consumer brand awareness"],
                "weaknesses": ["Gastrointestinal side effect burden (nausea/vomiting)", "Significantly higher cost and frequent supply constraints"],
                "market_share_percentage": 30.0,
                "quadrant_x_efficacy": 9.2,
                "quadrant_y_safety_convenience": 6.0
            }
        ],
        "swot_analysis": {
            "strengths": [
                "EMPA-REG OUTCOME demonstrated landmark 38% reduction in CV death, unmatched in primary mortality data.",
                "Robust once-daily oral dosing with minimal drug-drug interactions and no active metabolites.",
                "Proven across entire ejection fraction spectrum in heart failure (HFrEF and HFpEF)."
            ],
            "weaknesses": [
                "Glycemic efficacy declines at eGFR <30 mL/min/1.73m² (though cardio-renal benefits persist).",
                "Requires patient counseling on genital hygiene to prevent common mycotic infections."
            ],
            "opportunities": [
                "Post-MI (EMPACT-MI) and acute in-hospital heart failure initiation (EMPULSE) expand immediate hospital prescriber base.",
                "Fixed-dose combinations (e.g. Empagliflozin + Linagliptin / Metformin) create high-adherence single-pill regimens.",
                "Growing nephrology guideline endorsement (KDIGO 2023) positions SGLT2i as first-line standard of care."
            ],
            "threats": [
                "Fast-moving dual GLP-1/GIP agonists (e.g., Tirzepatide) capturing high-tier private market share.",
                "Pending patent expiries in non-US markets opening the door to low-cost generic price erosion."
            ]
        },
        "positioning_gap_summary": "While competitors lead in sheer weight loss (GLP-1s) or early diabetic nephropathy awareness (Canagliflozin), Empagliflozin occupies the premier 'Hard Mortality & All-Spectrum Heart Failure' quadrant, offering the most definitive survival benefit with standard oral simplicity.",
        "head_to_head_differentiators": [
            "38% relative risk reduction in CV death in EMPA-REG vs 14% non-significant in DECLARE (Dapagliflozin).",
            "Consistent efficacy across both HFrEF and HFpEF with simple once-daily morning tablet.",
            "Superior selectivity (>5000-fold for SGLT2 vs SGLT1) compared to Canagliflozin (~250-fold)."
        ]
    }
}

def generate_competitor_intelligence(molecule_name: str, indication: Optional[str] = None) -> CompetitorIntelligence:
    """Generate competitor matrix, SWOT, and positioning quadrant coordinates.

    Only curated competitor sets are returned. Unknown landscapes must be empty
    rather than generated from assumptions, because pricing/share/claims require
    source-backed market research.
    """
    clean_name = molecule_name.strip().lower()
    
    if clean_name in CURATED_COMPETITORS:
        raw = CURATED_COMPETITORS[clean_name]
        return CompetitorIntelligence(
            molecule=raw["molecule"],
            competitors=[CompetitorProfile(**c) for c in raw["competitors"]],
            swot_analysis=SWOTAnalysis(**raw["swot_analysis"]),
            positioning_gap_summary=raw["positioning_gap_summary"],
            head_to_head_differentiators=raw["head_to_head_differentiators"]
        )
    
    return CompetitorIntelligence(
        molecule=molecule_name.title(),
        competitors=[],
        swot_analysis=SWOTAnalysis(
            strengths=[],
            weaknesses=[],
            opportunities=[],
            threats=["Competitor landscape has not been verified for this molecule/indication."]
        ),
        positioning_gap_summary="No source-backed competitor matrix is available. Add verified competitors, labels, claims, and pricing before generating positioning.",
        head_to_head_differentiators=[]
    )
