import logging
from typing import List, Dict, Any, Optional

from ..models.competitor import (
    ClassRival,
    CompanyShare,
    CompetitorIntelligence,
    CompetitorProfile,
    MarketSummary,
    SWOTAnalysis,
)
from . import market_data_service as market

logger = logging.getLogger(__name__)

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

def _market_competitors(molecule_name: str) -> Dict[str, Any]:
    """Pull the measured competitor set for a molecule from ingested extracts.

    Returns empty structures — never placeholders — when nothing covers the
    molecule, so the caller can tell "no data" apart from "no competition".
    """
    try:
        overview = market.molecule_overview(molecule_name)
    except Exception:
        logger.exception("Market lookup failed for %s", molecule_name)
        return {}
    return overview or {}


def _profile_from_market(index: int, row: Dict[str, Any], unit: str,
                         source_label: Optional[str]) -> CompetitorProfile:
    """Turn one aggregated brand row into a competitor profile.

    Strategy fields (positioning, messaging, visual-aid angle) stay blank: an
    audit extract measures sales, it does not tell you how a brand is being
    detailed. Filling them would put unsourced claims in front of a reviewer.
    """
    return CompetitorProfile(
        id=f"MKT-{index}",
        molecule=row.get("molecule_desc") or "",
        brand_name=row.get("brand") or "",
        company=row.get("company") or "Not stated in source",
        market_share_percentage=float(row.get("market_share_percent") or 0.0),
        data_source="secondary_market",
        source_label=source_label,
        market_value=row.get("value_latest"),
        value_unit=unit,
        market_value_prev=row.get("value_prev"),
        market_growth_percent=row.get("growth_percent"),
        units_latest=row.get("units_latest"),
        ownership=row.get("ownership"),
        pack_count=row.get("pack_count"),
        period=row.get("period"),
        is_combination=bool(row.get("is_combination")),
        therapy_group=row.get("group_name"),
        subgroup=row.get("subgroup"),
    )


def generate_competitor_intelligence(
    molecule_name: str,
    indication: Optional[str] = None,
    max_market_brands: int = 25,
) -> CompetitorIntelligence:
    """Competitor matrix, SWOT, and positioning coordinates for a molecule.

    Two layers, kept distinct rather than blended:

    * **Curated** — hand-checked strategy, claims, and pricing. Rich, but only
      exists for molecules someone has researched.
    * **Secondary market** — every brand actually sold, with company, value,
      share, and growth, read from ingested audit extracts. Covers any molecule
      in the extract, but carries facts only, no strategy narrative.

    A molecule with neither returns an explicit empty state. Nothing in this
    function invents a competitor, a share, or a claim.
    """
    clean_name = molecule_name.strip().lower()
    curated = CURATED_COMPETITORS.get(clean_name)

    overview = _market_competitors(molecule_name)
    market_brands = overview.get("brands") or []
    datasets = overview.get("datasets") or []
    unit = datasets[0]["value_unit"] if datasets else "INR Cr"
    market_name = datasets[0]["market"] if datasets else None
    source_label = datasets[0]["source_label"] if datasets else None
    source_files = [d["original_filename"] for d in datasets]

    competitors: List[CompetitorProfile] = []
    if curated:
        competitors.extend(CompetitorProfile(**c) for c in curated["competitors"])

    # The subject molecule's own brands are the direct competitive set. A
    # curated entry never covers these — it lists rival molecules, not the
    # marketed brands of this one — so the two layers do not overlap.
    for position, row in enumerate(market_brands[:max_market_brands], start=1):
        competitors.append(_profile_from_market(position, row, unit, source_label))

    class_block = overview.get("class") or {}
    class_rivals = [ClassRival(**{
        "molecule_desc": r.get("molecule_desc") or "",
        "molecule_key": r.get("molecule_key"),
        "value_latest": r.get("value_latest") or 0.0,
        "growth_percent": r.get("growth_percent"),
        "brand_count": r.get("brand_count") or 0,
        "class_share_percent": r.get("class_share_percent") or 0.0,
    }) for r in (class_block.get("molecules") or [])]

    companies = [CompanyShare(**{
        "company": c.get("company") or "",
        "ownership": c.get("ownership"),
        "value_latest": c.get("value_latest") or 0.0,
        "growth_percent": c.get("growth_percent"),
        "brand_count": c.get("brand_count") or 0,
        "market_share_percent": c.get("market_share_percent") or 0.0,
    }) for c in (overview.get("companies") or [])]

    summary = MarketSummary(
        has_data=bool(market_brands),
        market=market_name,
        period=overview.get("period"),
        value_unit=unit if market_brands else None,
        market_size=overview.get("market_size") if market_brands else None,
        market_size_prev=overview.get("market_size_prev") if market_brands else None,
        market_growth_percent=overview.get("market_growth_percent"),
        total_brands=int(overview.get("total_brands") or 0),
        total_companies=len(companies),
        therapy_group=class_block.get("group"),
        group_value=class_block.get("group_value"),
        source_files=source_files if market_brands else [],
    )

    sources: List[str] = []
    if curated:
        sources.append("Curated competitor research")
    if market_brands and source_label:
        sources.append(source_label)

    if curated:
        swot = SWOTAnalysis(**curated["swot_analysis"])
        gap_summary = curated["positioning_gap_summary"]
        differentiators = curated["head_to_head_differentiators"]
    elif market_brands:
        leader = market_brands[0]
        swot = SWOTAnalysis(
            strengths=[],
            weaknesses=[],
            opportunities=[],
            threats=[
                f"{summary.total_brands} brands already compete on this molecule in "
                f"{market_name or 'this market'} ({overview.get('period')}), led by "
                f"{leader.get('brand')} ({leader.get('company')}) at "
                f"{leader.get('market_share_percent')}% share.",
                "Strategy fields below are not populated from the audit extract — "
                "positioning, claims, and messaging still require source-backed research.",
            ],
        )
        gap_summary = (
            f"Measured market: {summary.market_size} {unit} across {summary.total_brands} "
            f"brands and {summary.total_companies} companies ({overview.get('period')}). "
            "Share and growth are audited facts; positioning and claims are not — those "
            "still need label verification and MLR review before use."
        )
        differentiators = []
    else:
        swot = SWOTAnalysis(
            strengths=[],
            weaknesses=[],
            opportunities=[],
            threats=["Competitor landscape has not been verified for this molecule/indication."],
        )
        gap_summary = (
            "No source-backed competitor matrix is available. Upload a market extract "
            "(IQVIA/IMS, PharmaTrac, AWACS) under Market Data, or add verified "
            "competitors, labels, claims, and pricing before generating positioning."
        )
        differentiators = []

    return CompetitorIntelligence(
        molecule=(curated["molecule"] if curated else molecule_name.title()),
        competitors=competitors,
        swot_analysis=swot,
        positioning_gap_summary=gap_summary,
        head_to_head_differentiators=differentiators,
        market_summary=summary,
        company_leaderboard=companies,
        class_rivals=class_rivals,
        data_sources=sources,
    )
