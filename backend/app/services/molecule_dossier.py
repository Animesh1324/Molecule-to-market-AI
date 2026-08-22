"""Everything the application knows about one molecule, in a single call.

The data existed but was scattered: identity and label text in `drugs`,
approval history in `fda_submissions`, exclusivity in `orange_book_*`, recalls
and shortages in their own tables, literature in `pubmed_papers`. Answering
"tell me about this molecule" meant five round-trips and, for recalls and
shortages, no route at all.

Two rules this module holds to:

* **Every fact carries a link.** A brand plan claim has to be checkable, so
  each section names its source and a URL a reviewer can open. Papers get a
  resolved URL here rather than relying on the frontend to build one from a
  PMID, so the link exists in the payload itself.
* **Absent stays absent.** A section with no data returns an empty list and a
  populated `false`, never a zero or a placeholder that reads as a finding.
  Pembrolizumab genuinely has no Orange Book patents — it is a biologic — and
  that must not look like "no patents found, therefore off-patent".
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import func, or_, text

from ..db.database import SessionLocal
from ..db.drug_models import DrugORM
from ..db.fda_catalog_models import (
    DrugRecallORM,
    DrugShortageORM,
    FDAApplicationORM,
    FDASubmissionORM,
)
from ..db.orange_book_models import (
    OrangeBookExclusivityORM,
    OrangeBookPatentORM,
    OrangeBookProductORM,
)

logger = logging.getLogger(__name__)

PUBMED_URL = "https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
DOI_URL = "https://doi.org/{doi}"
PMC_URL = "https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/"
LABEL_URL = "https://labels.fda.gov/"
ORANGE_BOOK_URL = "https://www.accessdata.fda.gov/scripts/cder/ob/search_product.cfm"
RECALL_URL = "https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts"
SHORTAGE_URL = "https://www.accessdata.fda.gov/scripts/drugshortages/"


def _loads(raw: Optional[str]) -> List[str]:
    try:
        parsed = json.loads(raw or "[]")
        return [str(v) for v in parsed] if isinstance(parsed, list) else []
    except (ValueError, TypeError):
        return []


def paper_url(pmid: Optional[str], doi: Optional[str], pmcid: Optional[str]) -> Optional[str]:
    """Best resolvable link for a paper, most authoritative first.

    PMID before DOI: a PubMed record always resolves, whereas a DOI can point
    at a paywall or, for older records, not resolve at all.
    """
    if pmid:
        return PUBMED_URL.format(pmid=pmid)
    if doi:
        return DOI_URL.format(doi=doi)
    if pmcid:
        return PMC_URL.format(pmcid=pmcid)
    return None


def _is_combination(ingredient: Optional[str]) -> bool:
    """Whether a product name lists more than one active ingredient.

    FDA uses three separators inconsistently across datasets: the Orange Book
    writes "EMPAGLIFLOZIN; METFORMIN HYDROCHLORIDE", the NDC directory writes
    "Dolutegravir And Lamivudine", and SPL writes "Abacavir Sulfate,
    Dolutegravir Sodium, Lamivudine". Checking only the first two marked
    Triumeq as single-ingredient and would have presented a three-drug HIV
    regimen's label as dolutegravir's own.
    """
    text_value = (ingredient or "").lower()
    return ";" in text_value or " and " in text_value or "," in text_value


def _name_rank(candidate: Optional[str], molecule: str) -> int:
    """0 exact, 1 leading component, 2 anywhere. Lower is more specific."""
    value = (candidate or "").strip().lower()
    target = molecule.strip().lower()
    if value == target:
        return 0
    if value.startswith(target):
        return 1
    return 2


def _identity(session, needle: str, molecule: str) -> Dict[str, Any]:
    rows = (
        session.query(DrugORM)
        .filter(or_(DrugORM.generic_name.ilike(needle), DrugORM.search_blob.like(needle.lower())))
        .limit(400)
        .all()
    )
    if not rows:
        return {"found": False, "products": 0}

    # Substring matching also catches co-formulated products, and picking the
    # richest row across all of them misattributes: searching "empagliflozin"
    # returned an empagliflozin+metformin combination and reported the class as
    # Biguanide. Rank by name specificity FIRST, so the clinical
    # representative is a single-ingredient product wherever one exists.
    mono = [r for r in rows if not _is_combination(r.generic_name)]
    pool = mono or rows
    best = sorted(pool, key=lambda r: (
        _name_rank(r.generic_name, molecule),
        r.indications is None,
        r.drug_class is None,
    ))[0]
    combinations = sorted({r.generic_name for r in rows if _is_combination(r.generic_name)})

    # Some molecules carry no label on any single-ingredient listing — every
    # marketed product is a co-formulation. Dolutegravir is one: its mono rows
    # are bare NDC entries and only Triumeq has the narrative. Preferring mono
    # is right for identity, but returning nothing clinical helps no one, so
    # fall back to the richest row and say plainly where the text came from.
    clinical_row = best
    clinical_from_combination = False
    if best.indications is None:
        richer = sorted(rows, key=lambda r: (r.indications is None, r.drug_class is None))[0]
        if richer.indications is not None:
            clinical_row = richer
            clinical_from_combination = _is_combination(richer.generic_name)

    brands = sorted({r.brand_name for r in rows if r.brand_name})
    forms, routes = set(), set()
    for r in rows:
        forms.update(_loads(r.dosage_forms))
        routes.update(_loads(r.routes))
    return {
        "found": True,
        "generic_name": best.generic_name,
        "drug_class": best.drug_class,
        "therapeutic_class": best.therapeutic_class,
        "products": len(rows),
        "single_ingredient_products": len(mono),
        # Reported separately, never folded into the molecule's own facts.
        "combination_products": combinations[:20],
        "brands": brands[:40],
        "dosage_forms": sorted(forms)[:20],
        "routes": sorted(routes)[:20],
        "manufacturers": sorted({r.manufacturer for r in rows if r.manufacturer})[:30],
        "clinical": {
            "indications": clinical_row.indications,
            "dosage": clinical_row.dosage,
            "contraindications": clinical_row.contraindications,
            "warnings": clinical_row.warnings,
            "adverse_effects": clinical_row.adverse_effects,
            "drug_interactions": clinical_row.drug_interactions,
            "mechanism": clinical_row.mechanism,
            # Names the product the narrative came from. When that is a
            # co-formulation the text describes the combination, not this
            # molecule alone, and must not be quoted as if it did.
            "from_product": clinical_row.brand_name or clinical_row.generic_name,
            "from_combination_product": clinical_from_combination,
        },
        "source": {"name": "openFDA SPL label + NDC directory", "url": LABEL_URL},
    }


def _approvals(session, needle: str) -> Dict[str, Any]:
    apps = (
        session.query(FDAApplicationORM)
        .filter(FDAApplicationORM.generic_names.ilike(needle))
        .limit(400)
        .all()
    )
    if not apps:
        return {"found": False, "applications": 0, "source": {"name": "openFDA drugsfda", "url": LABEL_URL}}

    numbers = [a.application_number for a in apps]
    originals = (
        session.query(FDASubmissionORM)
        .filter(FDASubmissionORM.application_number.in_(numbers[:300]),
                FDASubmissionORM.submission_type == "ORIG",
                FDASubmissionORM.submission_status == "AP")
        .all()
    )
    dates = sorted(s.submission_status_date for s in originals if s.submission_status_date)
    return {
        "found": True,
        "applications": len(apps),
        "anda_count": sum(1 for n in numbers if n.upper().startswith("ANDA")),
        "first_approval": dates[0] if dates else None,
        "innovator": next((a.sponsor_name for a in apps
                           if a.application_number.upper().startswith("NDA")), None),
        "sponsors": sorted({a.sponsor_name for a in apps if a.sponsor_name})[:25],
        "source": {"name": "openFDA drugsfda", "url": LABEL_URL},
    }


def _exclusivity(session, needle: str, molecule: str) -> Dict[str, Any]:
    all_products = (
        session.query(OrangeBookProductORM)
        .filter(OrangeBookProductORM.ingredient.ilike(needle))
        .limit(600)
        .all()
    )
    # Same trap as identity: a combination product's patents are not the
    # molecule's patents. Counting both together reported 47 patents for
    # empagliflozin where the single-ingredient product has 27.
    products = [p for p in all_products if not _is_combination(p.ingredient)]
    combination_products = [p for p in all_products if _is_combination(p.ingredient)]
    if not products:
        # Biologics are in the Purple Book, so absence here is meaningful and
        # must not read as "no patents, therefore generic entry is open".
        return {
            "found": False,
            "note": "Not listed in the Orange Book. Biologics are listed in the "
                    "Purple Book instead; absence here is not evidence of expiry.",
            "source": {"name": "FDA Orange Book", "url": ORANGE_BOOK_URL},
        }

    appl_nos = list({p.appl_no for p in products})[:300]
    patents = (session.query(OrangeBookPatentORM)
               .filter(OrangeBookPatentORM.appl_no.in_(appl_nos)).all())
    excl = (session.query(OrangeBookExclusivityORM)
            .filter(OrangeBookExclusivityORM.appl_no.in_(appl_nos)).all())
    expiries = sorted(p.patent_expire_date_iso for p in patents if p.patent_expire_date_iso)
    return {
        "found": True,
        # DISTINCT: FDA lists one patent per covered indication, so a plain
        # count would report patent-indication pairs, not patents.
        "patents": len({p.patent_no for p in patents if p.patent_no}),
        "patent_listings": len(patents),
        "use_codes": len({p.patent_use_code for p in patents if p.patent_use_code}),
        "earliest_patent_expiry": expiries[0] if expiries else None,
        "latest_patent_expiry": expiries[-1] if expiries else None,
        "exclusivity_codes": sorted({e.exclusivity_code for e in excl if e.exclusivity_code}),
        "latest_exclusivity_expiry": max(
            (e.exclusivity_date_iso for e in excl if e.exclusivity_date_iso), default=None),
        "ab_rated_products": sum(1 for p in products if (p.te_code or "").upper().startswith("AB")),
        "reference_listed_drugs": sorted({p.trade_name for p in products
                                          if (p.rld or "").lower() == "yes" and p.trade_name})[:15],
        "combination_products": len(combination_products),
        "source": {"name": "FDA Orange Book", "url": ORANGE_BOOK_URL},
    }


def _safety_signals(session, needle: str) -> Dict[str, Any]:
    recalls = (session.query(DrugRecallORM)
               .filter(DrugRecallORM.search_blob.like(needle.lower()))
               .order_by(DrugRecallORM.recall_initiation_date.desc()).limit(200).all())
    shortages = (session.query(DrugShortageORM)
                 .filter(DrugShortageORM.generic_name.ilike(needle)).limit(100).all())
    by_class: Dict[str, int] = {}
    for r in recalls:
        if r.classification:
            by_class[r.classification] = by_class.get(r.classification, 0) + 1
    current = [s for s in shortages if (s.status or "").lower().startswith("current")]
    return {
        "recalls": {
            "total": len(recalls),
            "by_classification": by_class,
            "most_recent": [
                {"recall_number": r.recall_number, "date": r.recall_initiation_date,
                 "classification": r.classification, "firm": r.recalling_firm,
                 "reason": r.reason_for_recall}
                for r in recalls[:5]
            ],
            "source": {"name": "openFDA enforcement reports", "url": RECALL_URL},
        },
        "shortages": {
            "current": len(current),
            "total_recorded": len(shortages),
            "entries": [
                {"company": s.company_name, "status": s.status, "reason": s.shortage_reason,
                 "presentation": s.presentation, "therapeutic_category": s.therapeutic_category}
                for s in current[:5]
            ],
            "source": {"name": "FDA drug shortages", "url": SHORTAGE_URL},
        },
    }


def _literature(session, molecule: str, limit: int) -> Dict[str, Any]:
    """Cached PubMed records, each with a resolved link.

    Reads the cache written by `pubmed_service`; this does not fetch. A URL is
    attached here so the payload carries it, rather than leaving the frontend
    to reconstruct one from a PMID.
    """
    try:
        rows = session.execute(text(
            "SELECT pmid, pmcid, doi, title, journal, publication_year, study_type, "
            "evidence_level, abstract FROM pubmed_papers "
            "WHERE LOWER(title) LIKE :q OR LOWER(COALESCE(abstract,'')) LIKE :q "
            "ORDER BY publication_year DESC LIMIT :n"
        ), {"q": f"%{molecule.lower()}%", "n": limit}).mappings().all()
    except Exception:  # noqa: BLE001 - cache table may not exist yet
        logger.debug("pubmed cache unavailable", exc_info=True)
        return {"papers": [], "count": 0, "cached_only": True}

    papers = []
    for r in rows:
        url = paper_url(r["pmid"], r["doi"], r["pmcid"])
        papers.append({
            "pmid": r["pmid"], "doi": r["doi"], "title": r["title"],
            "journal": r["journal"], "year": r["publication_year"],
            "study_type": r["study_type"], "evidence_level": r["evidence_level"],
            "url": url,
        })
    return {
        "papers": papers,
        "count": len(papers),
        # True because this reads the local cache only. A caller wanting the
        # complete corpus must run pubmed_service's fetch first; saying so
        # keeps "we have 12 papers" from being mistaken for "12 papers exist".
        "cached_only": True,
        "source": {"name": "PubMed", "url": "https://pubmed.ncbi.nlm.nih.gov/"},
    }


def build_dossier(molecule: str, *, paper_limit: int = 25) -> Dict[str, Any]:
    """Every stored fact about `molecule`, each section carrying its source."""
    name = (molecule or "").strip()
    if not name:
        raise ValueError("molecule is required")
    needle = f"%{name}%"

    session = SessionLocal()
    try:
        identity = _identity(session, needle, name)
        dossier = {
            "molecule": name,
            "identity": identity,
            "approvals": _approvals(session, needle),
            "exclusivity": _exclusivity(session, needle, name),
            "safety_signals": _safety_signals(session, needle),
            "literature": _literature(session, name, paper_limit),
        }
        dossier["sections_populated"] = sorted(
            k for k in ("identity", "approvals", "exclusivity")
            if dossier[k].get("found")
        )
        return dossier
    finally:
        session.close()
