"""Real-world patient experience from FDA FAERS and the approved label.

The brand-planning need here is "what do patients actually complain about, and
what makes them stop taking it". Consumer review sites look like the obvious
source, but their content is copyrighted, self-selected, and unusable in an
MLR-reviewed document.

FAERS is the FDA's own adverse event reporting system: structured, free,
citable, and it covers combinations. It is spontaneous-report data, so counts
show what gets *reported*, never incidence — the caveat travels with the data
so nobody reads a report count as a rate.
"""
import asyncio
import logging
from typing import Any, Dict, List, Optional

import httpx

from ..models.patient_experience import (
    DemographicSplit,
    PatientExperience,
    ReportedProblem,
)
from .inn_synonyms import candidates as name_candidates
from .molecule_resolver import resolve as resolve_molecule

logger = logging.getLogger(__name__)

FAERS_URL = "https://api.fda.gov/drug/event.json"
LABEL_URL = "https://api.fda.gov/drug/label.json"

# Reactions that usually mean a patient stopped or could not continue therapy.
DISCONTINUATION_TERMS = {
    "DRUG INEFFECTIVE", "THERAPY CESSATION", "DRUG WITHDRAWAL SYNDROME",
    "TREATMENT NONCOMPLIANCE", "PRODUCT DOSE OMISSION", "INTENTIONAL DOSE OMISSION",
    "DRUG INTOLERANCE", "POOR QUALITY DRUG ADMINISTERED", "OFF LABEL USE",
    "PRODUCT USE ISSUE", "INAPPROPRIATE SCHEDULE OF PRODUCT ADMINISTRATION",
    "MEDICATION ERROR", "DRUG HYPERSENSITIVITY", "NON-COMPLIANCE",
}

AGE_GROUPS = {
    "1": "Neonate", "2": "Infant", "3": "Child",
    "4": "Adolescent", "5": "Adult", "6": "Elderly",
}
SEX_GROUPS = {"1": "Male", "2": "Female"}


def _search_clause(components: List[str]) -> str:
    """FAERS search across every spelling, AND-ed for a combination."""
    # Spaces, not "+": httpx percent-encodes a literal "+" as %2B, which
    # openFDA reads as a character rather than a boolean, silently widening the
    # search to millions of unrelated reports.
    clauses = []
    for component in components:
        aliases = name_candidates(component)[:3]
        alias_clause = " OR ".join(
            f'patient.drug.openfda.generic_name:"{a}"' for a in aliases
        )
        clauses.append(f"({alias_clause})")
    return " AND ".join(clauses)


async def _faers_count(client: httpx.AsyncClient, search: str, field: str, limit: int = 25) -> List[Dict[str, Any]]:
    try:
        response = await client.get(
            FAERS_URL, params={"search": search, "count": field, "limit": str(limit)}
        )
        if response.status_code == 404:
            return []          # openFDA returns 404 for "no matching records"
        if response.status_code != 200:
            logger.warning("FAERS %s returned HTTP %s", field, response.status_code)
            return []
        return response.json().get("results", [])
    except Exception as exc:
        logger.warning("FAERS query failed (%s): %s", field, exc)
        return []


async def _label_patient_sections(client: httpx.AsyncClient, component: str) -> List[str]:
    """Patient counselling text from the approved label."""
    try:
        response = await client.get(
            LABEL_URL,
            params={"search": f'openfda.generic_name:"{component}"', "limit": "1"},
        )
        if response.status_code != 200:
            return []
        results = response.json().get("results", [])
        if not results:
            return []
        record = results[0]
        out: List[str] = []
        for key in ("information_for_patients", "patient_medication_information"):
            for entry in record.get(key, []) or []:
                text = " ".join(str(entry).split())
                if text:
                    out.append(text[:900])
        return out[:4]
    except Exception as exc:
        logger.warning("Label patient-section fetch failed for %s: %s", component, exc)
        return []


async def build_patient_experience(molecule: str) -> PatientExperience:
    resolved = resolve_molecule(molecule)
    if not resolved.components:
        return PatientExperience(
            query=molecule, display_name=molecule,
            coverage_note="No molecule name supplied.",
        )

    search = _search_clause(resolved.components)

    async with httpx.AsyncClient(timeout=25.0) as client:
        reactions, seriousness, ages, sexes, label_sections = await asyncio.gather(
            _faers_count(client, search, "patient.reaction.reactionmeddrapt.exact", 30),
            _faers_count(client, search, "serious"),
            _faers_count(client, search, "patient.patientagegroup"),
            _faers_count(client, search, "patient.patientsex"),
            _label_patient_sections(client, resolved.primary),
        )

    total = sum(int(r.get("count", 0)) for r in reactions) or 0
    serious = next((int(r["count"]) for r in seriousness if str(r.get("term")) == "1"), 0)
    non_serious = next((int(r["count"]) for r in seriousness if str(r.get("term")) == "2"), 0)
    denominator = (serious + non_serious) or total or 1

    problems = [
        ReportedProblem(
            term=str(r.get("term", "")).title(),
            report_count=int(r.get("count", 0)),
            share_of_reports=round(int(r.get("count", 0)) / denominator * 100, 2),
        )
        for r in reactions
    ]

    discontinuation = [
        p for p in problems if p.term.upper() in DISCONTINUATION_TERMS
    ]
    off_label = next(
        (p.report_count for p in problems if p.term.upper() == "OFF LABEL USE"), 0
    )

    age_dist = [
        DemographicSplit(label=AGE_GROUPS.get(str(r.get("term")), f"Code {r.get('term')}"),
                         count=int(r.get("count", 0)))
        for r in ages
    ]
    sex_dist = [
        DemographicSplit(label=SEX_GROUPS.get(str(r.get("term")), "Unspecified"),
                         count=int(r.get("count", 0)))
        for r in sexes
    ]

    adherence: List[str] = []
    if discontinuation:
        adherence.append(
            "Reports flagging non-compliance, dose omission, or intolerance: "
            + ", ".join(f"{p.term} ({p.report_count:,})" for p in discontinuation[:5])
            + ". Treat these as adherence themes to probe in market research, not as rates."
        )
    if off_label:
        adherence.append(
            f"{off_label:,} reports coded 'Off Label Use'. Worth understanding which "
            "off-label patterns exist before building the promotional plan, since "
            "promotion must stay within the approved indication."
        )
    gi = [p for p in problems if p.term.upper() in {"NAUSEA", "DIARRHOEA", "VOMITING", "ABDOMINAL PAIN"}]
    if gi:
        adherence.append(
            "Gastrointestinal reactions are prominent in reporting ("
            + ", ".join(p.term for p in gi[:4])
            + "), which typically drives early discontinuation. Counselling and "
            "titration messaging are usually the lever."
        )

    if total:
        note = (
            f"{denominator:,} FAERS reports involving {resolved.display_name}. "
            f"{serious:,} coded serious, {non_serious:,} non-serious."
        )
        if resolved.is_combination:
            note += " Combination searched as an AND across both components."
    else:
        note = (
            f"No FAERS reports matched {resolved.display_name}. Expected for molecules "
            "not marketed in the US, or very recently launched."
        )

    return PatientExperience(
        query=molecule,
        display_name=resolved.display_name,
        components=resolved.components,
        is_combination=resolved.is_combination,
        total_reports=denominator,
        serious_reports=serious,
        non_serious_reports=non_serious,
        top_reported_problems=problems[:20],
        discontinuation_signals=discontinuation,
        off_label_use_reports=off_label,
        age_distribution=age_dist,
        sex_distribution=sex_dist,
        patient_counselling_from_label=label_sections,
        adherence_considerations=adherence,
        data_sources=[
            "FDA Adverse Event Reporting System (FAERS) via openFDA",
            "FDA Structured Product Labeling — patient counselling sections",
        ],
        coverage_note=note,
        interpretation_caveat=(
            "FAERS is spontaneous reporting. Counts reflect what was reported, not "
            "incidence, and carry no denominator of treated patients. A report does "
            "not establish that the drug caused the event. Never present these "
            "numbers as rates or as comparative safety."
        ),
    )
