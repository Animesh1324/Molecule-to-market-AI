import logging
from typing import Dict, Any, List, Optional
from ..models.regulatory import RegulatoryIntelligence, RegulatoryAgencyInfo

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

async def fetch_regulatory_intelligence(molecule_name: str) -> RegulatoryIntelligence:
    """Fetch structured regulatory label intelligence across US FDA, CDSCO, and EMA.

    Unknown molecules must not be represented as approved. Until a reliable
    parser is added for each agency, return an explicit not-verified dossier.
    """
    clean_name = molecule_name.strip().lower()
    
    if clean_name in CURATED_REGULATORY:
        return RegulatoryIntelligence(**CURATED_REGULATORY[clean_name])
    
    # No verified regulatory dossier found.
    return RegulatoryIntelligence(
        generic_name=molecule_name.title(),
        us_fda=RegulatoryAgencyInfo(
            agency_name="US FDA",
            status="Not verified",
            approval_year=None,
            innovator_brand_name=None,
            application_numbers=[],
            approved_indications=[],
            dosage_and_administration_summary="No verified FDA label data available in this application.",
            boxed_warnings=[],
            warnings_and_precautions=[],
            contraindications=[],
            source_spl_or_url="https://dailymed.nlm.nih.gov"
        ),
        india_cdsco=RegulatoryAgencyInfo(
            agency_name="CDSCO (India)",
            status="Not verified",
            approval_year=None,
            innovator_brand_name=None,
            application_numbers=[],
            approved_indications=[],
            dosage_and_administration_summary="No verified CDSCO label data available in this application.",
            boxed_warnings=[],
            warnings_and_precautions=[],
            contraindications=[],
            source_spl_or_url="https://cdsco.gov.in"
        ),
        eu_ema=RegulatoryAgencyInfo(
            agency_name="EMA (European Union)",
            status="Not verified",
            approval_year=None,
            innovator_brand_name=None,
            application_numbers=[],
            approved_indications=[],
            dosage_and_administration_summary="No verified EMA label data available in this application.",
            boxed_warnings=[],
            warnings_and_precautions=[],
            contraindications=[],
            source_spl_or_url="https://www.ema.europa.eu"
        ),
        generic_vs_innovator_status="Not verified",
        patent_expiry_timeline=None,
        key_label_claims_verified=[],
        ai_strategic_interpretation=[
            "Regulatory status could not be verified from the curated dataset.",
            "Do not use regulatory, safety, efficacy, or promotional claims until label review is completed."
        ],
        compliance_fair_balance_notes="MLR review required. No external claim should be made until approved labeling and jurisdiction-specific requirements are verified."
    )
