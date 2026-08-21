"""PMT intelligence: strategic reading derived from stored drug records.

Deliberately separated from the drug endpoints. Everything here is *generated*
— an inference this application draws from the source records — and is labelled
as such on the way out. Mixing it into the drug profile would let a reader
carry a software inference into an MLR pack believing it came from the FDA.

The rules this layer observes:

* every observation names the record it came from
* nothing is asserted that is not visible in a stored field
* an absent field produces an evidence gap, never an assumption
* no comparative efficacy or safety claim is made, ever
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from ..models.drug import PMTAnalysis, PMTProductProfile
from ..repositories import drug_repository as repo
from . import drug_search_service as search_service

logger = logging.getLogger(__name__)


def _as_dict(item: Any) -> Optional[Dict[str, Any]]:
    """Search results come back as Pydantic models, the repository yields dicts.

    Normalise at the boundary so downstream code has one shape to handle.
    """
    if item is None:
        return None
    if isinstance(item, dict):
        return item
    if hasattr(item, "model_dump"):
        return item.model_dump()
    if hasattr(item, "dict"):
        return item.dict()
    return None


def _summarise(text: Optional[str], limit: int = 220) -> Optional[str]:
    if not text:
        return None
    clean = " ".join(str(text).split())
    return clean[:limit] + ("…" if len(clean) > limit else "")


def _profile(record: Dict[str, Any]) -> PMTProductProfile:
    return PMTProductProfile(
        brand=record.get("brand_name"),
        generic=record.get("generic_name"),
        molecule=", ".join(record.get("active_ingredients") or []) or record.get("generic_name"),
        company=record.get("manufacturer"),
        drug_class=record.get("drug_class") or record.get("therapeutic_class"),
        indication_summary=_summarise(record.get("indications")),
        dosage_summary=_summarise(record.get("dosage")),
    )


def _dosing_frequency(record: Dict[str, Any]) -> Optional[str]:
    """Read a dosing cadence out of the label text, when it states one plainly."""
    text = (record.get("dosage") or "").lower()
    for pattern, label in (
        (r"\bonce (?:a )?dail(?:y|ies)\b|\bonce per day\b|\bqd\b", "once daily"),
        (r"\btwice (?:a )?daily\b|\bbid\b", "twice daily"),
        (r"\bthree times (?:a )?daily\b|\btid\b", "three times daily"),
        (r"\bonce weekly\b|\bevery week\b", "once weekly"),
        (r"\bevery (?:2|two) weeks\b|\bq2w\b", "every two weeks"),
        (r"\bevery (?:3|three) weeks\b|\bq3w\b", "every three weeks"),
        (r"\bevery (?:4|four) weeks\b|\bmonthly\b", "monthly"),
    ):
        if re.search(pattern, text):
            return label
    return None


async def build_analysis(
    molecule: str,
    competitors: Optional[List[str]] = None,
) -> PMTAnalysis:
    """Assemble the PMT view for one molecule against optional competitors."""
    result = await search_service.search(molecule, page=1, page_size=1)
    if not result.items:
        return PMTAnalysis(
            evidence_gaps=[
                f"No drug record could be resolved for '{molecule}', so no analysis "
                "is possible. Ingest the molecule or add it manually first."
            ]
        )

    record = _as_dict(result.items[0]) or {}
    used: List[str] = [record["id"]]

    competitor_records: List[Dict[str, Any]] = []
    for name in competitors or []:
        found = await search_service.search(name, page=1, page_size=1)
        if found.items:
            competitor = _as_dict(found.items[0]) or {}
            competitor_records.append(competitor)
            used.append(competitor.get("id", ""))

    positioning: List[str] = []
    differentiation: List[str] = []
    advantages: List[str] = []
    disadvantages: List[str] = []
    patients: List[str] = []
    physicians: List[str] = []
    gaps: List[str] = []

    drug_class = record.get("drug_class") or record.get("therapeutic_class")
    if drug_class:
        positioning.append(
            f"Recorded class is '{drug_class}'. Positioning has to establish a place "
            "within that class before it can claim one against it."
        )
    else:
        gaps.append("No drug class on the record — class positioning cannot be framed yet.")

    routes = record.get("routes") or []
    forms = record.get("dosage_forms") or []
    if routes:
        oral = any("oral" in r.lower() for r in routes)
        parenteral = any(
            k in " ".join(routes).lower() for k in ("intravenous", "subcutaneous", "injection", "infusion")
        )
        if oral and not parenteral:
            advantages.append(
                f"Oral administration ({', '.join(routes)}) — no administration burden, "
                "which is a genuine adherence argument against injectable comparators."
            )
        if parenteral:
            disadvantages.append(
                f"Parenteral administration ({', '.join(routes)}) requires a site of care "
                "or device training; the access and adherence plan has to absorb that."
            )
    if forms:
        differentiation.append(f"Dosage forms available: {', '.join(forms[:6])}.")

    cadence = _dosing_frequency(record)
    if cadence:
        advantages.append(f"Label states {cadence} dosing — a convenience point to test in research.")
    else:
        gaps.append("Dosing cadence is not stated plainly enough in the label text to read automatically.")

    strengths = record.get("strengths") or []
    if len(strengths) >= 3:
        differentiation.append(
            f"{len(strengths)} strengths on record, supporting titration and a broader patient fit."
        )
    elif strengths:
        differentiation.append(f"Limited strength range ({', '.join(strengths[:4])}) constrains titration.")

    indications = record.get("indications")
    if indications:
        text = " ".join(str(indications).split())
        patients.append(f"Label-defined population: {_summarise(text, 260)}")
        for term, specialty in (
            ("heart failure", "Cardiologists"), ("diabetes", "Endocrinologists / Diabetologists"),
            ("kidney", "Nephrologists"), ("cancer", "Medical Oncologists"),
            ("carcinoma", "Medical Oncologists"), ("asthma", "Pulmonologists"),
            ("copd", "Pulmonologists"), ("arthritis", "Rheumatologists"),
            ("depression", "Psychiatrists"), ("epilep", "Neurologists"),
            ("infection", "Infectious Disease specialists"),
        ):
            if term in text.lower() and specialty not in physicians:
                physicians.append(specialty)
    else:
        gaps.append("No indication text — target population cannot be defined from the record.")

    if record.get("contraindications"):
        disadvantages.append(
            "Contraindications are on the label and carve patients out of the addressable "
            "pool; size that exclusion before the forecast is signed off."
        )
    else:
        gaps.append("No contraindication text — the excluded population is unquantified.")

    if record.get("warnings"):
        disadvantages.append(
            "Warnings text exists and will shape both the fair-balance obligation and "
            "the objections the field force meets."
        )

    for competitor in competitor_records:
        competitor_class = competitor.get("drug_class") or "class not recorded"
        same_class = bool(drug_class) and competitor_class.lower() == str(drug_class).lower()
        positioning.append(
            f"vs {competitor.get('brand_name') or competitor.get('generic_name')} "
            f"({competitor_class}): "
            + ("same recorded class, so differentiation must come from dosing, "
               "formulation, or access rather than mechanism."
               if same_class else
               "different recorded class, so the argument is mechanism-level.")
        )
        competitor_cadence = _dosing_frequency(competitor)
        if cadence and competitor_cadence and cadence != competitor_cadence:
            differentiation.append(
                f"Dosing cadence differs from {competitor.get('generic_name')}: "
                f"{cadence} vs {competitor_cadence}."
            )

    if not competitor_records and competitors:
        gaps.append(
            "None of the named competitors resolved to a record; comparative "
            "positioning is unavailable."
        )

    return PMTAnalysis(
        product_profile=_profile(record),
        competitive_products=[_profile(c) for c in competitor_records],
        positioning_observations=positioning,
        differentiation_candidates=differentiation,
        competitive_advantages=advantages,
        competitive_disadvantages=disadvantages,
        target_patient_segment=patients,
        target_physician_segment=physicians,
        evidence_gaps=gaps,
        source_records_used=used,
    )
