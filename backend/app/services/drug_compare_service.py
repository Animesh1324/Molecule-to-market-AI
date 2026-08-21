"""Side-by-side drug comparison.

Strictly a presentation of what each record holds. Where a field is missing on
either side it is reported as "Information not available" rather than inferred,
and no judgement is drawn about which drug is better — that is a clinical claim
and this service does not make one.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from ..models.drug import ComparisonField, DrugComparison, InteractionOut
from ..repositories import drug_repository as repo
from . import drug_ingestion_service as ingestion
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


NOT_AVAILABLE = "Information not available"

# Ordered so identity and mechanism read before the safety narrative.
COMPARE_FIELDS: List[Tuple[str, str]] = [
    ("generic_name", "Generic name"),
    ("brand_name", "Brand name"),
    ("active_ingredients", "Active ingredients"),
    ("drug_class", "Drug class"),
    ("therapeutic_class", "Therapeutic class"),
    ("mechanism", "Mechanism of action"),
    ("indications", "Indications"),
    ("dosage", "Dosage"),
    ("routes", "Route of administration"),
    ("dosage_forms", "Dosage forms"),
    ("strengths", "Strengths"),
    ("adverse_effects", "Adverse effects"),
    ("contraindications", "Contraindications"),
    ("warnings", "Warnings"),
    ("precautions", "Precautions"),
    ("drug_interactions", "Drug interactions"),
    ("pregnancy_information", "Pregnancy"),
    ("lactation_information", "Lactation"),
    ("manufacturer", "Manufacturer"),
]


def _value(record: Optional[Dict[str, Any]], field: str) -> Optional[str]:
    if not record:
        return None
    raw = record.get(field)
    if raw is None or raw == "" or raw == []:
        return None
    if isinstance(raw, list):
        return ", ".join(str(v) for v in raw) or None
    return str(raw)


async def _resolve_one(name: str, ingest_if_missing: bool) -> Optional[Dict[str, Any]]:
    result = await search_service.search(
        name, page=1, page_size=1, ingest_if_missing=ingest_if_missing
    )
    return _as_dict(result.items[0]) if result.items else None


async def compare(drug_a: str, drug_b: str, ingest_if_missing: bool = True) -> DrugComparison:
    record_a = await _resolve_one(drug_a, ingest_if_missing)
    record_b = await _resolve_one(drug_b, ingest_if_missing)

    fields: List[ComparisonField] = []
    missing_both: List[str] = []

    for key, label in COMPARE_FIELDS:
        value_a = _value(record_a, key)
        value_b = _value(record_b, key)
        both = value_a is not None and value_b is not None
        if value_a is None and value_b is None:
            missing_both.append(label)
        fields.append(
            ComparisonField(
                field=key,
                label=label,
                drug_a_value=value_a if value_a is not None else NOT_AVAILABLE,
                drug_b_value=value_b if value_b is not None else NOT_AVAILABLE,
                both_available=both,
                # Only claim a difference when both sides are actually present:
                # a missing value is not evidence of a difference.
                differs=bool(both and value_a.strip().lower() != value_b.strip().lower()),
            )
        )

    shared: List[InteractionOut] = []
    if record_a and record_b:
        name_a = record_a.get("generic_name") or drug_a
        name_b = record_b.get("generic_name") or drug_b
        for row in repo.interactions_for(name_a):
            pair = {row["drug_a"].lower(), row["drug_b"].lower()}
            if name_b.lower() in pair:
                shared.append(InteractionOut(**row))

    if record_a and record_b:
        comparable = sum(1 for f in fields if f.both_available)
        note = (
            f"{comparable} of {len(fields)} fields are populated on both records. "
            f"{len(missing_both)} field(s) are absent from both sources."
        )
    elif record_a or record_b:
        found = (record_a or record_b or {}).get("generic_name", "one drug")
        missing = drug_b if record_a else drug_a
        note = (
            f"Only '{found}' could be resolved. No record was found for '{missing}', "
            "so this is a one-sided view rather than a comparison."
        )
    else:
        note = f"Neither '{drug_a}' nor '{drug_b}' could be resolved from the permitted sources."

    return DrugComparison(
        drug_a=record_a,
        drug_b=record_b,
        fields=fields,
        shared_interactions=shared,
        fields_missing_for_both=missing_both,
        comparison_note=note,
        caveat=(
            "A side-by-side presentation of label text, not a clinical assessment. "
            "Differences shown are textual, not evidence of comparative efficacy or "
            "safety — a head-to-head claim needs a head-to-head trial. Fields marked "
            f"'{NOT_AVAILABLE}' are absent from the source, not known to be absent "
            "from the drug."
        ),
    )
