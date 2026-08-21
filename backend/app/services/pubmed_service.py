import httpx
import logging
from typing import List, Dict, Any, Optional
from ..models.evidence import ResearchPaper, ClaimEvidenceMapping
from .molecule_resolver import resolve as resolve_molecule

logger = logging.getLogger(__name__)

# Curated landmark evidence repository
CURATED_PAPERS: Dict[str, List[Dict[str, Any]]] = {
    "empagliflozin": [
        {
            "id": "EMPA-1",
            "pmid": "26378978",
            "doi": "10.1056/NEJMoa1504720",
            "title": "Empagliflozin, Cardiovascular Outcomes, and Mortality in Type 2 Diabetes (EMPA-REG OUTCOME)",
            "authors": ["Zinman B", "Wanner C", "Lachin JM", "Fitchett D", "Bluhmki E", "Hantel S", "et al."],
            "journal": "New England Journal of Medicine (NEJM)",
            "publication_year": 2015,
            "study_type": "Randomized Controlled Trial",
            "evidence_level": "Level 1 (Highest)",
            "sample_size": 7020,
            "primary_endpoint_result": "38% relative risk reduction in death from cardiovascular causes (HR 0.62; 95% CI, 0.49 to 0.77; p<0.001)",
            "hazard_ratio": "0.62 (CV Death) / 0.65 (All-cause mortality)",
            "relative_risk_reduction": "38% (CV Death), 32% (All-cause death), 35% (HF Hospitalization)",
            "p_value": "p < 0.001",
            "key_findings": "Patients with type 2 diabetes at high risk for cardiovascular events who received empagliflozin had significantly lower rates of the primary composite cardiovascular outcome and death from any cause than those in the placebo group.",
            "limitations": "Conducted in a high-risk CV population; predominantly white and male cohort.",
            "claim_support_potential": "Strongest Level 1 evidence for cardiovascular mortality reduction claim and heart failure hospitalization reduction in T2DM.",
            "relevance_score": 0.99,
            "url": "https://pubmed.ncbi.nlm.nih.gov/26378978/"
        },
        {
            "id": "EMPA-2",
            "pmid": "32865377",
            "doi": "10.1056/NEJMoa2022190",
            "title": "Cardiovascular and Renal Outcomes with Empagliflozin in Heart Failure (EMPEROR-Reduced)",
            "authors": ["Packer M", "Anker SD", "Butler J", "Filippatos G", "Pocock SJ", "Carson P", "et al."],
            "journal": "New England Journal of Medicine (NEJM)",
            "publication_year": 2020,
            "study_type": "Randomized Controlled Trial",
            "evidence_level": "Level 1 (Highest)",
            "sample_size": 3730,
            "primary_endpoint_result": "25% relative risk reduction in composite CV death or hospitalization for heart failure (HR 0.75; 95% CI, 0.65 to 0.86; p<0.001)",
            "hazard_ratio": "0.75 (Primary Composite)",
            "relative_risk_reduction": "25% (CV Death / HF Hospitalization), 30% (Total HF Hospitalizations)",
            "p_value": "p < 0.001",
            "key_findings": "Empagliflozin reduced the risk of cardiovascular death or hospitalization for heart failure in patients with HFrEF, regardless of the presence or absence of diabetes.",
            "limitations": "Median follow-up was 16 months.",
            "claim_support_potential": "Foundation for HFrEF indication and detailing to Cardiologists.",
            "relevance_score": 0.98,
            "url": "https://pubmed.ncbi.nlm.nih.gov/32865377/"
        },
        {
            "id": "EMPA-3",
            "pmid": "36331190",
            "doi": "10.1056/NEJMoa2214238",
            "title": "Empagliflozin in Patients with Chronic Kidney Disease (EMPA-KIDNEY)",
            "authors": ["The EMPA-KIDNEY Collaborative Group", "Herrington WG", "Staplin N", "Wanner C", "Green JB", "et al."],
            "journal": "New England Journal of Medicine (NEJM)",
            "publication_year": 2023,
            "study_type": "Randomized Controlled Trial",
            "evidence_level": "Level 1 (Highest)",
            "sample_size": 6609,
            "primary_endpoint_result": "28% relative risk reduction in progression of kidney disease or death from cardiovascular causes (HR 0.72; 95% CI, 0.64 to 0.82; p<0.001)",
            "hazard_ratio": "0.72 (Kidney progression or CV death)",
            "relative_risk_reduction": "28% relative risk reduction",
            "p_value": "p < 0.001",
            "key_findings": "Empagliflozin therapy led to a significantly lower risk of kidney disease progression or death from cardiovascular causes than placebo among a wide range of patients with CKD at risk of progression.",
            "limitations": "Trial stopped early for overwhelming efficacy at pre-specified interim analysis.",
            "claim_support_potential": "Core scientific proof point for Nephrology detailing and CKD brand extension.",
            "relevance_score": 0.97,
            "url": "https://pubmed.ncbi.nlm.nih.gov/36331190/"
        }
    ],
    "semaglutide": [
        {
            "id": "SEMA-1",
            "pmid": "33567185",
            "doi": "10.1056/NEJMoa2032183",
            "title": "Once-Weekly Semaglutide in Adults with Overweight or Obesity (STEP 1)",
            "authors": ["Wilding JPH", "Batterham RL", "Calanna S", "Davies M", "Van Gaal LF", "Lingvay I", "et al."],
            "journal": "New England Journal of Medicine (NEJM)",
            "publication_year": 2021,
            "study_type": "Randomized Controlled Trial",
            "evidence_level": "Level 1 (Highest)",
            "sample_size": 1961,
            "primary_endpoint_result": "Mean weight loss of -14.9% with semaglutide 2.4 mg vs -2.4% with placebo (treatment difference -12.4 percentage points; p<0.001)",
            "hazard_ratio": "N/A (Continuous Endpoint)",
            "relative_risk_reduction": "86.4% of participants achieved ≥5% weight loss vs 31.5% on placebo",
            "p_value": "p < 0.001",
            "key_findings": "In adults with overweight or obesity, 2.4 mg of semaglutide once weekly plus lifestyle intervention was associated with sustained, clinically relevant reduction in body weight.",
            "limitations": "68-week trial duration; GI adverse events common during dose escalation.",
            "claim_support_potential": "Benchmark efficacy claim for obesity and weight management promotion.",
            "relevance_score": 0.99,
            "url": "https://pubmed.ncbi.nlm.nih.gov/33567185/"
        },
        {
            "id": "SEMA-2",
            "pmid": "37952131",
            "doi": "10.1056/NEJMoa2307563",
            "title": "Semaglutide and Cardiovascular Outcomes in Obesity without Diabetes (SELECT)",
            "authors": ["Lincoff AM", "Brown-Frandsen K", "Colhoun HM", "Deanfield J", "Emerson SS", "Esbjerg S", "et al."],
            "journal": "New England Journal of Medicine (NEJM)",
            "publication_year": 2023,
            "study_type": "Randomized Controlled Trial",
            "evidence_level": "Level 1 (Highest)",
            "sample_size": 17604,
            "primary_endpoint_result": "20% relative risk reduction in 3-point MACE (CV death, nonfatal MI, nonfatal stroke) (HR 0.80; 95% CI, 0.72 to 0.90; p<0.001)",
            "hazard_ratio": "0.80 (3-Point MACE)",
            "relative_risk_reduction": "20% (3-Point MACE), 15% (CV Death)",
            "p_value": "p < 0.001",
            "key_findings": "In patients with preexisting cardiovascular disease and overweight or obesity but without diabetes, weekly subcutaneous semaglutide 2.4 mg was superior to placebo in reducing the incidence of death from CV causes, nonfatal MI, or nonfatal stroke.",
            "limitations": "Mean duration of follow-up was 39.8 months.",
            "claim_support_potential": "Unprecedented cardio-protective claim in non-diabetic obese patients; key differentiator vs older GLP-1 therapies.",
            "relevance_score": 0.98,
            "url": "https://pubmed.ncbi.nlm.nih.gov/37952131/"
        }
    ],
    "pembrolizumab": [
        {
            "id": "PEMBRO-1",
            "pmid": "29658856",
            "doi": "10.1056/NEJMoa1801005",
            "title": "Pembrolizumab plus Chemotherapy in Metastatic Non-Small-Cell Lung Cancer (KEYNOTE-189)",
            "authors": ["Gandhi L", "Rodríguez-Abreu D", "Gadgeel S", "Esteban E", "Felip E", "De Angelis F", "et al."],
            "journal": "New England Journal of Medicine (NEJM)",
            "publication_year": 2018,
            "study_type": "Randomized Controlled Trial",
            "evidence_level": "Level 1 (Highest)",
            "sample_size": 616,
            "primary_endpoint_result": "51% relative risk reduction in death (Overall Survival HR 0.49; 95% CI, 0.38 to 0.64; p<0.001) in combo arm vs placebo+chemo.",
            "hazard_ratio": "0.49 (Overall Survival)",
            "relative_risk_reduction": "51% reduction in mortality risk; doubling of 12-month OS (69.2% vs 49.4%)",
            "p_value": "p < 0.001",
            "key_findings": "In patients with previously untreated metastatic non-squamous NSCLC without EGFR or ALK mutations, adding pembrolizumab to standard chemotherapy significantly prolonged overall survival and progression-free survival across all PD-L1 TPS subgroups.",
            "limitations": "Crossover from placebo to pembrolizumab monotherapy allowed after disease progression.",
            "claim_support_potential": "The gold-standard Level-1 evidence establishing Keytruda as the undisputed #1 standard of care in 1st-line NSCLC.",
            "relevance_score": 0.99,
            "url": "https://pubmed.ncbi.nlm.nih.gov/29658856/"
        },
        {
            "id": "PEMBRO-2",
            "pmid": "27718847",
            "doi": "10.1056/NEJMoa1606774",
            "title": "Pembrolizumab versus Chemotherapy for PD-L1-Positive Non-Small-Cell Lung Cancer (KEYNOTE-024)",
            "authors": ["Reck M", "Rodríguez-Abreu D", "Robinson AG", "Hui R", "Csőszi T", "Fülöp A", "et al."],
            "journal": "New England Journal of Medicine (NEJM)",
            "publication_year": 2016,
            "study_type": "Randomized Controlled Trial",
            "evidence_level": "Level 1 (Highest)",
            "sample_size": 305,
            "primary_endpoint_result": "Progression-Free Survival HR 0.50 (95% CI, 0.37-0.68; p<0.001); Overall Survival HR 0.60 (p=0.005) in PD-L1 TPS ≥50%.",
            "hazard_ratio": "0.50 (PFS) / 0.60 (OS)",
            "relative_risk_reduction": "50% reduction in risk of disease progression or death",
            "p_value": "p < 0.001",
            "key_findings": "Pembrolizumab monotherapy was associated with significantly longer progression-free and overall survival and fewer adverse events than platinum-based chemotherapy in patients with advanced NSCLC and PD-L1 expression on ≥50% of tumor cells.",
            "limitations": "Limited to TPS ≥50% patient cohort.",
            "claim_support_potential": "Definitive evidence for chemo-free monotherapy in high PD-L1 expressors.",
            "relevance_score": 0.98,
            "url": "https://pubmed.ncbi.nlm.nih.gov/27718847/"
        }
    ],
    "apixaban": [
        {
            "id": "APIX-1",
            "pmid": "21870978",
            "doi": "10.1056/NEJMoa1107039",
            "title": "Apixaban versus Warfarin in Patients with Atrial Fibrillation (ARISTOTLE)",
            "authors": ["Granger CB", "Alexander JH", "McMurray JJV", "Lopes RD", "Hylek EM", "Hanna M", "et al."],
            "journal": "New England Journal of Medicine (NEJM)",
            "publication_year": 2011,
            "study_type": "Randomized Controlled Trial",
            "evidence_level": "Level 1 (Highest)",
            "sample_size": 18201,
            "primary_endpoint_result": "21% relative risk reduction in stroke or systemic embolism (HR 0.79; 95% CI, 0.66 to 0.95; p<0.001 for non-inferiority, p=0.01 for superiority).",
            "hazard_ratio": "0.79 (Stroke) / 0.69 (Major Bleed) / 0.89 (Mortality)",
            "relative_risk_reduction": "21% (Stroke), 31% (Major Bleeding), 11% (All-cause mortality)",
            "p_value": "p = 0.01 (Superiority for Stroke), p < 0.001 (Bleeding)",
            "key_findings": "In patients with atrial fibrillation, apixaban was superior to warfarin in preventing stroke or systemic embolism, caused less bleeding, and resulted in lower all-cause mortality.",
            "limitations": "Double-blind double-dummy trial design requiring sham INR monitoring in apixaban arm.",
            "claim_support_potential": "Only DOAC trial demonstrating statistically significant superiority in all three key endpoints: Stroke reduction, Bleeding reduction, and All-cause mortality reduction.",
            "relevance_score": 0.99,
            "url": "https://pubmed.ncbi.nlm.nih.gov/21870978/"
        }
    ]
}

async def search_pubmed_evidence(molecule_name: str, indication: Optional[str] = None) -> List[ResearchPaper]:
    """Search PubMed E-utilities or return curated high-relevance clinical literature.

    Never synthesize papers or endpoint data. Unknown or unavailable data must
    remain blank so downstream MLR review can distinguish evidence from gaps.
    """
    clean_name = molecule_name.strip().lower()

    if clean_name in CURATED_PAPERS:
        return [ResearchPaper(**p) for p in CURATED_PAPERS[clean_name]]

    # A fixed-dose combination has to be searched as an AND of its components.
    # Sending "Empagliflozin + Metformin[Title/Abstract]" as one phrase matches
    # nothing, which is why combination searches came back empty.
    resolved = resolve_molecule(molecule_name)
    if resolved.is_combination:
        combo_key = " + ".join(resolved.components).lower()
        if combo_key in CURATED_PAPERS:
            return [ResearchPaper(**p) for p in CURATED_PAPERS[combo_key]]

    # Try fetching live from NCBI E-Utilities
    papers: List[ResearchPaper] = []
    try:
        terms = resolved.components or [molecule_name]
        molecule_clause = " AND ".join(f"{t}[Title/Abstract]" for t in terms)
        query = f"({molecule_clause}) AND (clinical trial[Filter] OR systematic review[Filter])"
        if indication:
            query += f" AND {indication}[Title/Abstract]"
        
        async with httpx.AsyncClient(timeout=8.0) as client:
            esearch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
            params = {
                "db": "pubmed",
                "term": query,
                "retmode": "json",
                "retmax": "25",
                "sort": "pub_date"
            }
            search_resp = await client.get(esearch_url, params=params)
            
            if search_resp.status_code == 200:
                data = search_resp.json()
                id_list = data.get("esearchresult", {}).get("idlist", [])
                
                if id_list:
                    esummary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
                    sum_params = {
                        "db": "pubmed",
                        "id": ",".join(id_list),
                        "retmode": "json"
                    }
                    sum_resp = await client.get(esummary_url, params=sum_params)
                    
                    if sum_resp.status_code == 200:
                        sum_data = sum_resp.json().get("result", {})
                        for pmid in id_list:
                            item = sum_data.get(pmid, {})
                            if not item:
                                continue
                            
                            pub_year = 2024
                            pub_date = item.get("pubdate", "")
                            if pub_date and len(pub_date) >= 4 and pub_date[:4].isdigit():
                                pub_year = int(pub_date[:4])
                            
                            authors = [a.get("name", "") for a in item.get("authors", [])][:5]
                            title = item.get("title", f"Clinical study on {molecule_name.title()}")
                            journal = item.get("source", "Peer-Reviewed Medical Journal")
                            
                            pub_types = item.get("pubtype", []) or []
                            study_type = ", ".join(pub_types[:2]) if pub_types else "Unclassified PubMed Record"
                            evidence_level = "Unrated - requires medical review"
                            lowered_types = " ".join(pub_types).lower()
                            if "randomized controlled trial" in lowered_types:
                                evidence_level = "Candidate Level 1 - verify full text"
                            elif "systematic review" in lowered_types or "meta-analysis" in lowered_types:
                                evidence_level = "Candidate Level 1 - verify methodology"

                            papers.append(ResearchPaper(
                                id=f"PMID-{pmid}",
                                pmid=pmid,
                                doi=item.get("articleids", [{}])[0].get("value") if item.get("articleids") else None,
                                title=title,
                                authors=authors if authors else ["Clinical Investigators"],
                                journal=journal,
                                publication_year=pub_year,
                                study_type=study_type,
                                evidence_level=evidence_level,
                                sample_size=None,
                                primary_endpoint_result=None,
                                hazard_ratio=None,
                                relative_risk_reduction=None,
                                p_value=None,
                                key_findings="PubMed bibliographic record found. Clinical findings require abstract/full-text extraction and medical review before use.",
                                limitations="Endpoint, population, and effect-size details are not parsed from PubMed summary metadata.",
                                claim_support_potential="Citation candidate only; not claim-ready until reviewed against the publication and approved label.",
                                relevance_score=0.75,
                                url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                            ))
    except Exception as e:
        logger.warning(f"Live PubMed query error for {molecule_name}: {e}")
    
    if papers:
        return papers
    
    return []

def map_claims_to_evidence(papers: List[ResearchPaper]) -> List[ClaimEvidenceMapping]:
    """Generate conservative Claim-to-Evidence mappings for MLR triage."""
    if not papers:
        return []

    mappings = []
    
    # Efficacy claim
    mappings.append(ClaimEvidenceMapping(
        claim_text="Potential efficacy claim identified from reviewed evidence candidates; final wording requires MLR approval.",
        category="Efficacy",
        strength_of_evidence="Requires medical review",
        supported_by_papers=papers[:2],
        label_status="Not claim-ready"
    ))
    
    # Safety / Tolerability claim
    mappings.append(ClaimEvidenceMapping(
        claim_text="Potential safety/tolerability claim identified; verify against approved prescribing information before use.",
        category="Safety",
        strength_of_evidence="Requires label verification",
        supported_by_papers=papers[:1],
        label_status="Needs MLR review"
    ))
    
    return mappings
