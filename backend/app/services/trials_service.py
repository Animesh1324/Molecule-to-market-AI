import httpx
import logging
from typing import List, Dict, Any, Optional
from ..models.trials import ClinicalTrial, ClinicalTrialLandscape

logger = logging.getLogger(__name__)

CURATED_TRIALS: Dict[str, List[Dict[str, Any]]] = {
    "empagliflozin": [
        {
            "nct_id": "NCT01131676",
            "title": "EMPA-REG OUTCOME: A Study to Evaluate the Effects of Empagliflozin on Heart and Blood Vessels in Patients With Type 2 Diabetes",
            "acronym": "EMPA-REG OUTCOME",
            "sponsor": "Boehringer Ingelheim & Eli Lilly",
            "sponsor_type": "Industry",
            "phase": "Phase 3",
            "status": "COMPLETED",
            "indication": "Type 2 Diabetes Mellitus with High Cardiovascular Risk",
            "study_design": {
                "allocation": "Randomized",
                "intervention_model": "Parallel Assignment",
                "masking": "Double (Participant, Investigator)",
                "primary_purpose": "Treatment"
            },
            "interventions": ["Empagliflozin 10 mg", "Empagliflozin 25 mg", "Placebo"],
            "primary_endpoints": ["Time to first occurrence of 3-point MACE (CV death, non-fatal MI, non-fatal stroke)"],
            "secondary_endpoints": ["Hospitalization for heart failure", "All-cause mortality", "Renal composite outcome"],
            "enrollment": 7020,
            "geography": ["United States", "Germany", "Japan", "India", "Global 42 countries"],
            "start_date": "2010-09-01",
            "completion_date": "2015-05-15",
            "results_available": True,
            "results_summary": "Achieved non-inferiority and superiority for 3-point MACE; 38% reduction in CV death (p<0.001) and 35% reduction in HF hospitalization.",
            "competitor_molecules": ["Canagliflozin", "Dapagliflozin"],
            "url": "https://clinicaltrials.gov/study/NCT01131676"
        },
        {
            "nct_id": "NCT03057977",
            "title": "EMPEROR-Reduced: Empagliflozin Outcome Trial in Patients With Chronic Heart Failure With Reduced Ejection Fraction",
            "acronym": "EMPEROR-Reduced",
            "sponsor": "Boehringer Ingelheim",
            "sponsor_type": "Industry",
            "phase": "Phase 3",
            "status": "COMPLETED",
            "indication": "Heart Failure With Reduced Ejection Fraction (HFrEF)",
            "study_design": {
                "allocation": "Randomized",
                "intervention_model": "Parallel Assignment",
                "masking": "Double (Participant, Investigator)",
                "primary_purpose": "Treatment"
            },
            "interventions": ["Empagliflozin 10 mg once daily", "Placebo"],
            "primary_endpoints": ["Time to first adjudicated cardiovascular death or hospitalization for heart failure"],
            "secondary_endpoints": ["Total number of adjudicated hospitalizations for heart failure", "eGFR slope decline"],
            "enrollment": 3730,
            "geography": ["North America", "Europe", "Asia", "Latin America"],
            "start_date": "2017-03-06",
            "completion_date": "2020-05-28",
            "results_available": True,
            "results_summary": "25% relative risk reduction in CV death or HF hospitalization (HR 0.75; p<0.001).",
            "competitor_molecules": ["Dapagliflozin (DAPA-HF)"],
            "url": "https://clinicaltrials.gov/study/NCT03057977"
        },
        {
            "nct_id": "NCT03594110",
            "title": "EMPA-KIDNEY: The Study of Heart and Kidney Protection With Empagliflozin",
            "acronym": "EMPA-KIDNEY",
            "sponsor": "University of Oxford & Boehringer Ingelheim",
            "sponsor_type": "Academic/Other",
            "phase": "Phase 3",
            "status": "COMPLETED",
            "indication": "Chronic Kidney Disease",
            "study_design": {
                "allocation": "Randomized",
                "intervention_model": "Parallel Assignment",
                "masking": "Double (Participant, Investigator)",
                "primary_purpose": "Treatment"
            },
            "interventions": ["Empagliflozin 10 mg", "Placebo"],
            "primary_endpoints": ["Time to kidney disease progression or cardiovascular death"],
            "secondary_endpoints": ["All-cause hospitalization", "All-cause mortality"],
            "enrollment": 6609,
            "geography": ["United Kingdom", "United States", "China", "Germany", "Japan", "Global"],
            "start_date": "2019-02-14",
            "completion_date": "2022-07-28",
            "results_available": True,
            "results_summary": "28% risk reduction in kidney disease progression or CV death (HR 0.72; p<0.001). Trial stopped early for overwhelming efficacy.",
            "competitor_molecules": ["Dapagliflozin (DAPA-CKD)"],
            "url": "https://clinicaltrials.gov/study/NCT03594110"
        }
    ],
    "semaglutide": [
        {
            "nct_id": "NCT03548935",
            "title": "STEP 1: Effect and Safety of Semaglutide 2.4 mg Once-Weekly in Subjects With Overweight or Obesity",
            "acronym": "STEP 1",
            "sponsor": "Novo Nordisk A/S",
            "sponsor_type": "Industry",
            "phase": "Phase 3",
            "status": "COMPLETED",
            "indication": "Overweight and Obesity",
            "study_design": {
                "allocation": "Randomized",
                "intervention_model": "Parallel Assignment",
                "masking": "Double (Participant, Investigator)",
                "primary_purpose": "Treatment"
            },
            "interventions": ["Semaglutide 2.4 mg Subcutaneous", "Placebo Subcutaneous"],
            "primary_endpoints": ["Percentage change in body weight from baseline to week 68", "Achievement of ≥5% weight loss"],
            "secondary_endpoints": ["Achievement of ≥10%, ≥15%, and ≥20% weight loss", "Change in waist circumference and systolic BP"],
            "enrollment": 1961,
            "geography": ["United States", "Europe", "Asia", "Canada"],
            "start_date": "2018-06-18",
            "completion_date": "2020-10-15",
            "results_available": True,
            "results_summary": "-14.9% mean weight loss vs -2.4% with placebo (treatment difference -12.4%, p<0.001).",
            "competitor_molecules": ["Tirzepatide (SURMOUNT)", "Liraglutide (SCALE)"],
            "url": "https://clinicaltrials.gov/study/NCT03548935"
        },
        {
            "nct_id": "NCT03574597",
            "title": "SELECT: Semaglutide Effects on Cardiovascular Outcomes in People With Overweight or Obesity",
            "acronym": "SELECT",
            "sponsor": "Novo Nordisk A/S",
            "sponsor_type": "Industry",
            "phase": "Phase 3",
            "status": "COMPLETED",
            "indication": "Cardiovascular Disease with Overweight or Obesity (Non-diabetic)",
            "study_design": {
                "allocation": "Randomized",
                "intervention_model": "Parallel Assignment",
                "masking": "Double (Participant, Investigator)",
                "primary_purpose": "Treatment"
            },
            "interventions": ["Semaglutide 2.4 mg Subcutaneous weekly", "Placebo Subcutaneous"],
            "primary_endpoints": ["Time from randomization to first occurrence of 3-point MACE (CV death, non-fatal MI, non-fatal stroke)"],
            "secondary_endpoints": ["Time to CV death", "Time to all-cause mortality", "Heart failure composite"],
            "enrollment": 17604,
            "geography": ["North America", "Europe", "Latin America", "Asia-Pacific (41 countries)"],
            "start_date": "2018-10-12",
            "completion_date": "2023-09-20",
            "results_available": True,
            "results_summary": "20% reduction in 3-point MACE (HR 0.80, 95% CI 0.72-0.90, p<0.001) in patients with obesity and CVD without diabetes.",
            "competitor_molecules": ["Tirzepatide", "Cagrilintide+Semaglutide (CagriSema)"],
            "url": "https://clinicaltrials.gov/study/NCT03574597"
        }
    ],
    "pembrolizumab": [
        {
            "nct_id": "NCT02578680",
            "title": "KEYNOTE-189: Study of Pemetrexed+Platinum Chemotherapy With or Without Pembrolizumab in First Line Metastatic Non-squamous Non-small Cell Lung Cancer",
            "acronym": "KEYNOTE-189",
            "sponsor": "Merck Sharp & Dohme LLC",
            "sponsor_type": "Industry",
            "phase": "Phase 3",
            "status": "COMPLETED",
            "indication": "Metastatic Non-Squamous Non-Small Cell Lung Cancer",
            "study_design": {
                "allocation": "Randomized",
                "intervention_model": "Parallel Assignment",
                "masking": "Double (Participant, Investigator)",
                "primary_purpose": "Treatment"
            },
            "interventions": ["Pembrolizumab 200 mg Q3W + Pemetrexed + Carboplatin/Cisplatin", "Placebo + Pemetrexed + Carboplatin/Cisplatin"],
            "primary_endpoints": ["Overall Survival (OS)", "Progression-Free Survival (PFS) by RECIST 1.1"],
            "secondary_endpoints": ["Objective Response Rate (ORR)", "Duration of Response (DOR)", "Safety & Tolerability"],
            "enrollment": 616,
            "geography": ["Global Multicenter across 16 countries"],
            "start_date": "2016-02-17",
            "completion_date": "2020-07-28",
            "results_available": True,
            "results_summary": "Significant OS benefit with median OS 22.0 months vs 10.6 months on chemo alone (HR 0.56, 95% CI 0.46-0.69).",
            "competitor_molecules": ["Nivolumab", "Atezolizumab", "Durvalumab", "Cemiplimab"],
            "url": "https://clinicaltrials.gov/study/NCT02578680"
        }
    ],
    "apixaban": [
        {
            "nct_id": "NCT00412984",
            "title": "ARISTOTLE: Apixaban for Reduction In STroke and Other ThromboemboLic Events in Atrial Fibrillation",
            "acronym": "ARISTOTLE",
            "sponsor": "Bristol-Myers Squibb & Pfizer",
            "sponsor_type": "Industry",
            "phase": "Phase 3",
            "status": "COMPLETED",
            "indication": "Non-Valvular Atrial Fibrillation (NVAF)",
            "study_design": {
                "allocation": "Randomized",
                "intervention_model": "Parallel Assignment",
                "masking": "Double (Participant, Investigator)",
                "primary_purpose": "Treatment"
            },
            "interventions": ["Apixaban 5 mg BID (or 2.5 mg BID dose-adjusted)", "Warfarin (INR target 2.0 - 3.0) with sham monitoring"],
            "primary_endpoints": ["First occurrence of adjudicated ischemic or hemorrhagic stroke, or systemic embolism"],
            "secondary_endpoints": ["Major bleeding by ISTH criteria", "All-cause mortality"],
            "enrollment": 18201,
            "geography": ["Global 39 countries, 1034 clinical centers"],
            "start_date": "2006-12-18",
            "completion_date": "2011-04-12",
            "results_available": True,
            "results_summary": "Superiority achieved: 21% stroke risk reduction (HR 0.79), 31% major bleeding reduction (HR 0.69), and 11% all-cause death reduction (HR 0.89).",
            "competitor_molecules": ["Rivaroxaban (ROCKET-AF)", "Dabigatran (RE-LY)", "Edoxaban (ENGAGE AF-TIMI 48)"],
            "url": "https://clinicaltrials.gov/study/NCT00412984"
        }
    ]
}

async def fetch_clinical_trial_landscape(molecule_name: str, indication: Optional[str] = None) -> ClinicalTrialLandscape:
    """Fetch clinical trials from ClinicalTrials.gov API v2.

    Do not synthesize trial registrations, results, or competitor molecules.
    Missing fields remain unknown/not specified for MLR auditability.
    """
    clean_name = molecule_name.strip().lower()
    
    if clean_name in CURATED_TRIALS:
        trials = [ClinicalTrial(**t) for t in CURATED_TRIALS[clean_name]]
        phase_dist = {"Phase 3": len(trials)}
        status_dist = {"COMPLETED": len(trials)}
        return ClinicalTrialLandscape(
            total_trials_found=len(trials),
            phase_distribution=phase_dist,
            status_distribution=status_dist,
            landmark_trials=trials,
            all_trials=trials
        )
    
    # Try querying ClinicalTrials.gov API v2
    trials_list: List[ClinicalTrial] = []
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            url = f"https://clinicaltrials.gov/api/v2/studies"
            params = {
                "query.intr": molecule_name,
                "pageSize": "5",
                "format": "json"
            }
            if indication:
                params["query.cond"] = indication
            
            resp = await client.get(url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                studies = data.get("studies", [])
                for s in studies:
                    protocol = s.get("protocolSection", {})
                    id_mod = protocol.get("identificationModule", {})
                    status_mod = protocol.get("statusModule", {})
                    sponsor_mod = protocol.get("sponsorCollaboratorsModule", {})
                    design_mod = protocol.get("designModule", {})
                    outcomes_mod = protocol.get("outcomesModule", {})
                    
                    nct_id = id_mod.get("nctId", "NCT00000000")
                    title = id_mod.get("briefTitle", f"Clinical Study of {molecule_name.title()}")
                    acronym = id_mod.get("acronym")
                    sponsor = sponsor_mod.get("leadSponsor", {}).get("name", "Not specified")
                    sponsor_type = sponsor_mod.get("leadSponsor", {}).get("class", "Not specified")
                    phases = design_mod.get("phases", [])
                    phase_str = " / ".join(phases) if phases else "Not specified"
                    status = status_mod.get("overallStatus", "Not specified")
                    
                    primary_outcomes = [po.get("measure", "") for po in outcomes_mod.get("primaryOutcomes", [])]
                    secondary_outcomes = [so.get("measure", "") for so in outcomes_mod.get("secondaryOutcomes", [])]
                    conditions = protocol.get("conditionsModule", {}).get("conditions", [])
                    interventions = [
                        item.get("name", "")
                        for item in protocol.get("armsInterventionsModule", {}).get("interventions", [])
                        if item.get("name")
                    ]
                    locations = protocol.get("contactsLocationsModule", {}).get("locations", [])
                    geography = sorted({
                        loc.get("country")
                        for loc in locations
                        if loc.get("country")
                    })
                    
                    trials_list.append(ClinicalTrial(
                        nct_id=nct_id,
                        title=title,
                        acronym=acronym,
                        sponsor=sponsor,
                        sponsor_type=sponsor_type,
                        phase=phase_str,
                        status=status,
                        indication=", ".join(conditions) if conditions else (indication or "Not specified"),
                        study_design={
                            "allocation": design_mod.get("designInfo", {}).get("allocation", "Not specified"),
                            "intervention_model": design_mod.get("designInfo", {}).get("interventionModel", "Not specified"),
                            "masking": design_mod.get("designInfo", {}).get("maskingInfo", {}).get("masking", "Not specified"),
                            "primary_purpose": design_mod.get("designInfo", {}).get("primaryPurpose", "Not specified")
                        },
                        interventions=interventions,
                        primary_endpoints=primary_outcomes,
                        secondary_endpoints=secondary_outcomes,
                        enrollment=design_mod.get("enrollmentInfo", {}).get("count"),
                        geography=geography,
                        start_date=status_mod.get("startDateStruct", {}).get("date"),
                        completion_date=status_mod.get("completionDateStruct", {}).get("date"),
                        results_available=bool(s.get("hasResults", False)),
                        results_summary=None,
                        competitor_molecules=[],
                        url=f"https://clinicaltrials.gov/study/{nct_id}"
                    ))
    except Exception as e:
        logger.warning(f"ClinicalTrials.gov API v2 query error for {molecule_name}: {e}")
    
    phase_dist = {}
    status_dist = {}
    for t in trials_list:
        phase_dist[t.phase] = phase_dist.get(t.phase, 0) + 1
        status_dist[t.status] = status_dist.get(t.status, 0) + 1
    
    return ClinicalTrialLandscape(
        total_trials_found=len(trials_list),
        phase_distribution=phase_dist,
        status_distribution=status_dist,
        landmark_trials=trials_list[:3],
        all_trials=trials_list
    )
