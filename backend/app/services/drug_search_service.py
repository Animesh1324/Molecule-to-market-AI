"""Drug search across brand, generic, ingredient, class, strength, and form.

Search runs against the cached database first and only reaches for an upstream
when nothing matches — that is the caching contract in Step 13, and it is also
what keeps a search responsive.

Tolerances: case, surrounding whitespace, salt suffixes ("metformin
hydrochloride"), INN/USAN spelling ("paracetamol" vs "acetaminophen"), and
fixed-dose combinations, which are searched component-wise because no single
compound record exists for them.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Tuple

from ..models.drug import DrugSearchResult
from ..repositories import drug_repository as repo
from . import drug_ingestion_service as ingestion
from .inn_synonyms import base_moiety, candidates as name_candidates
from .molecule_resolver import resolve as resolve_molecule

logger = logging.getLogger(__name__)

# Class shorthand a brand manager types that never appears verbatim in a label.
CLASS_ALIASES: Dict[str, List[str]] = {
    "glp-1": ["glucagon-like peptide-1", "glp-1 receptor agonist", "incretin"],
    "glp1": ["glucagon-like peptide-1", "glp-1 receptor agonist"],
    "sglt2": ["sodium-glucose", "sglt2 inhibitor"],
    "dpp-4": ["dipeptidyl peptidase", "dpp-4 inhibitor"],
    "dpp4": ["dipeptidyl peptidase"],
    "ppi": ["proton pump inhibitor"],
    "arb": ["angiotensin receptor blocker", "angiotensin ii receptor"],
    "ace": ["angiotensin converting enzyme"],
    "ssri": ["serotonin reuptake inhibitor"],
    "nsaid": ["nonsteroidal anti-inflammatory"],
    "statin": ["hmg-coa reductase inhibitor"],
    "beta blocker": ["adrenergic beta-antagonist", "beta-adrenergic blocker"],
    "pd-1": ["programmed death receptor", "pd-1 blocking antibody"],
    "checkpoint inhibitor": ["programmed death", "ctla-4"],
}


def _normalise(term: str) -> str:
    return re.sub(r"\s+", " ", (term or "").strip().lower())


def expand_terms(term: str) -> List[str]:
    """Every spelling worth trying, most specific first."""
    normalised = _normalise(term)
    if not normalised:
        return []

    out: List[str] = [normalised]

    def add(value: str) -> None:
        value = _normalise(value)
        if value and value not in out:
            out.append(value)

    for alias in CLASS_ALIASES.get(normalised, []):
        add(alias)

    for alias in name_candidates(normalised):
        add(alias)
    add(base_moiety(normalised))

    # A combination has no single record; its components do.
    resolved = resolve_molecule(term)
    if resolved.is_combination:
        for component in resolved.components:
            add(component)
            for alias in name_candidates(component):
                add(alias)
    return out


def _matched_on(term: str, rows: List[Dict[str, Any]]) -> str:
    needle = _normalise(term)
    if not rows:
        return "no match"
    first = rows[0]
    if needle in _normalise(first.get("generic_name") or ""):
        return "generic name"
    if needle in _normalise(first.get("brand_name") or ""):
        return "brand name"
    if any(needle in _normalise(i) for i in first.get("active_ingredients") or []):
        return "active ingredient"
    for key in ("drug_class", "therapeutic_class"):
        if needle in _normalise(first.get(key) or ""):
            return "drug class"
    if any(needle in _normalise(s) for s in first.get("strengths") or []):
        return "strength"
    if any(needle in _normalise(f) for f in first.get("dosage_forms") or []):
        return "dosage form"
    return "related term"


async def search(
    term: str,
    page: int = 1,
    page_size: int = 25,
    ingest_if_missing: bool = True,
) -> DrugSearchResult:
    """Cache-first search, falling back to on-demand ingestion."""
    if not (term or "").strip():
        return DrugSearchResult(
            query="", note="Enter a brand name, generic name, ingredient, or drug class."
        )

    attempts = expand_terms(term)

    rows: List[Dict[str, Any]] = []
    total = 0
    for attempt in attempts:
        rows, total = repo.search_drugs(attempt, page=page, page_size=page_size)
        if rows:
            break

    ingested = False
    if not rows and ingest_if_missing:
        # Nothing cached: try the sources, then look again.
        ingested = await ingestion.ensure_ingested(term)
        for attempt in attempts:
            rows, total = repo.search_drugs(attempt, page=page, page_size=page_size)
            if rows:
                break

    if rows:
        note = f"{total} record(s) matched."
        if ingested:
            note += " Fetched from source on this request and cached."
    else:
        note = (
            f"No drug record matched '{term}'. The permitted sources returned nothing "
            "for this term — check the spelling, or add the record manually if it is "
            "an India-only product no public register carries."
        )

    return DrugSearchResult(
        items=rows,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
        query=term,
        matched_on=_matched_on(term, rows),
        ingested_on_demand=ingested,
        note=note,
    )
