import asyncio
import httpx
import logging
from typing import Optional, Dict, Any
from ..models.molecule import MoleculeProfile, Pharmacokinetics, SpecialPopulations, AdverseEffects
from .molecule_resolver import resolve as resolve_molecule
from .openfda_regulatory import fetch_molecule_clinical_profile
from . import response_cache

logger = logging.getLogger(__name__)

# Curated landmark molecule data store for instant high-fidelity responses & offline reliability
CURATED_MOLECULES: Dict[str, Dict[str, Any]] = {
    "empagliflozin": {
        "generic_name": "Empagliflozin",
        "chemical_name": "(2S,3R,4R,5S,6R)-2-[4-chloro-3-[[4-[(3S)-oxolan-3-yl]oxyphenyl]methyl]phenyl]-6-(hydroxymethyl)oxane-3,4,5-triol",
        "chemical_class": "C-Glycoside / Organochlorine",
        "pharmacological_class": "Sodium-Glucose Co-Transporter 2 (SGLT2) Inhibitor",
        "cas_number": "864070-44-0",
        "pubchem_cid": 11949646,
        "smiles": "C1COCC1OC2=CC=C(C=C2)CC3=C(C=CC(=C3)C4C(C(C(C(O4)CO)O)O)O)Cl",
        "molecular_formula": "C23H27ClO7",
        "molecular_weight": 450.91,
        "mechanism_of_action": "Potent, highly selective competitive inhibitor of SGLT2 (SGLT2/SGLT1 selectivity >5000-fold) in the proximal renal tubules. Inhibits glucose and sodium reabsorption, promoting glucosuria, natriuresis, reducing intraglomerular pressure, and lowering blood pressure and cardiac preload/afterload.",
        "pharmacodynamics": "Causes dose-dependent urinary glucose excretion (approx. 64-78 g/day), lowers HbA1c by 0.7-0.9%, induces osmotic diuresis leading to modest weight loss (~2-3 kg) and systolic BP reduction (3-5 mmHg) without reflex tachycardia.",
        "pharmacokinetics": {
            "absorption": "Rapidly absorbed following oral administration; peak plasma concentrations reached at ~1.5 hours.",
            "bioavailability": "High absolute oral bioavailability (~60-70%). Not affected by food.",
            "tmax": "1.5 hours",
            "distribution": "Apparent volume of distribution approx. 73.8 L; extensively distributed to tissues.",
            "protein_binding": "86.2% bound to human plasma proteins.",
            "metabolism": "Primary metabolic pathway is glucuronidation by UGT2B7, UGT1A3, UGT1A8, and UGT1A9. No major active circulating metabolites.",
            "cyp_pathways": ["Minor CYP involvement; no clinically relevant CYP450 inhibition or induction."],
            "elimination": "Biphasic terminal elimination; approx. 54.4% excreted in urine and 41.2% in feces.",
            "half_life": "12.4 hours (ideal for once-daily dosing)",
            "clearance": "Apparent oral clearance approx. 10.6 L/h"
        },
        "approved_indications": [
            "Type 2 Diabetes Mellitus (Glycemic control & reduction of CV death risk)",
            "Heart Failure with reduced Ejection Fraction (HFrEF) - Reduces CV death & hospitalization",
            "Heart Failure with preserved Ejection Fraction (HFpEF) - EMPEROR-Preserved",
            "Chronic Kidney Disease (CKD) at risk of progression - EMPA-KIDNEY"
        ],
        "investigational_indications": [
            "Acute Heart Failure in-hospital initiation (EMPULSE)",
            "Post-Myocardial Infarction CV event reduction (EMPACT-MI)",
            "Non-Alcoholic Steatohepatitis (NASH / MASH)"
        ],
        "dosage_forms": ["Oral Film-Coated Tablets"],
        "routes_of_administration": ["Oral (Once Daily, morning, with or without food)"],
        "standard_dosages": ["10 mg once daily (Starting dose)", "25 mg once daily (Max dose for additional glycemic control)"],
        "contraindications": [
            "Severe hypersensitivity to empagliflozin or excipients",
            "Patients on dialysis or with end-stage renal disease without urinary output"
        ],
        "black_box_warnings": [],
        "drug_interactions": [
            "Diuretics (Thiazide / Loop): Potential additive volume depletion and hypotension.",
            "Insulin & Sulfonylureas: Increased risk of hypoglycemia; lower dose of secretagogue recommended.",
            "Lithium: SGLT2 inhibitors may increase renal lithium excretion, reducing serum levels."
        ],
        "adverse_effects": {
            "common": ["Female genital mycotic infections (moniliasis)", "Urinary tract infections (UTI)", "Nasopharyngitis", "Increased urination (polyuria)", "Thirst"],
            "rare": ["Fournier's gangrene (necrotizing fasciitis of perineum)", "Euglycemic Diabetic Ketoacidosis (euDKA)", "Severe pyelonephritis / urosepsis"],
            "serious": ["Symptomatic hypotension / volume depletion", "Acute kidney injury secondary to dehydration", "Ketoacidosis requiring hospitalization"]
        },
        "special_populations": {
            "pregnancy": "Not recommended during 2nd and 3rd trimesters of pregnancy due to potential risk to fetal renal development.",
            "lactation": "Breastfeeding is not recommended as potential for serious adverse reactions in nursing infants exists.",
            "pediatric": "Safety and efficacy established for T2DM in children aged 10 years and older; not established for HF or CKD.",
            "geriatric": "Higher incidence of volume depletion and hypotension in patients ≥75 years; renal monitoring advised.",
            "renal_impairment": "No dose adjustment required down to eGFR 20 mL/min/1.73m²; glycemic efficacy declines at lower eGFR, but CV and renal protection persists.",
            "hepatic_impairment": "No dose adjustment needed in mild to moderate hepatic impairment. Use with caution in severe hepatic impairment."
        },
        "differentiating_science": "Landmark EMPA-REG OUTCOME trial demonstrated a remarkable 38% relative risk reduction in CV death, establishing SGLT2i as a foundational cardio-renal-metabolic disease-modifying therapy rather than merely a glucose-lowering agent.",
        "key_targets": ["SLC5A2 (SGLT2)", "Proximal Tubule Sodium-Hydrogen Exchanger 3 (NHE3) modulation"]
    },
    "semaglutide": {
        "generic_name": "Semaglutide",
        "chemical_name": "GLP-1 receptor agonist peptide modified with Aib8, Arg34, and a C18 diacid spacer-linked lysine",
        "chemical_class": "Synthetic Glucagon-Like Peptide-1 (GLP-1) Analogue",
        "pharmacological_class": "GLP-1 Receptor Agonist (Incretin Mimetic)",
        "cas_number": "910463-68-2",
        "pubchem_cid": 56843331,
        "smiles": "Peptide macromolecule (94% homology to human GLP-1)",
        "molecular_formula": "C187H291N45O59",
        "molecular_weight": 4113.58,
        "mechanism_of_action": "Selectively binds to and activates the GLP-1 receptor. Stimulates glucose-dependent insulin secretion, inhibits glucagon release, delays gastric emptying, and centrally suppresses appetite via hypothalamic POMC/CART activation.",
        "pharmacodynamics": "Robust HbA1c lowering (~1.5-2.0%), significant weight loss (15-20% in STEP trials), improves systolic blood pressure, lipid profile, and reduces systemic inflammatory biomarkers (hs-CRP).",
        "pharmacokinetics": {
            "absorption": "Subcutaneous bioavailability ~89%; oral formulation bioavailability ~1% (co-formulated with SNAC absorption enhancer).",
            "bioavailability": "89% (SC) / 1% (Oral with SNAC)",
            "tmax": "1-3 days post subcutaneous injection; 1 hour post oral dosing.",
            "distribution": "Extensively bound to albumin (>99%) via C18 fatty diacid chain.",
            "protein_binding": ">99% to plasma albumin",
            "metabolism": "Proteolytic cleavage of peptide backbone and beta-oxidation of fatty acid side-chain.",
            "cyp_pathways": ["No significant hepatic CYP450 metabolism."],
            "elimination": "Metabolites excreted via urine (approx. 3%) and feces.",
            "half_life": "Approx. 1 week (168 hours) - enables once-weekly subcutaneous dosing.",
            "clearance": "0.05 L/h in T2DM patients."
        },
        "approved_indications": [
            "Type 2 Diabetes Mellitus (Glycemic control & MACE CV risk reduction)",
            "Chronic Weight Management (Obesity / Overweight with at least one weight-related comorbidity)",
            "Cardiovascular risk reduction in established CVD with obesity (SELECT Trial)",
            "Metabolic Dysfunction-Associated Steatohepatitis (MASH / NASH)"
        ],
        "investigational_indications": [
            "Alzheimer's Disease & Neurocognitive Protection (EVOKE / EVOKE Plus)",
            "Peripheral Artery Disease (STRIDE)",
            "Chronic Kidney Disease progression in T2D (FLOW trial)"
        ],
        "dosage_forms": ["Subcutaneous Autoinjector Pen (Once Weekly)", "Oral Tablets (Daily, Fasting with water)"],
        "routes_of_administration": ["Subcutaneous (Abdomen, Thigh, Upper Arm)", "Oral (Rybelsus)"],
        "standard_dosages": ["0.25 mg weekly (Escalation)", "0.5 mg, 1.0 mg, 2.0 mg weekly (T2D)", "2.4 mg weekly (Wegovy for Obesity)"],
        "contraindications": [
            "Personal or family history of Medullary Thyroid Carcinoma (MTC)",
            "Multiple Endocrine Neoplasia syndrome type 2 (MEN 2)",
            "History of severe hypersensitivity to semaglutide"
        ],
        "black_box_warnings": [
            "WARNING: RISK OF THYROID C-CELL TUMORS. In rodents, semaglutide causes dose-dependent thyroid C-cell tumors at clinically relevant exposures. Contraindicated in patients with MTC or MEN 2."
        ],
        "drug_interactions": [
            "Oral medications: Delays gastric emptying, potentially impacting rate/extent of absorption of concomitant oral drugs.",
            "Insulin & Sulfonylureas: Increased risk of hypoglycemia; proactive dose down-titration required."
        ],
        "adverse_effects": {
            "common": ["Nausea", "Vomiting", "Diarrhea", "Abdominal pain", "Constipation", "Dyspepsia", "Headache"],
            "rare": ["Acute Pancreatitis", "Diabetic Retinopathy complications in rapidly improved HbA1c", "Gallbladder disorders (cholelithiasis)"],
            "serious": ["Anaphylaxis & angioedema", "Bowel obstruction / gastroparesis", "Acute kidney injury from gastrointestinal dehydration"]
        },
        "special_populations": {
            "pregnancy": "Discontinue at least 2 months prior to a planned pregnancy due to long washout period.",
            "lactation": "Not recommended during breastfeeding.",
            "pediatric": "Approved for chronic weight management in pediatric patients aged ≥12 years.",
            "geriatric": "No general dose adjustment required; gastrointestinal tolerability should be monitored.",
            "renal_impairment": "No dose adjustment required in mild, moderate, or severe renal impairment; monitor renal function if severe GI fluid loss occurs.",
            "hepatic_impairment": "No dose adjustment required."
        },
        "differentiating_science": "SELECT and FLOW landmark trials proved multi-organ disease modification: 20% reduction in 3-point MACE in non-diabetic obese patients and 24% reduction in major kidney disease events.",
        "key_targets": ["GLP-1R (Glucagon-Like Peptide-1 Receptor)"]
    },
    "dapagliflozin": {
        "generic_name": "Dapagliflozin",
        "chemical_name": "(2S,3R,4R,5S,6R)-2-[4-chloro-3-[(4-ethoxyphenyl)methyl]phenyl]-6-(hydroxymethyl)oxane-3,4,5-triol",
        "chemical_class": "C-Aryl Glucoside",
        "pharmacological_class": "SGLT2 Inhibitor",
        "cas_number": "461432-26-8",
        "pubchem_cid": 9887712,
        "smiles": "CCOC1=CC=C(C=C1)CC2=C(C=CC(=C2)C3C(C(C(C(O3)CO)O)O)O)Cl",
        "molecular_formula": "C21H25ClO6",
        "molecular_weight": 408.87,
        "mechanism_of_action": "Inhibits subtype 2 of sodium-glucose transport proteins (SGLT2), blocking glucose reabsorption in the renal proximal tubule to increase urinary glucose and sodium excretion.",
        "pharmacodynamics": "Promotes ~70g/day urinary glucose excretion, decreases plasma volume, reduces cardiac filling pressures, and preserves glomerular filtration rate (GFR).",
        "pharmacokinetics": {
            "absorption": "Rapidly absorbed; peak plasma concentration within 2 hours.",
            "bioavailability": "Absolute bioavailability approx. 78%.",
            "tmax": "2.0 hours",
            "distribution": "Apparent volume of distribution is 118 L.",
            "protein_binding": "Approx. 91% protein bound.",
            "metabolism": "Metabolized mainly by UGT1A9 to dapagliflozin 3-O-glucuronide (inactive).",
            "cyp_pathways": ["Minor CYP-mediated metabolism."],
            "elimination": "75% excreted in urine, 21% in feces.",
            "half_life": "12.9 hours",
            "clearance": "207 mL/min"
        },
        "approved_indications": [
            "Type 2 Diabetes Mellitus",
            "Heart Failure across all ejection fractions (HFrEF and HFpEF / HFmrEF - DAPA-HF & DELIVER)",
            "Chronic Kidney Disease (DAPA-CKD) to reduce risk of sustained eGFR decline & ESKD"
        ],
        "investigational_indications": ["Acute organ protection in cardiometabolic shock"],
        "dosage_forms": ["Oral Tablets (5 mg, 10 mg)"],
        "routes_of_administration": ["Oral (Once Daily)"],
        "standard_dosages": ["10 mg once daily"],
        "contraindications": ["Hypersensitivity to dapagliflozin", "Dialysis"],
        "black_box_warnings": [],
        "drug_interactions": ["Loop Diuretics", "Insulin Secretagogues", "Lithium"],
        "adverse_effects": {
            "common": ["Vulvovaginal mycotic infection", "Nasopharyngitis", "Dysuria"],
            "rare": ["Fournier's gangrene", "Ketoacidosis"],
            "serious": ["Severe dehydration", "Urosepsis"]
        },
        "special_populations": {
            "pregnancy": "Avoid in 2nd/3rd trimester",
            "lactation": "Avoid",
            "pediatric": "Approved for T2D age ≥10",
            "geriatric": "Monitor hydration status",
            "renal_impairment": "Indicated down to eGFR 25 mL/min/1.73m² for CKD and HF",
            "hepatic_impairment": "No adjustment needed"
        },
        "differentiating_science": "First SGLT2 inhibitor to achieve FDA approval for heart failure with reduced ejection fraction (HFrEF) regardless of diabetes status, following the milestone DAPA-HF trial.",
        "key_targets": ["SLC5A2 (SGLT2)"]
    },
    "pembrolizumab": {
        "generic_name": "Pembrolizumab",
        "chemical_name": "Humanized IgG4-kappa monoclonal antibody against Programmed Cell Death 1 (PD-1)",
        "chemical_class": "Monoclonal Antibody (IgG4 isotype with S228P hinge mutation)",
        "pharmacological_class": "Immune Checkpoint Inhibitor (PD-1 Blocker)",
        "cas_number": "1374853-91-4",
        "pubchem_cid": None,
        "smiles": "Biological Therapeutic Macromolecule (~149 kDa)",
        "molecular_formula": "C6504H10004N1716O2036S46",
        "molecular_weight": 149000.0,
        "mechanism_of_action": "Potent, highly selective humanized IgG4-kappa antibody that binds to the PD-1 receptor and blocks its interaction with PD-L1 and PD-L2. This releases PD-1 pathway-mediated inhibition of the immune response, reactivating tumor-specific cytotoxic T-lymphocytes to eradicate cancer cells.",
        "pharmacodynamics": "Induces sustained receptor occupancy on circulating CD4+ and CD8+ T-cells (>90% at approved doses), restoring anti-tumor cytotoxic effector function and inducing prolonged objective response rates (ORR) across multiple tumor histologies.",
        "pharmacokinetics": {
            "absorption": "Administered exclusively via intravenous (IV) infusion with 100% systemic bioavailability.",
            "bioavailability": "100% (IV Infusion)",
            "tmax": "End of 30-minute IV infusion",
            "distribution": "Limited extravascular distribution; steady-state volume of distribution approx. 6.0 L.",
            "protein_binding": "Monoclonal antibody; not bound to plasma proteins in traditional small-molecule fashion.",
            "metabolism": "Nonspecific catabolic protein degradation pathways via cellular lysosomes; no CYP450 involvement.",
            "cyp_pathways": ["Zero CYP450 interaction."],
            "elimination": "Catabolized to small peptides and amino acids.",
            "half_life": "Approx. 22 days (528 hours), enabling convenient Q3W (every 3 weeks) or Q6W (every 6 weeks) dosing.",
            "clearance": "0.22 L/day"
        },
        "approved_indications": [
            "Non-Small Cell Lung Cancer (NSCLC) - 1st line monotherapy or combo with chemotherapy (KEYNOTE-189, KEYNOTE-024)",
            "Melanoma (Unresectable or Metastatic / Adjuvant)",
            "Head and Neck Squamous Cell Carcinoma (HNSCC)",
            "Classical Hodgkin Lymphoma (cHL)",
            "Urothelial Carcinoma / Bladder Cancer",
            "Microsatellite Instability-High (MSI-H) / dMMR Solid Tumors (Tumor-agnostic approval)",
            "Triple-Negative Breast Cancer (TNBC - KEYNOTE-522)",
            "Renal Cell Carcinoma (RCC in combination with Axitinib/Lenvatinib)"
        ],
        "investigational_indications": [
            "Perioperative / Neoadjuvant regimens across resectable solid tumors",
            "Novel antibody-drug conjugate (ADC) combination regimens"
        ],
        "dosage_forms": ["Injectable Solution for IV Infusion (100 mg / 4 mL single-dose vial)"],
        "routes_of_administration": ["Intravenous (IV) Infusion over 30 minutes"],
        "standard_dosages": ["200 mg every 3 weeks (Q3W)", "400 mg every 6 weeks (Q6W)"],
        "contraindications": ["None listed on US FDA approved label (weigh risk-benefit in active autoimmune disease)"],
        "black_box_warnings": [],
        "drug_interactions": [
            "Systemic Corticosteroids / Immunosuppressants: Avoid baseline high-dose steroids before initiation as they may diminish pharmacodynamic activity.",
            "Live vaccines: Avoid concomitant administration."
        ],
        "adverse_effects": {
            "common": ["Fatigue", "Musculoskeletal pain", "Decreased appetite", "Pruritus / Rash", "Diarrhea", "Nausea", "Cough"],
            "rare": ["Severe Immune-Mediated Endocrinopathies (Hypophysitis, Adrenal Insufficiency, Type 1 Diabetes)", "Myocarditis", "Encephalitis / Neuropathies", "Severe Cutaneous Adverse Reactions (SJS/TEN)"],
            "serious": ["Immune-Mediated Pneumonitis", "Immune-Mediated Colitis", "Immune-Mediated Hepatitis", "Immune-Mediated Nephritis"]
        },
        "special_populations": {
            "pregnancy": "Can cause fetal harm based on its mechanism of action; verify pregnancy status before initiating.",
            "lactation": "Advise women not to breastfeed during treatment and for 4 months after final dose.",
            "pediatric": "Approved for MSI-H/dMMR cancer, cHL, and Melanoma in pediatric patients.",
            "geriatric": "No overall differences in safety or efficacy observed in patients ≥65 years.",
            "renal_impairment": "No dose adjustment required in mild or moderate renal impairment; not studied in severe renal impairment.",
            "hepatic_impairment": "No dose adjustment needed in mild hepatic impairment."
        },
        "differentiating_science": "Revolutionized oncology by establishing immunotherapy as the 4th pillar of cancer care alongside surgery, chemotherapy, and radiation. KEYNOTE-189 proved a doubling of overall survival in metastatic NSCLC.",
        "key_targets": ["PDCD1 (PD-1 / CD279)"]
    },
    "apixaban": {
        "generic_name": "Apixaban",
        "chemical_name": "1-(4-methoxyphenyl)-7-oxo-6-[4-(2-oxopiperidin-1-yl)phenyl]-4,5-dihydropyrazolo[3,4-c]pyridine-3-carboxamide",
        "chemical_class": "Pyrazolopyridine / Piperidone derivative",
        "pharmacological_class": "Direct Oral Factor Xa Inhibitor (DOAC / NOAC)",
        "cas_number": "503612-47-3",
        "pubchem_cid": 10182969,
        "smiles": "COC1=CC=C(C=C1)N2C3=C(CCN(C3=O)C4=CC=C(C=C4)N5CCCCC5=O)C(=N2)C(=O)N",
        "molecular_formula": "C25H25N5O4",
        "molecular_weight": 459.50,
        "mechanism_of_action": "Potent, highly selective, reversible direct competitive inhibitor of free and clot-bound Factor Xa and prothrombinase activity. By inhibiting Factor Xa, it decreases thrombin generation and thrombus development without requiring antithrombin III cofactor.",
        "pharmacodynamics": "Dose-dependent prolongation of clotting tests (Anti-Factor Xa activity, PT/INR, aPTT). Achieves predictable anticoagulation without need for routine INR monitoring.",
        "pharmacokinetics": {
            "absorption": "Rapidly absorbed from the gastrointestinal tract; not significantly affected by food.",
            "bioavailability": "Approx. 50% absolute bioavailability.",
            "tmax": "3-4 hours post oral dose",
            "distribution": "Vd approx. 21 L; plasma protein binding is approx. 87%.",
            "protein_binding": "87% bound to plasma proteins",
            "metabolism": "Metabolized mainly via CYP3A4/5 with minor contributions from CYP1A2, 2C8, 2C9, 2C19, and 2J2. O-demethylation and sulfation.",
            "cyp_pathways": ["Substrate of CYP3A4 and P-glycoprotein (P-gp)."],
            "elimination": "Approx. 27% excreted renally as parent drug; remainder eliminated via biliary and direct intestinal excretion.",
            "half_life": "Approx. 12 hours (supports twice-daily BID dosing).",
            "clearance": "Total clearance approx. 3.3 L/h"
        },
        "approved_indications": [
            "Reduction of risk of stroke and systemic embolism in Non-Valvular Atrial Fibrillation (NVAF) - ARISTOTLE Trial",
            "Deep Vein Thrombosis (DVT) and Pulmonary Embolism (PE) treatment",
            "Reduction in the risk of recurrent DVT and PE following initial therapy",
            "Prophylaxis of DVT/PE in adult patients following elective hip or knee replacement surgery"
        ],
        "investigational_indications": ["Extended secondary stroke prevention in embolic stroke of undetermined source (ESUS)"],
        "dosage_forms": ["Oral Film-Coated Tablets (2.5 mg, 5 mg)"],
        "routes_of_administration": ["Oral (Twice Daily, morning and evening, with or without food)"],
        "standard_dosages": ["5 mg BID (Standard NVAF)", "2.5 mg BID (Dose reduction if at least 2 criteria met: Age ≥80, Weight ≤60 kg, Serum Creatinine ≥1.5 mg/dL)"],
        "contraindications": [
            "Active pathological bleeding",
            "Severe hypersensitivity to apixaban",
            "Prosthetic heart valves (mechanical)"
        ],
        "black_box_warnings": [
            "WARNING: PREMATURE DISCONTINUATION INCREASES RISK OF THROMBOTIC EVENTS. Discontinuing in the absence of adequate alternative anticoagulation increases stroke risk.",
            "WARNING: SPINAL/EPIDURAL HEMATOMA. Epidural or spinal hematomas may occur in patients receiving neuraxial anesthesia or spinal puncture."
        ],
        "drug_interactions": [
            "Strong dual inhibitors of CYP3A4 and P-gp (e.g. Ketoconazole, Itraconazole, Ritonavir): Reduce apixaban dose to 2.5 mg BID.",
            "Strong dual inducers of CYP3A4 and P-gp (e.g. Rifampin, Carbamazepine, Phenytoin, St. John's wort): Avoid concomitant use as efficacy is significantly reduced."
        ],
        "adverse_effects": {
            "common": ["Epistaxis", "Gingival bleeding", "Hematuria", "Bruising / Contusion", "Gastrointestinal hemorrhage"],
            "rare": ["Intracranial hemorrhage", "Retroperitoneal hemorrhage", "Spinal hematoma"],
            "serious": ["Major life-threatening hemorrhage (Reversible with Andexanet alfa / 4F-PCC)"]
        },
        "special_populations": {
            "pregnancy": "Avoid in pregnancy due to maternal and fetal hemorrhage risks.",
            "lactation": "Discontinue drug or discontinue nursing.",
            "pediatric": "Safety and effectiveness not established in pediatric patients.",
            "geriatric": "Standard dose reduction criteria incorporate age ≥80 years.",
            "renal_impairment": "No dose adjustment based solely on CrCl; standard dose reduction criteria apply. Can be used in ESRD on hemodialysis under specific guidance.",
            "hepatic_impairment": "No dose adjustment in mild/moderate hepatic impairment; not recommended in severe hepatic impairment."
        },
        "differentiating_science": "ARISTOTLE trial proved superior efficacy in stroke prevention with a remarkable 31% reduction in major bleeding and 11% reduction in all-cause mortality compared to Warfarin, making it the #1 prescribed oral anticoagulant globally.",
        "key_targets": ["F10 (Coagulation Factor Xa)"]
    }
}

async def _combination_profile(resolved) -> MoleculeProfile:
    """Compose a fixed-dose-combination profile from each component's profile.

    PubChem resolves single compounds only, so an FDC used to 404 and surface as
    "molecule not found". Each component is looked up on its own (curated first,
    then PubChem) and the results are merged, so a brand team sees the chemistry
    and class of every moiety instead of an empty record.
    """
    component_profiles = []
    for component in resolved.components:
        try:
            component_profiles.append(await fetch_molecule_intelligence(component))
        except Exception as exc:  # one bad component must not sink the whole FDC
            logger.warning("Component lookup failed for %s: %s", component, exc)

    def _blank_pk():
        return Pharmacokinetics(
            absorption="Not stated in the source record", bioavailability="Not stated in the source record", tmax="Not stated in the source record",
            distribution="Not stated in the source record", protein_binding="Not stated in the source record",
            metabolism="Not stated in the source record", cyp_pathways=[], elimination="Not stated in the source record",
            half_life="Not stated in the source record", clearance="Not stated in the source record",
        )

    def _blank_sp():
        return SpecialPopulations(
            pregnancy="Not stated in the source record", lactation="Not stated in the source record", pediatric="Not stated in the source record",
            geriatric="Not stated in the source record", renal_impairment="Not stated in the source record",
            hepatic_impairment="Not stated in the source record",
        )

    if not component_profiles:
        return MoleculeProfile(
            generic_name=resolved.display_name,
            chemical_class="Not stated in the source record",
            pharmacological_class="Not stated in the source record",
            smiles="", molecular_formula="",
            mechanism_of_action="No component of this combination could be resolved.",
            pharmacodynamics="Not verified.",
            pharmacokinetics=_blank_pk(),
            adverse_effects=AdverseEffects(common=[], rare=[], serious=[]),
            special_populations=_blank_sp(),
            differentiating_science=(
                f"No component of {resolved.display_name} resolved. Check the spelling "
                "of each molecule in the combination."
            ),
        )

    def merged_list(field: str):
        out = []
        for profile in component_profiles:
            for item in getattr(profile, field, None) or []:
                if item not in out:
                    out.append(item)
        return out

    classes = [
        f"{p.generic_name}: {p.pharmacological_class}"
        for p in component_profiles
        if p.pharmacological_class and p.pharmacological_class != "Not stated in the source record"
    ]
    moa = " | ".join(
        f"{p.generic_name} — {p.mechanism_of_action}"
        for p in component_profiles
        if p.mechanism_of_action and not p.mechanism_of_action.startswith("No verified")
    )
    pd = " | ".join(
        f"{p.generic_name} — {p.pharmacodynamics}"
        for p in component_profiles
        if p.pharmacodynamics and not p.pharmacodynamics.startswith("No verified")
    )

    adverse = AdverseEffects(
        common=merged_list("adverse_effects.common") if False else
            [a for p in component_profiles for a in (p.adverse_effects.common or [])],
        rare=[a for p in component_profiles for a in (p.adverse_effects.rare or [])],
        serious=[a for p in component_profiles for a in (p.adverse_effects.serious or [])],
    )

    return MoleculeProfile(
        generic_name=resolved.display_name,
        chemical_name=" ; ".join(p.chemical_name for p in component_profiles if p.chemical_name) or None,
        chemical_class="Fixed-dose combination",
        pharmacological_class="; ".join(classes) or "Not stated in the source record",
        cas_number=None,
        pubchem_cid=None,
        smiles=".".join(p.smiles for p in component_profiles if p.smiles),
        molecular_formula=" + ".join(p.molecular_formula for p in component_profiles if p.molecular_formula),
        molecular_weight=None,
        mechanism_of_action=moa or "Not verified for the combination.",
        pharmacodynamics=pd or "Not verified for the combination.",
        pharmacokinetics=_blank_pk(),
        approved_indications=merged_list("approved_indications"),
        investigational_indications=merged_list("investigational_indications"),
        dosage_forms=merged_list("dosage_forms"),
        routes_of_administration=merged_list("routes_of_administration"),
        standard_dosages=[],
        contraindications=merged_list("contraindications"),
        black_box_warnings=merged_list("black_box_warnings"),
        drug_interactions=merged_list("drug_interactions"),
        adverse_effects=adverse,
        special_populations=_blank_sp(),
        differentiating_science=(
            f"{resolved.display_name} is a fixed-dose combination of "
            f"{len(component_profiles)} moieties. Component chemistry and class are merged "
            "above. Combination-specific pharmacokinetics, efficacy, safety, and interaction "
            "data must come from the approved combination label — they cannot be inferred "
            "from the individual molecules."
        ),
        key_targets=merged_list("key_targets"),
    )


async def _fetch_molecule_intelligence_impl(molecule_name: str) -> MoleculeProfile:
    """Molecule profile: chemistry from PubChem, pharmacology from the FDA label.

    PubChem is a chemical registry — it answers formula, weight, and structure,
    and carries no pharmacology at all. On its own it left every clinical field
    reading "Not stated in the source record" for any molecule without a hand-written entry.

    So the chemistry layer is enriched from the molecule's FDA structured
    product label, which is where class, mechanism, indications, dosing,
    contraindications, and interactions actually live. Enrichment only fills
    fields that are empty, so curated values always win.

    PubChem and openFDA are fetched concurrently rather than one after the
    other: neither depends on the other's network response — enrichment only
    needs the chemistry profile's *values* to decide what's already filled,
    which happens after both round trips are back, not during either of
    them. Measured live: sequential fetching made GET /api/molecules/search
    take ~7s for a molecule needing openFDA's synonym retry; fetching
    concurrently removes the chemistry round trip from that critical path
    entirely rather than adding it on top.
    """
    profile, clinical = await asyncio.gather(
        _chemistry_profile(molecule_name),
        _fetch_clinical_enrichment(molecule_name),
    )
    return _apply_enrichment(profile, clinical)


async def _chemistry_profile(molecule_name: str) -> MoleculeProfile:
    """Chemistry-layer profile: curated entry, combination, or PubChem."""
    clean_name = molecule_name.strip().lower()

    if clean_name in CURATED_MOLECULES:
        data = CURATED_MOLECULES[clean_name]
        return MoleculeProfile(**data)

    # PubChem resolves single compounds only — a fixed-dose combination returns
    # 404 and used to surface as "molecule not found". Build the combination
    # profile from its components instead.
    resolved = resolve_molecule(molecule_name)
    if resolved.is_combination:
        return await _combination_profile(resolved)
    
    # Try querying PubChem REST API
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            cid_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{molecule_name}/cids/JSON"
            cid_resp = await client.get(cid_url)
            
            if cid_resp.status_code == 200:
                cid_data = cid_resp.json()
                cids = cid_data.get("IdentifierList", {}).get("CID", [])
                if cids:
                    cid = cids[0]
                    prop_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/property/MolecularFormula,MolecularWeight,IUPACName,CanonicalSMILES/JSON"
                    prop_resp = await client.get(prop_url)
                    
                    if prop_resp.status_code == 200:
                        props = prop_resp.json().get("PropertyTable", {}).get("Properties", [{}])[0]
                        
                        return MoleculeProfile(
                            generic_name=molecule_name.title(),
                            chemical_name=props.get("IUPACName", f"{molecule_name.title()} compound"),
                            chemical_class="Chemical record from PubChem",
                            pharmacological_class="Not verified in this application",
                            pubchem_cid=cid,
                            smiles=props.get("CanonicalSMILES", ""),
                            molecular_formula=props.get("MolecularFormula", ""),
                            molecular_weight=float(props.get("MolecularWeight", 0.0)) if props.get("MolecularWeight") else None,
                            mechanism_of_action="Not available from PubChem. Requires verified pharmacology source review.",
                            pharmacodynamics="Not available from PubChem. Requires verified clinical/pharmacology source review.",
                            pharmacokinetics=Pharmacokinetics(
                                absorption="Not stated in the source record",
                                bioavailability="Not stated in the source record",
                                tmax="Not stated in the source record",
                                distribution="Not stated in the source record",
                                protein_binding="Not stated in the source record",
                                metabolism="Not stated in the source record",
                                cyp_pathways=[],
                                elimination="Not stated in the source record",
                                half_life="Not stated in the source record",
                                clearance="Not stated in the source record"
                            ),
                            approved_indications=[],
                            investigational_indications=[],
                            dosage_forms=[],
                            routes_of_administration=[],
                            standard_dosages=[],
                            contraindications=[],
                            black_box_warnings=[],
                            drug_interactions=[],
                            adverse_effects=AdverseEffects(
                                common=[],
                                rare=[],
                                serious=[]
                            ),
                            special_populations=SpecialPopulations(
                                pregnancy="Not stated in the source record",
                                lactation="Not stated in the source record",
                                pediatric="Not stated in the source record",
                                geriatric="Not stated in the source record",
                                renal_impairment="Not stated in the source record",
                                hepatic_impairment="Not stated in the source record"
                            ),
                            differentiating_science="Not assessed. Requires source-backed medical review.",
                            key_targets=[]
                        )
    except Exception as e:
        logger.warning(f"PubChem live fetch failed for {molecule_name}: {e}")
    
    # No verified molecule record found.
    return MoleculeProfile(
        generic_name=molecule_name.title(),
        chemical_name=None,
        chemical_class="Not stated in the source record",
        pharmacological_class="Not stated in the source record",
        pubchem_cid=None,
        smiles="",
        molecular_formula="",
        molecular_weight=None,
        mechanism_of_action="No verified mechanism found. Add validated source before use.",
        pharmacodynamics="No verified pharmacodynamic data found.",
        pharmacokinetics=Pharmacokinetics(
            absorption="Not stated in the source record",
            bioavailability="Not stated in the source record",
            tmax="Not stated in the source record",
            distribution="Not stated in the source record",
            protein_binding="Not stated in the source record",
            metabolism="Not stated in the source record",
            cyp_pathways=[],
            elimination="Not stated in the source record",
            half_life="Not stated in the source record",
            clearance="Not stated in the source record"
        ),
        approved_indications=[],
        investigational_indications=[],
        dosage_forms=[],
        routes_of_administration=[],
        standard_dosages=[],
        contraindications=[],
        black_box_warnings=[],
        drug_interactions=[],
        adverse_effects=AdverseEffects(
            common=[],
            rare=[],
            serious=[]
        ),
        special_populations=SpecialPopulations(
            pregnancy="Not stated in the source record",
            lactation="Not stated in the source record",
            pediatric="Not stated in the source record",
            geriatric="Not stated in the source record",
            renal_impairment="Not stated in the source record",
            hepatic_impairment="Not stated in the source record"
        ),
        differentiating_science="No verified differentiation claim is available.",
        key_targets=[]
    )


async def _fetch_clinical_enrichment(molecule_name: str) -> Optional[Dict[str, Any]]:
    """The openFDA fetch half of enrichment, kept separate so it can run
    concurrently with the PubChem chemistry fetch rather than after it.
    """
    try:
        return await fetch_molecule_clinical_profile(molecule_name)
    except Exception:
        logger.warning("openFDA clinical enrichment failed for %s", molecule_name, exc_info=True)
        return None


def _apply_enrichment(profile: MoleculeProfile, clinical: Optional[Dict[str, Any]]) -> MoleculeProfile:
    """Fill the clinical fields PubChem cannot answer, from already-fetched
    FDA label data.

    PubChem is a chemical registry — formula, weight, SMILES. It has no
    pharmacology, so every clinical field on a non-curated molecule rendered
    "Not stated in the source record". Those exact fields live on the FDA structured product label.

    Only empty fields are filled: a curated or PubChem-supplied value always
    wins, and a label section the SPL omits leaves the field as it was rather
    than borrowing text from a different product. Purely synchronous — no
    network call happens here, it only merges what _fetch_clinical_enrichment
    already retrieved.
    """
    if not clinical:
        return profile

    _PLACEHOLDER = ("not stated in the source record", "not verified", "not available", "")

    def blank(value) -> bool:
        if value is None:
            return True
        if isinstance(value, str):
            lowered = value.strip().lower()
            return any(lowered.startswith(p) for p in _PLACEHOLDER if p) or lowered == ""
        return len(value) == 0

    updates: Dict[str, Any] = {}
    for field in ("pharmacological_class", "mechanism_of_action", "pharmacodynamics",
                  "approved_indications", "dosage_forms", "routes_of_administration",
                  "standard_dosages", "contraindications", "black_box_warnings",
                  "drug_interactions"):
        incoming = clinical.get(field)
        if incoming and blank(getattr(profile, field, None)):
            updates[field] = incoming

    pk_incoming = clinical.get("pharmacokinetics") or {}
    pk_updates = {
        field: value for field, value in pk_incoming.items()
        if value and blank(getattr(profile.pharmacokinetics, field, None))
    }
    if pk_updates:
        updates["pharmacokinetics"] = profile.pharmacokinetics.model_copy(update=pk_updates)

    adverse = clinical.get("adverse_effects") or []
    if adverse and not profile.adverse_effects.common:
        updates["adverse_effects"] = profile.adverse_effects.model_copy(
            update={"common": adverse[:10]})

    return profile.model_copy(update=updates) if updates else profile


# openFDA's own live latency dominates this call for any non-curated
# molecule, paid again on every page load — see regulatory_service.py's
# identical rationale. A molecule's chemistry and label content change on
# the order of months, not between one page view and the next.
MOLECULE_PROFILE_CACHE_TTL_HOURS = 24 * 7


async def fetch_molecule_intelligence(molecule_name: str) -> MoleculeProfile:
    """Molecule profile — cached. See _fetch_molecule_intelligence_impl for
    what this actually computes; this wrapper only adds the cache-or-fetch
    layer in front of it.
    """
    return await response_cache.get_or_fetch(
        cache_key=f"molecule_profile:{molecule_name.strip().lower()}",
        ttl_hours=MOLECULE_PROFILE_CACHE_TTL_HOURS,
        fetch=lambda: _fetch_molecule_intelligence_impl(molecule_name),
        to_dict=lambda p: p.model_dump(),
        from_dict=lambda d: MoleculeProfile.model_validate(d),
    )
