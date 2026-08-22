"""PubMed literature retrieval for a molecule.

Completeness is the point. The evidence module is meant to answer "what has been
published on this molecule", so it pages the entire result set through NCBI's
history server and caches it, rather than showing the first 25 hits and calling
it the literature.

Three rules hold throughout:

* **Nothing is invented.** An unparseable publication date is stored as NULL,
  never defaulted to a year. A record without an abstract says so.
* **The true total is always reported**, separately from how many records were
  pulled down, so a partial fetch can never read as the whole literature.
* **Evidence tiers stay labelled "candidate".** PubMed's publication type is a
  cataloguing decision, not a methodological appraisal.
"""
import asyncio
import hashlib
import json
import logging
import os
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

from ..db.database import SessionLocal
from ..db.evidence_models import PubMedPaperORM, PubMedQueryORM
from ..models.evidence import ResearchPaper, ClaimEvidenceMapping
from .molecule_resolver import resolve as resolve_molecule

logger = logging.getLogger(__name__)

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



# ---------------------------------------------------------------------------
# Live PubMed retrieval
#
# The previous implementation asked for 25 records, kept only the first page,
# and returned curated papers *instead of* searching when a molecule happened to
# be curated — so Empagliflozin reported four papers when PubMed indexes
# thousands. It also defaulted an unparseable publication date to the year 2024,
# which put a fabricated year on a real citation.
#
# This version pages the whole result set through the E-utilities history
# server, stores it, and reports the true total separately from how much has
# been pulled down, so "complete" is a claim the UI can actually make.
# ---------------------------------------------------------------------------

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

# NCBI allows 3 requests/second anonymously and 10 with a key. Staying under the
# limit matters: exceeding it earns an IP block, which would take the evidence
# module down entirely rather than just slowing it.
_API_KEY = (os.getenv("NCBI_API_KEY") or "").strip()
_MIN_INTERVAL = 0.11 if _API_KEY else 0.34

# esummary tolerates large id batches; 200 keeps each response a sane size.
SUMMARY_BATCH = 200
ABSTRACT_BATCH = 100
# Ceiling on one fetch pass. Some molecules (aspirin, metformin) index six
# figures of papers; pulling all of them on a page load helps nobody. The true
# total is always reported, so the UI never implies this ceiling is everything.
DEFAULT_MAX_RECORDS = int(os.getenv("PUBMED_MAX_RECORDS", "2000"))
CACHE_TTL_HOURS = int(os.getenv("PUBMED_CACHE_TTL_HOURS", "168"))

_rate_lock = asyncio.Lock()
_last_call = 0.0


async def _throttled_get(client: httpx.AsyncClient, url: str, params: Dict[str, Any]):
    """Serialise NCBI calls to stay inside the published rate limit."""
    global _last_call
    if _API_KEY:
        params = {**params, "api_key": _API_KEY}
    params = {**params, "tool": "molecule-to-market-ai", "email": os.getenv("NCBI_EMAIL", "")}
    async with _rate_lock:
        delta = time.monotonic() - _last_call
        if delta < _MIN_INTERVAL:
            await asyncio.sleep(_MIN_INTERVAL - delta)
        _last_call = time.monotonic()
    return await client.get(url, params=params)


def _query_id(molecule: str, indication: Optional[str]) -> str:
    raw = f"{molecule.strip().lower()}|{(indication or '').strip().lower()}"
    return hashlib.sha1(raw.encode()).hexdigest()[:20]


def build_query(molecule: str, indication: Optional[str] = None,
                clinical_only: bool = False) -> str:
    """PubMed query for a molecule, searching each component of a combination.

    A fixed-dose combination has to be an AND of its components: sending
    "Empagliflozin + Metformin[Title/Abstract]" as one phrase matches nothing.
    """
    resolved = resolve_molecule(molecule)
    terms = resolved.components or [molecule]
    # Search the whole record, not just title/abstract — restricting to
    # Title/Abstract silently drops papers indexed under the MeSH term only.
    clauses = " AND ".join(f'("{t}"[Title/Abstract] OR "{t}"[MeSH Terms])' for t in terms)
    query = f"({clauses})"
    if indication:
        query += f' AND ("{indication}"[Title/Abstract] OR "{indication}"[MeSH Terms])'
    if clinical_only:
        query += " AND (clinical trial[Filter] OR systematic review[Filter] OR meta-analysis[Filter])"
    return query


def _classify(pub_types: List[str]) -> tuple:
    """Map PubMed publication types onto a study type and an evidence tier.

    Tiers are labelled "candidate" throughout: PubMed's publication type is a
    cataloguing decision, not a methodological appraisal, and calling a record
    Level 1 without reading it would be exactly the unsourced assertion this
    application is supposed to avoid.
    """
    lowered = " ".join(pub_types).lower()
    study_type = ", ".join(pub_types[:2]) if pub_types else "Journal Article"
    if "meta-analysis" in lowered:
        return study_type, "Candidate Level 1 — meta-analysis, verify methodology"
    if "systematic review" in lowered:
        return study_type, "Candidate Level 1 — systematic review, verify methodology"
    if "randomized controlled trial" in lowered:
        return study_type, "Candidate Level 1 — RCT, verify full text"
    if "clinical trial" in lowered:
        return study_type, "Candidate Level 2 — clinical trial, verify design"
    if "review" in lowered:
        return study_type, "Candidate Level 3 — narrative review"
    if "case reports" in lowered:
        return study_type, "Candidate Level 4 — case report"
    return study_type, "Unrated — requires medical review"


def _parse_year(pubdate: str) -> Optional[int]:
    """Year from a PubMed date string, or None. Never a default."""
    match = re.search(r"(1[89]\d{2}|20\d{2})", pubdate or "")
    return int(match.group(1)) if match else None


def _extract_ids(item: Dict[str, Any]) -> Dict[str, Optional[str]]:
    """Pull DOI and PMCID out of the articleids array by type, not position.

    The previous code took articleids[0], which is the PMID entry, and stored it
    in the doi field — so every record carried a DOI that was not a DOI.
    """
    ids = {"doi": None, "pmcid": None}
    for entry in item.get("articleids") or []:
        kind = (entry.get("idtype") or "").lower()
        value = entry.get("value")
        if kind == "doi" and value:
            ids["doi"] = str(value)
        elif kind == "pmc" and value:
            ids["pmcid"] = str(value)
    return ids


async def _esearch_history(client: httpx.AsyncClient, query: str) -> Dict[str, Any]:
    """Run the search, keeping results on NCBI's history server."""
    response = await _throttled_get(client, f"{EUTILS}/esearch.fcgi", {
        "db": "pubmed", "term": query, "retmode": "json",
        "usehistory": "y", "retmax": "0", "sort": "pub_date",
    })
    response.raise_for_status()
    result = response.json().get("esearchresult", {}) or {}
    return {
        "count": int(result.get("count") or 0),
        "webenv": result.get("webenv"),
        "query_key": result.get("querykey"),
    }


async def _fetch_summaries(client: httpx.AsyncClient, webenv: str, query_key: str,
                           total: int, max_records: int) -> List[Dict[str, Any]]:
    """Page esummary through the history server until the cap or the end."""
    wanted = min(total, max_records)
    records: List[Dict[str, Any]] = []
    for start in range(0, wanted, SUMMARY_BATCH):
        response = await _throttled_get(client, f"{EUTILS}/esummary.fcgi", {
            "db": "pubmed", "retmode": "json", "WebEnv": webenv,
            "query_key": query_key, "retstart": str(start),
            "retmax": str(min(SUMMARY_BATCH, wanted - start)),
        })
        if response.status_code != 200:
            logger.warning("esummary page at %d returned %s", start, response.status_code)
            break
        payload = response.json().get("result", {}) or {}
        for pmid in payload.get("uids", []) or []:
            item = payload.get(pmid)
            if item:
                records.append(item)
    return records


async def _fetch_abstracts(client: httpx.AsyncClient, pmids: List[str]) -> Dict[str, str]:
    """Abstract text per PMID.

    Turns "clinical findings require full-text extraction" into the actual
    abstract, which is what a reviewer needs to judge whether a paper supports a
    claim. Structured abstracts keep their section labels.
    """
    abstracts: Dict[str, str] = {}
    for start in range(0, len(pmids), ABSTRACT_BATCH):
        batch = pmids[start:start + ABSTRACT_BATCH]
        try:
            response = await _throttled_get(client, f"{EUTILS}/efetch.fcgi", {
                "db": "pubmed", "id": ",".join(batch),
                "retmode": "xml", "rettype": "abstract",
            })
            if response.status_code != 200:
                continue
            root = ET.fromstring(response.text)
            for article in root.iter("PubmedArticle"):
                pmid_node = article.find(".//MedlineCitation/PMID")
                if pmid_node is None or not pmid_node.text:
                    continue
                parts: List[str] = []
                for node in article.iter("AbstractText"):
                    label = node.get("Label")
                    text = "".join(node.itertext()).strip()
                    if not text:
                        continue
                    parts.append(f"{label}: {text}" if label else text)
                if parts:
                    abstracts[pmid_node.text.strip()] = "\n\n".join(parts)
        except ET.ParseError:
            logger.warning("Could not parse abstract XML for batch starting %d", start)
        except Exception:
            logger.exception("Abstract fetch failed for batch starting %d", start)
    return abstracts


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

def _paper_from_orm(row: PubMedPaperORM, molecule: str) -> ResearchPaper:
    authors = json.loads(row.authors_json or "[]")
    return ResearchPaper(
        id=f"PMID-{row.pmid}",
        pmid=row.pmid,
        pmcid=row.pmcid,
        doi=row.doi,
        title=row.title,
        authors=authors,
        journal=row.journal or "Journal not stated in PubMed record",
        # The model requires an int; 0 is the sentinel for "PubMed carried no
        # parseable date". It is never rendered as a year by the UI.
        publication_year=row.publication_year or 0,
        study_type=row.study_type or "Journal Article",
        evidence_level=row.evidence_level or "Unrated — requires medical review",
        sample_size=None,
        primary_endpoint_result=None,
        hazard_ratio=None,
        relative_risk_reduction=None,
        p_value=None,
        key_findings=(row.abstract or
                      "PubMed indexed this record without an abstract. Open the "
                      "publication to review its findings."),
        limitations=("Effect sizes, population, and endpoints are not machine-extracted "
                     "from PubMed metadata — read the publication before citing."),
        claim_support_potential=("Citation candidate. Not claim-ready until reviewed "
                                 "against the publication and the approved label."),
        relevance_score=0.75,
        url=f"https://pubmed.ncbi.nlm.nih.gov/{row.pmid}/",
    )


def _store(records: List[Dict[str, Any]], abstracts: Dict[str, str]) -> List[str]:
    """Upsert summary records, returning the PMIDs in the order given."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    session = SessionLocal()
    ordered: List[str] = []
    try:
        for item in records:
            pmid = str(item.get("uid") or "").strip()
            if not pmid:
                continue
            ordered.append(pmid)
            pub_types = [str(t) for t in (item.get("pubtype") or [])]
            study_type, evidence_level = _classify(pub_types)
            ids = _extract_ids(item)
            row = session.get(PubMedPaperORM, pmid)
            values = dict(
                pmcid=ids["pmcid"],
                doi=ids["doi"],
                title=(item.get("title") or "Title not stated in PubMed record").strip(),
                authors_json=json.dumps([a.get("name", "") for a in (item.get("authors") or [])
                                         if a.get("name")]),
                journal=item.get("source") or None,
                publication_year=_parse_year(item.get("pubdate") or ""),
                publication_date=item.get("pubdate") or None,
                pub_types_json=json.dumps(pub_types),
                study_type=study_type,
                evidence_level=evidence_level,
                fetched_at=now,
            )
            abstract = abstracts.get(pmid)
            if row is None:
                session.add(PubMedPaperORM(pmid=pmid, abstract=abstract, **values))
            else:
                for field, value in values.items():
                    setattr(row, field, value)
                # Never overwrite a stored abstract with nothing.
                if abstract:
                    row.abstract = abstract
        session.commit()
    except Exception:
        session.rollback()
        logger.exception("Storing PubMed records failed")
        raise
    finally:
        session.close()
    return ordered


def _load_cached(query_id: str, limit: Optional[int], offset: int,
                 molecule: str) -> Optional[Dict[str, Any]]:
    session = SessionLocal()
    try:
        query = session.get(PubMedQueryORM, query_id)
        if query is None:
            return None
        age_hours = 999.0
        try:
            fetched = datetime.strptime(query.fetched_at, "%Y-%m-%d %H:%M:%S")
            age_hours = (datetime.now() - fetched).total_seconds() / 3600.0
        except (ValueError, TypeError):
            pass
        pmids = json.loads(query.pmids_json or "[]")
        window = pmids[offset:offset + limit] if limit else pmids[offset:]
        rows = {r.pmid: r for r in session.query(PubMedPaperORM)
                .filter(PubMedPaperORM.pmid.in_(window)).all()} if window else {}
        papers = [_paper_from_orm(rows[p], molecule) for p in window if p in rows]
        return {
            "papers": papers,
            "total_available": query.total_available,
            "fetched_count": query.fetched_count,
            "complete": bool(query.complete),
            "stale": age_hours > CACHE_TTL_HOURS,
            "fetched_at": query.fetched_at,
            "status": query.status,
        }
    finally:
        session.close()


def _save_query(query_id: str, molecule: str, indication: Optional[str], query_string: str,
                total: int, pmids: List[str], complete: bool,
                status: str = "ready", message: Optional[str] = None) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    session = SessionLocal()
    try:
        row = session.get(PubMedQueryORM, query_id)
        values = dict(
            molecule=molecule, molecule_key=molecule.strip().lower(),
            indication=indication, query_string=query_string,
            total_available=total, fetched_count=len(pmids),
            pmids_json=json.dumps(pmids), complete=1 if complete else 0,
            status=status, message=message, fetched_at=now,
        )
        if row is None:
            session.add(PubMedQueryORM(id=query_id, **values))
        else:
            for field, value in values.items():
                setattr(row, field, value)
        session.commit()
    except Exception:
        session.rollback()
        logger.exception("Storing PubMed query state failed")
    finally:
        session.close()


def _mark_query_error(query_id: str, molecule: str, indication: Optional[str],
                      query_string: str, message: str) -> None:
    """Flag a failed fetch, preserving any corpus already stored."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    session = SessionLocal()
    try:
        row = session.get(PubMedQueryORM, query_id)
        if row is None:
            session.add(PubMedQueryORM(
                id=query_id, molecule=molecule, molecule_key=molecule.strip().lower(),
                indication=indication, query_string=query_string,
                total_available=0, fetched_count=0, pmids_json=json.dumps([]),
                complete=0, status="error", message=message, fetched_at=now,
            ))
        else:
            row.status = "error"
            row.message = message
            # fetched_at is deliberately not advanced: the cache is as old as
            # its last successful fetch, and a failure should not hide that.
        session.commit()
    except Exception:
        session.rollback()
        logger.exception("Recording PubMed error state failed")
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def fetch_pubmed_corpus(molecule: str, indication: Optional[str] = None,
                              max_records: int = DEFAULT_MAX_RECORDS,
                              with_abstracts: bool = True) -> Dict[str, Any]:
    """Fetch and cache the PubMed bibliography for a molecule.

    Returns the true total PubMed reports alongside how many were stored, so a
    partial fetch is always visible as partial rather than passed off as the
    whole literature.
    """
    query_id = _query_id(molecule, indication)
    query_string = build_query(molecule, indication)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            search = await _esearch_history(client, query_string)
            total = search["count"]
            if not total or not search["webenv"]:
                _save_query(query_id, molecule, indication, query_string, total, [], True)
                return {"total_available": total, "fetched_count": 0, "complete": True}

            records = await _fetch_summaries(client, search["webenv"], search["query_key"],
                                             total, max_records)
            pmids = [str(r.get("uid")) for r in records if r.get("uid")]
            abstracts = await _fetch_abstracts(client, pmids) if (with_abstracts and pmids) else {}

        ordered = _store(records, abstracts)
        complete = len(ordered) >= total
        _save_query(query_id, molecule, indication, query_string, total, ordered, complete)
        logger.info("PubMed %s: %d of %d records cached", molecule, len(ordered), total)
        return {"total_available": total, "fetched_count": len(ordered), "complete": complete}
    except Exception as exc:
        logger.exception("PubMed corpus fetch failed for %s", molecule)
        # Record the failure WITHOUT clearing what is already cached. A transient
        # NCBI outage must not empty a module that was working a minute ago —
        # writing zeros here destroyed the corpus on every failed refresh.
        _mark_query_error(query_id, molecule, indication, query_string, str(exc)[:400])
        raise


async def get_evidence_page(molecule: str, indication: Optional[str] = None,
                            limit: int = 100, offset: int = 0,
                            refresh: bool = False) -> Dict[str, Any]:
    """One page of the molecule's literature, fetching it first if needed."""
    query_id = _query_id(molecule, indication)
    cached = None if refresh else _load_cached(query_id, limit, offset, molecule)

    if cached is None or cached["stale"] or (refresh and offset == 0):
        try:
            await fetch_pubmed_corpus(molecule, indication)
            cached = _load_cached(query_id, limit, offset, molecule)
        except Exception:
            # A live failure must not empty a module that already has data.
            if cached is None:
                cached = _load_cached(query_id, limit, offset, molecule)

    curated = _curated_for(molecule)
    if cached is None:
        return {
            "molecule": molecule.title(), "papers": curated,
            "total_available": len(curated), "fetched_count": len(curated),
            "returned": len(curated), "offset": offset, "limit": limit,
            "complete": True, "source": "curated" if curated else "none",
            "fetched_at": None,
        }

    papers = cached["papers"]
    if offset == 0 and curated:
        # Curated papers carry hand-checked endpoints and effect sizes that
        # PubMed metadata does not, so they lead — de-duplicated by PMID.
        seen = {p.pmid for p in curated if p.pmid}
        papers = curated + [p for p in papers if p.pmid not in seen]

    return {
        "molecule": molecule.title(),
        "papers": papers,
        "total_available": max(cached["total_available"], len(curated)),
        "fetched_count": cached["fetched_count"],
        "returned": len(papers),
        "offset": offset,
        "limit": limit,
        "complete": cached["complete"],
        "source": "pubmed",
        "fetched_at": cached["fetched_at"],
        "query": build_query(molecule, indication),
    }


def _curated_for(molecule: str) -> List[ResearchPaper]:
    """Hand-checked papers for this molecule, if any exist."""
    clean = molecule.strip().lower()
    if clean in CURATED_PAPERS:
        return [ResearchPaper(**p) for p in CURATED_PAPERS[clean]]
    resolved = resolve_molecule(molecule)
    if resolved.is_combination:
        combo = " + ".join(resolved.components).lower()
        if combo in CURATED_PAPERS:
            return [ResearchPaper(**p) for p in CURATED_PAPERS[combo]]
    return []


async def search_pubmed_evidence(molecule_name: str, indication: Optional[str] = None,
                                 limit: int = 100) -> List[ResearchPaper]:
    """Backwards-compatible entry point: the first page of the literature.

    Curated papers no longer *replace* the PubMed search — they lead it. A
    curated molecule previously returned four papers and never queried PubMed
    at all, which is why the evidence module looked thin for exactly the
    molecules the app knows best.
    """
    page = await get_evidence_page(molecule_name, indication, limit=limit, offset=0)
    return page["papers"]


def map_claims_to_evidence(papers: List[ResearchPaper]) -> List[ClaimEvidenceMapping]:
    """Conservative claim-to-evidence mappings for MLR triage."""
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
