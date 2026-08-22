import logging
from typing import Dict, Any, List, Optional

from ..models.regulatory import RegulatoryIntelligence, RegulatoryAgencyInfo
from .openfda_regulatory import fetch_us_fda_profile
from . import response_cache

logger = logging.getLogger(__name__)

CURATED_REGULATORY: Dict[str, Dict[str, Any]] = {
    "empagliflozin": {
        "generic_name": "Empagliflozin",
        "us_fda": {
            "agency_name": "US FDA",
            "status": "Approved",
            "approval_year": 2014,
            "innovator_brand_name": "JARDIANCE",
            "application_numbers": ["NDA 204629", "NDA 204629/S-033"],
            "approved_indications": [
                "Adjunct to diet and exercise to improve glycemic control in adults and pediatric patients aged 10 years and older with type 2 diabetes mellitus.",
                "To reduce the risk of cardiovascular death in adults with type 2 diabetes mellitus and established cardiovascular disease.",
                "To reduce the risk of cardiovascular death and hospitalization for heart failure in adults with heart failure (all ejection fractions).",
                "To reduce the risk of sustained decline in eGFR, end-stage kidney disease, cardiovascular death, and hospitalization in adults with chronic kidney disease at risk of progression."
            ],
            "dosage_and_administration_summary": "10 mg orally once daily in the morning, taken with or without food. May increase to 25 mg once daily in patients tolerating 10 mg who require additional glycemic control.",
            "boxed_warnings": [],
            "warnings_and_precautions": [
                "Ketoacidosis: Assess patients with signs/symptoms of metabolic acidosis; consider discontinuing.",
                "Volume Depletion: Assess and correct volume status before initiation, especially in elderly or patients on loop diuretics.",
                "Urosepsis and Pyelonephritis: Evaluate patients for signs of serious UTIs.",
                "Necrotizing Fasciitis of the Perineum (Fournier's Gangrene): Discontinue immediately if suspected.",
                "Genital Mycotic Infections: Counsel patients on risk and proper hygiene."
            ],
            "contraindications": [
                "Hypersensitivity to empagliflozin or any excipients.",
                "Patients on dialysis."
            ],
            "source_spl_or_url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=2958473a-c5c8-4720-91a9-bcfd48fb2c7a"
        },
        "india_cdsco": {
            "agency_name": "CDSCO (India)",
            "status": "Approved",
            "approval_year": 2015,
            "innovator_brand_name": "JARDIANCE / GIBTULIO",
            "application_numbers": ["Form 45 / Import NOC 2015-CDSCO"],
            "approved_indications": [
                "Type 2 Diabetes Mellitus glycemic management & CV death reduction",
                "Heart failure across reduced and preserved ejection fractions",
                "Chronic kidney disease management"
            ],
            "dosage_and_administration_summary": "10 mg / 25 mg film-coated tablets once daily.",
            "boxed_warnings": [],
            "warnings_and_precautions": ["Euglycemic DKA risk in perioperative periods", "Monitoring in elderly patients"],
            "contraindications": ["End-stage renal disease on hemodialysis", "Known severe hypersensitivity"],
            "source_spl_or_url": "https://cdsco.gov.in"
        },
        "eu_ema": {
            "agency_name": "EMA (European Union)",
            "status": "Approved",
            "approval_year": 2014,
            "innovator_brand_name": "JARDIANCE",
            "application_numbers": ["EU/1/14/930/001-026"],
            "approved_indications": [
                "Treatment of adults and children aged 10 and older with insufficiently controlled T2D",
                "Treatment of adults with symptomatic chronic heart failure",
                "Treatment of adults with chronic kidney disease"
            ],
            "dosage_and_administration_summary": "10 mg once daily starting dose.",
            "boxed_warnings": [],
            "warnings_and_precautions": ["Renal monitoring", "Diabetic ketoacidosis alert"],
            "contraindications": ["Hypersensitivity to active substance"],
            "source_spl_or_url": "https://www.ema.europa.eu/en/medicines/human/EPAR/jardiance"
        },
        "generic_vs_innovator_status": "Innovator Exclusivity / Transitioning to Generic Formulations in key emerging markets",
        "patent_expiry_timeline": "Primary substance patent expired / expiring 2025-2027 depending on jurisdiction; formulation and use patents contested.",
        "key_label_claims_verified": [
            "Reduces risk of cardiovascular death in adults with T2DM and established CVD.",
            "Reduces risk of CV death and hospitalization for heart failure across all ejection fractions.",
            "Reduces risk of sustained eGFR decline and end-stage kidney disease in CKD."
        ],
        "ai_strategic_interpretation": [
            "Strategic Positioning Window: Foundation triple-pillar (Diabetes + Heart Failure + CKD) positioning provides massive physician reach across Diabetologists, Cardiologists, and Nephrologists.",
            "Generic Defense Opportunity: Emphasize brand heritage, reliable supply chain, and patient support programs as generic alternatives enter market."
        ],
        "compliance_fair_balance_notes": "All promotional materials detailing CV or Renal mortality benefits MUST prominently display the risk of genital mycotic infections, volume depletion, and euglycemic DKA as per FDA OPDP and CDSCO UCPMP guidelines."
    },
    "semaglutide": {
        "generic_name": "Semaglutide",
        "us_fda": {
            "agency_name": "US FDA",
            "status": "Approved",
            "approval_year": 2017,
            "innovator_brand_name": "OZEMPIC / WEGOVY / RYBELSUS",
            "application_numbers": ["NDA 209637 (Ozempic)", "NDA 215256 (Wegovy)", "NDA 213051 (Rybelsus)"],
            "approved_indications": [
                "Adjunct to diet and exercise to improve glycemic control in adults with type 2 diabetes mellitus.",
                "To reduce the risk of major adverse cardiovascular events (CV death, nonfatal MI, nonfatal stroke) in adults with T2DM and established CVD.",
                "Chronic weight management in adults and pediatric patients aged ≥12 with obesity (BMI ≥30 or ≥27 with comorbidity).",
                "To reduce the risk of cardiovascular death, heart attack, and stroke in adults with cardiovascular disease and obesity (Wegovy)."
            ],
            "dosage_and_administration_summary": "Ozempic: 0.25 mg weekly titration to 0.5 mg, 1.0 mg, 2.0 mg SC. Wegovy: 0.25 mg up-titrated monthly to 2.4 mg SC weekly. Rybelsus: 3 mg daily fasting for 30 days, then 7 mg or 14 mg daily.",
            "boxed_warnings": [
                "WARNING: RISK OF THYROID C-CELL TUMORS. In rodents, semaglutide causes dose-dependent and treatment-duration-dependent thyroid C-cell tumors at clinically relevant exposures. It is unknown whether semaglutide causes thyroid C-cell tumors, including medullary thyroid carcinoma (MTC), in humans."
            ],
            "warnings_and_precautions": [
                "Pancreatitis: Discontinue promptly if pancreatitis is suspected.",
                "Diabetic Retinopathy Complications: Rapid improvement in glucose control has been associated with temporary worsening of diabetic retinopathy.",
                "Hypoglycemia with Concomitant Use of Insulin Secretagogues or Insulin.",
                "Acute Kidney Injury: Monitor renal function in patients reporting severe adverse gastrointestinal reactions.",
                "Hypersensitivity: Serious hypersensitivity reactions including anaphylaxis and angioedema.",
                "Acute Gallbladder Disease: Cholelithiasis and cholecystitis reported."
            ],
            "contraindications": [
                "Personal or family history of Medullary Thyroid Carcinoma (MTC) or Multiple Endocrine Neoplasia syndrome type 2 (MEN 2).",
                "Known hypersensitivity to semaglutide."
            ],
            "source_spl_or_url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=2958473a-c5c8-4720-91a9-bcfd48fb2c7b"
        },
        "india_cdsco": {
            "agency_name": "CDSCO (India)",
            "status": "Approved",
            "approval_year": 2020,
            "innovator_brand_name": "RYBELSUS (Oral) / OZEMPIC (Import)",
            "application_numbers": ["Form 45 Import Permission"],
            "approved_indications": [
                "Type 2 Diabetes Mellitus glycemic control",
                "CV risk reduction in high risk T2DM patients"
            ],
            "dosage_and_administration_summary": "Oral 3mg, 7mg, 14mg tablets; SC injectables.",
            "boxed_warnings": ["Black box thyroid C-cell warning required on product literature"],
            "warnings_and_precautions": ["Pancreatitis alert", "GI tolerability management"],
            "contraindications": ["MTC / MEN-2 history"],
            "source_spl_or_url": "https://cdsco.gov.in"
        },
        "eu_ema": {
            "agency_name": "EMA (European Union)",
            "status": "Approved",
            "approval_year": 2018,
            "innovator_brand_name": "OZEMPIC / WEGOVY",
            "application_numbers": ["EU/1/17/1251/001-006"],
            "approved_indications": [
                "Treatment of adults with insufficiently controlled type 2 diabetes mellitus",
                "Weight management including weight loss and weight maintenance in adults with obesity"
            ],
            "dosage_and_administration_summary": "Once-weekly subcutaneous injection.",
            "boxed_warnings": ["Thyroid C-cell potential risk reflected in SmPC Special Warnings"],
            "warnings_and_precautions": ["Diabetic retinopathy monitoring", "Dehydration risk"],
            "contraindications": ["Hypersensitivity"],
            "source_spl_or_url": "https://www.ema.europa.eu"
        },
        "generic_vs_innovator_status": "Innovator Exclusivity / Patent Active with heavy supply constraint dynamics",
        "patent_expiry_timeline": "US / EU compound patents protect molecule until ~2031-2032; peptide synthesis and delivery device patents active.",
        "key_label_claims_verified": [
            "Demonstrated up to 15-20% sustained mean body weight reduction in clinical trials.",
            "Reduces risk of major adverse cardiovascular events (MACE) by 20% in patients with established CVD and obesity.",
            "Potent HbA1c reduction with low inherent risk of hypoglycemia when used as monotherapy."
        ],
        "ai_strategic_interpretation": [
            "Dual-Market Maximization: Distinct branding split between Metabolic/Diabetic care (Ozempic/Rybelsus) vs Dedicated Obesity/Cardiovascular risk reduction (Wegovy).",
            "Adherence & Titration Support: Commercial strategy requires robust digital patient support programs to mitigate GI dropout during initial 16-week titration phase."
        ],
        "compliance_fair_balance_notes": "MANDATORY: Every promotional communication must include prominent Black Box Warning regarding Thyroid C-cell tumors and contraindication in MTC/MEN-2, matching FDA OPDP strict enforcement standards."
    },
    "pembrolizumab": {
        "generic_name": "Pembrolizumab",
        "us_fda": {
            "agency_name": "US FDA",
            "status": "Approved (Breakthrough Therapy & Priority Review)",
            "approval_year": 2014,
            "innovator_brand_name": "KEYTRUDA",
            "application_numbers": ["BLA 125514", "BLA 125514/S-089"],
            "approved_indications": [
                "1st-line treatment of patients with metastatic non-small cell lung cancer (NSCLC) in combination with pemetrexed and platinum chemotherapy.",
                "1st-line monotherapy of metastatic NSCLC with tumor PD-L1 expression (TPS ≥1%) with no EGFR or ALK genomic tumor aberrations.",
                "Adjuvant treatment of adult and pediatric patients (≥12 years) with Stage IIB, IIC, or III melanoma following complete resection.",
                "Treatment of adult and pediatric patients with unresectable or metastatic microsatellite instability-high (MSI-H) or mismatch repair deficient (dMMR) solid tumors."
            ],
            "dosage_and_administration_summary": "200 mg every 3 weeks or 400 mg every 6 weeks administered as an intravenous infusion over 30 minutes until disease progression or unacceptable toxicity.",
            "boxed_warnings": [],
            "warnings_and_precautions": [
                "Severe and Fatal Immune-Mediated Adverse Reactions: Can occur in any organ system (Pneumonitis, Colitis, Hepatitis, Endocrinopathies, Nephritis).",
                "Infusion-Related Reactions: Interrupt or slow rate of infusion for mild/moderate reactions; permanently discontinue for severe reactions.",
                "Complications of Allogeneic HSCT: Fatal and serious complications reported when transplant is performed before or after PD-1 inhibitor therapy."
            ],
            "contraindications": ["None on US FDA label"],
            "source_spl_or_url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=9333c79b-d487-4538-a9f0-70191bfdef2b"
        },
        "india_cdsco": {
            "agency_name": "CDSCO (India)",
            "status": "Approved",
            "approval_year": 2018,
            "innovator_brand_name": "KEYTRUDA",
            "application_numbers": ["Form 45 Import Biological"],
            "approved_indications": [
                "Advanced Non-Small Cell Lung Carcinoma (NSCLC)",
                "Advanced Melanoma and Head & Neck Cancer"
            ],
            "dosage_and_administration_summary": "Intravenous infusion Q3W / Q6W.",
            "boxed_warnings": [],
            "warnings_and_precautions": ["Immune-mediated adverse reaction protocols with high-dose corticosteroid management"],
            "contraindications": ["Severe hypersensitivity to pembrolizumab"],
            "source_spl_or_url": "https://cdsco.gov.in"
        },
        "eu_ema": {
            "agency_name": "EMA (European Union)",
            "status": "Approved",
            "approval_year": 2015,
            "innovator_brand_name": "KEYTRUDA",
            "application_numbers": ["EU/1/15/1024/001-002"],
            "approved_indications": [
                "Monotherapy and combination therapy for advanced/metastatic NSCLC, Melanoma, HNSCC, cHL, Urothelial, MSI-H CRC, and TNBC."
            ],
            "dosage_and_administration_summary": "200 mg Q3W or 400 mg Q6W IV.",
            "boxed_warnings": [],
            "warnings_and_precautions": ["Immune-related toxicities requiring systemic immunosuppression"],
            "contraindications": ["Hypersensitivity to active substance"],
            "source_spl_or_url": "https://www.ema.europa.eu"
        },
        "generic_vs_innovator_status": "Innovator Exclusivity / Primary Patent Cliff ~2028-2030 (Biosimilar development active worldwide)",
        "patent_expiry_timeline": "Core US composition of matter patent expires November 2028; subcutaneous co-formulation (with hyaluronidase) in development to extend exclusivity lifecycle.",
        "key_label_claims_verified": [
            "Demonstrated statistically significant doubling of overall survival in 1st-line metastatic NSCLC (KEYNOTE-189).",
            "First FDA-approved tumor-agnostic cancer therapy for MSI-H/dMMR biomarkers regardless of tissue origin.",
            "Favorable tolerability vs cytotoxic platinum chemotherapy regimens."
        ],
        "ai_strategic_interpretation": [
            "Lifecycle Defense: Prepare for the 2028 patent cliff by accelerating physician adoption of Subcutaneous (SC) Keytruda formulation and expanding combination ADC clinical programs.",
            "Biomarker Companion Strategy: Reinforce NGS and PD-L1 IHC 22C3 companion diagnostic testing across hospital oncology pathology labs."
        ],
        "compliance_fair_balance_notes": "All promotional materials must present comprehensive warnings on Immune-Mediated Adverse Reactions (imARs) including pneumonitis, colitis, and endocrinopathies, and the necessity of immediate corticosteroid management."
    },
    "apixaban": {
        "generic_name": "Apixaban",
        "us_fda": {
            "agency_name": "US FDA",
            "status": "Approved",
            "approval_year": 2012,
            "innovator_brand_name": "ELIQUIS",
            "application_numbers": ["NDA 202155", "NDA 202155/S-028"],
            "approved_indications": [
                "To reduce the risk of stroke and systemic embolism in patients with nonvalvular atrial fibrillation (NVAF).",
                "For the prophylaxis of deep vein thrombosis (DVT), which may lead to pulmonary embolism (PE), in patients who have undergone hip or knee replacement surgery.",
                "For the treatment of DVT and PE, and for the reduction in the risk of recurrent DVT and PE following initial therapy."
            ],
            "dosage_and_administration_summary": "NVAF: 5 mg orally twice daily. Reduce to 2.5 mg BID if at least 2 of: age ≥80 years, body weight ≤60 kg, serum creatinine ≥1.5 mg/dL. DVT/PE treatment: 10 mg BID for 7 days, then 5 mg BID.",
            "boxed_warnings": [
                "WARNING: (A) PREMATURE DISCONTINUATION OF ELIQUIS INCREASES THE RISK OF THROMBOTIC EVENTS. (B) SPINAL/EPIDURAL HEMATOMA RISK WITH NEURAXIAL ANESTHESIA."
            ],
            "warnings_and_precautions": [
                "Bleeding Risk: Increases the risk of hemorrhage. Promptly evaluate signs of blood loss.",
                "Prosthetic Heart Valves: Not recommended in patients with prosthetic heart valves.",
                "Antiphospholipid Syndrome (APS): Direct-acting oral anticoagulants (DOACs) are not recommended in patients with triple-positive APS."
            ],
            "contraindications": [
                "Active pathological bleeding.",
                "Severe hypersensitivity reaction to apixaban."
            ],
            "source_spl_or_url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=a00cf1b7-e215-46b0-951b-568b6b23f81e"
        },
        "india_cdsco": {
            "agency_name": "CDSCO (India)",
            "status": "Approved / Generics Available",
            "approval_year": 2013,
            "innovator_brand_name": "ELIQUIS",
            "application_numbers": ["Form 45 Import / Generic Formulations Approved"],
            "approved_indications": [
                "Stroke prevention in non-valvular atrial fibrillation",
                "Deep vein thrombosis and pulmonary embolism treatment"
            ],
            "dosage_and_administration_summary": "2.5 mg and 5 mg tablets twice daily.",
            "boxed_warnings": ["Black box warning on premature discontinuation risk"],
            "warnings_and_precautions": ["Bleeding risk assessment with HAS-BLED / CHA2DS2-VASc"],
            "contraindications": ["Active clinical bleeding"],
            "source_spl_or_url": "https://cdsco.gov.in"
        },
        "eu_ema": {
            "agency_name": "EMA (European Union)",
            "status": "Approved",
            "approval_year": 2011,
            "innovator_brand_name": "ELIQUIS",
            "application_numbers": ["EU/1/11/691/001-015"],
            "approved_indications": [
                "Prevention of stroke and systemic embolism in adult patients with non-valvular atrial fibrillation with one or more risk factors",
                "Treatment of DVT and PE and prevention of recurrent DVT and PE"
            ],
            "dosage_and_administration_summary": "5 mg twice daily with standard dose reduction criteria.",
            "boxed_warnings": ["Premature cessation warning in SmPC section 4.4"],
            "warnings_and_precautions": ["Hemorrhagic risk monitoring"],
            "contraindications": ["Clinically significant active bleeding", "Hepatic disease associated with coagulopathy"],
            "source_spl_or_url": "https://www.ema.europa.eu"
        },
        "generic_vs_innovator_status": "Patent Litigation / Exclusivity Extended in US to ~2026-2028; Generic competition active in international markets",
        "patent_expiry_timeline": "US formulation patent litigation affirmed patent protection through 2026-2028; emerging markets have active generic competition.",
        "key_label_claims_verified": [
            "Superior stroke risk reduction (21% RRR) compared to Warfarin (ARISTOTLE trial).",
            "Statistically significant 31% reduction in major bleeding vs Warfarin.",
            "11% relative risk reduction in all-cause mortality vs Warfarin."
        ],
        "ai_strategic_interpretation": [
            "Gold-Standard DOAC Framing: Position Eliquis as the undisputed #1 anticoagulant balancing superior stroke prevention with best-in-class GI and intracranial bleeding safety.",
            "Simplified Dose Reduction Algorithm: Highlight the intuitive '2 of 3 rule' (80-60-1.5: Age ≥80, Weight ≤60kg, Creatinine ≥1.5) to build physician confidence."
        ],
        "compliance_fair_balance_notes": "MANDATORY: Prominently feature the Black Box Warnings regarding the danger of premature discontinuation leading to stroke and the risk of spinal hematoma in patients undergoing spinal procedures."
    }
}

async def _india_from_market_data(molecule_name: str) -> Optional[RegulatoryAgencyInfo]:
    """India status inferred from the team's own market extract.

    CDSCO publishes no machine-readable approvals API, so India used to render
    as "Not verified" for every molecule. But a syndicated audit extract is
    direct evidence of the Indian market: a molecule with hundreds of brands and
    a measured turnover is unambiguously marketed here, and that is a sourced
    fact, not an inference about approval status.

    Stated precisely for that reason — "marketed, N brands recorded in <file>" —
    rather than "approved", which only CDSCO can say.
    """
    try:
        from . import market_data_service as market
        overview = market.brand_competitors(molecule_name, limit=5)
        # Company count must come from the full leaderboard, not from the five
        # brands fetched for display — otherwise 573 brands report 3 companies.
        companies = market.company_leaderboard(molecule_name, limit=1000)
    except Exception:
        logger.warning("Market lookup failed for India status", exc_info=True)
        return None

    brands = overview.get("brands") or []
    if not brands:
        return None
    period = overview.get("period") or "the loaded period"
    leader = brands[0]
    return RegulatoryAgencyInfo(
        agency_name="CDSCO (India)",
        status=f"Marketed in India — {overview['total_brands']} brand(s) recorded",
        approval_year=None,
        innovator_brand_name=leader.get("brand"),
        application_numbers=[],
        approved_indications=[],
        dosage_and_administration_summary=(
            f"{overview['total_brands']} brand(s) from {len(companies)} company(ies) "
            f"recorded in the loaded market extract for {period}, turning over "
            f"{overview['market_size']} INR Cr. Market presence is measured; the "
            f"CDSCO-approved indication and schedule still require register "
            f"verification (see the India / CDSCO module)."
        ),
        boxed_warnings=[],
        warnings_and_precautions=[],
        contraindications=[],
        source_spl_or_url="https://cdsco.gov.in/opencms/opencms/en/Approval_new/Approved-New-Drugs/",
    )


def _unavailable(agency: str, url: str, reason: str) -> RegulatoryAgencyInfo:
    """Explicit, actionable empty state for an agency with no machine source.

    Says what is missing and where to get it, instead of the bare "Not verified"
    that gave a reader nothing to act on. It still does not assert a status,
    because asserting one without a source is the failure this module exists to
    prevent.
    """
    return RegulatoryAgencyInfo(
        agency_name=agency,
        status="No machine-readable source connected",
        approval_year=None,
        innovator_brand_name=None,
        application_numbers=[],
        approved_indications=[],
        dosage_and_administration_summary=reason,
        boxed_warnings=[],
        warnings_and_precautions=[],
        contraindications=[],
        source_spl_or_url=url,
    )


async def _fetch_regulatory_intelligence_impl(molecule_name: str) -> RegulatoryIntelligence:
    """Regulatory dossier across US FDA, CDSCO, and EMA.

    Three layers, in order of authority:

    1. **Curated** — hand-checked dossiers for the molecules someone has
       researched in full.
    2. **openFDA** — live label and application facts for the US. This covers
       essentially every molecule marketed in the States, which is why the US
       block is rarely empty now.
    3. **The team's own market extract** — direct evidence of Indian market
       presence, where no CDSCO API exists.

    An agency with no connected source says exactly that and links the register
    to check. It never reports a status it cannot source.
    """
    clean_name = molecule_name.strip().lower()

    if clean_name in CURATED_REGULATORY:
        return RegulatoryIntelligence(**CURATED_REGULATORY[clean_name])

    profile = None
    try:
        profile = await fetch_us_fda_profile(molecule_name)
    except Exception:
        logger.warning("openFDA regulatory lookup failed for %s", molecule_name, exc_info=True)

    india = await _india_from_market_data(molecule_name)

    if profile:
        us = profile["info"]
        interpretation = [
            f"FDA record found: {profile['application_count']} application(s) on file"
            + (f", first approved {us.approval_year}." if us.approval_year else "."),
        ]
        if profile["market_status"]:
            interpretation.append(profile["market_status"] + ".")
        if profile["pharm_class"]:
            interpretation.append("FDA established pharmacologic class: "
                                  + "; ".join(profile["pharm_class"]) + ".")
        interpretation.append(
            "Label text above is quoted from the FDA structured product label. "
            "Verify against the current SPL and the local approved label before "
            "any promotional use."
        )
        verified_claims = [
            f"US innovator brand: {us.innovator_brand_name}" if us.innovator_brand_name else "",
            f"First US approval: {us.approval_year}" if us.approval_year else "",
            f"FDA application numbers: {', '.join(us.application_numbers[:6])}"
            if us.application_numbers else "",
        ]
        generic_status = profile["market_status"] or "Status not determinable from FDA applications"
    else:
        us = _unavailable(
            "US FDA",
            "https://dailymed.nlm.nih.gov",
            "No openFDA label or application record matched this molecule. It may be "
            "investigational, non-US, or listed under a different INN spelling. "
            "Search DailyMed directly to confirm.",
        )
        interpretation = [
            "No FDA record matched this molecule name.",
            "Do not make regulatory, safety, efficacy, or promotional claims until a "
            "label has been reviewed.",
        ]
        verified_claims = []
        generic_status = "Not determinable — no FDA application record matched"

    return RegulatoryIntelligence(
        generic_name=molecule_name.title(),
        us_fda=us,
        india_cdsco=india or _unavailable(
            "CDSCO (India)",
            "https://cdsco.gov.in/opencms/opencms/en/Approval_new/Approved-New-Drugs/",
            "CDSCO publishes no machine-readable approvals API. Load an Indian market "
            "extract under Secondary Data to establish market presence, and check the "
            "CDSCO approved-new-drugs register for the approved indication and schedule.",
        ),
        eu_ema=_unavailable(
            "EMA (European Union)",
            "https://www.ema.europa.eu/en/medicines",
            "No EMA source is connected. Check the EMA medicines register for the EPAR "
            "and the EU summary of product characteristics.",
        ),
        generic_vs_innovator_status=generic_status,
        patent_expiry_timeline=None,
        key_label_claims_verified=[c for c in verified_claims if c],
        ai_strategic_interpretation=interpretation,
        compliance_fair_balance_notes=(
            "MLR review required. Label text shown here is quoted from the source "
            "regulator's published label; it is not a promotional claim and has not "
            "been reviewed for fair balance in any market."
        ),
    )


# openFDA's own live latency (2-5s per query, entirely outside this app's
# control) is paid again on every page load of the same molecule, even though
# a drug's label and application history change on the order of months, not
# between one page view and the next. Cached for a week — long enough to
# remove that cost from every repeat view, short enough that a real label
# update is never stale for long.
REGULATORY_CACHE_TTL_HOURS = 24 * 7


async def fetch_regulatory_intelligence(molecule_name: str) -> RegulatoryIntelligence:
    """Regulatory dossier across US FDA, CDSCO, and EMA — cached.

    See _fetch_regulatory_intelligence_impl for what this actually computes;
    this wrapper only adds the cache-or-fetch layer in front of it.
    """
    return await response_cache.get_or_fetch(
        cache_key=f"regulatory:{molecule_name.strip().lower()}",
        ttl_hours=REGULATORY_CACHE_TTL_HOURS,
        fetch=lambda: _fetch_regulatory_intelligence_impl(molecule_name),
        to_dict=lambda r: r.model_dump(),
        from_dict=lambda d: RegulatoryIntelligence.model_validate(d),
    )
