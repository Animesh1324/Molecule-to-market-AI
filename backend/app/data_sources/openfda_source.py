"""openFDA adapter: label text, product identity, and class.

The FDA's Structured Product Labeling is the authoritative public source for
the clinical fields this module carries — indications, dosage, warnings,
contraindications, adverse reactions, interactions, pregnancy and lactation.
It is a documented public API with no licence restriction, which is why it is
the default ingestion source rather than a consumer drug site.

Two endpoints are combined:

* ``/drug/label``  — the label narrative (most of the clinical fields)
* ``/drug/ndc``    — marketed product identity (brand, dosage form, strength,
                     route, class, manufacturer), which the label omits or
                     buries
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

from ..services.inn_synonyms import candidates as name_candidates
from .base import DrugDataSource, DrugRecord, SourceAttribution, SourceUnavailable

logger = logging.getLogger(__name__)

LABEL_URL = "https://api.fda.gov/drug/label.json"
NDC_URL = "https://api.fda.gov/drug/ndc.json"

# Label section -> DrugRecord field. Several sections carry the same clinical
# meaning under different SPL names, so each target lists its candidates in
# priority order.
_LABEL_FIELD_MAP: Dict[str, List[str]] = {
    "indications": ["indications_and_usage"],
    "dosage": ["dosage_and_administration"],
    "contraindications": ["contraindications"],
    "warnings": ["boxed_warning", "warnings_and_cautions", "warnings"],
    "precautions": ["precautions", "general_precautions"],
    "adverse_effects": ["adverse_reactions"],
    "drug_interactions": ["drug_interactions", "drug_and_or_laboratory_test_interactions"],
    "pregnancy_information": ["pregnancy", "teratogenic_effects"],
    "lactation_information": ["nursing_mothers", "lactation"],
    "mechanism": ["mechanism_of_action", "clinical_pharmacology"],
}

MAX_FIELD_CHARS = 6000


def _first_text(record: Dict[str, Any], keys: List[str]) -> Optional[str]:
    """First populated label section among `keys`, whitespace-normalised."""
    for key in keys:
        value = record.get(key)
        if not value:
            continue
        if isinstance(value, list):
            text = " ".join(str(v) for v in value if v)
        else:
            text = str(value)
        text = " ".join(text.split())
        if text:
            return text[:MAX_FIELD_CHARS]
    return None


def _unique(values: Optional[List[Any]]) -> List[str]:
    out: List[str] = []
    for value in values or []:
        text = str(value).strip()
        if text and text not in out:
            out.append(text)
    return out


class OpenFDASource(DrugDataSource):
    name = "openFDA"
    enabled = True
    access_policy = (
        "Public FDA API (api.fda.gov). No licence or key required for the "
        "request volumes this application makes. Terms permit programmatic use."
    )

    def __init__(self, timeout: float = 20.0, limit: int = 5):
        self.timeout = timeout
        self.limit = limit

    async def _query(self, client: httpx.AsyncClient, url: str, search: str) -> List[Dict[str, Any]]:
        try:
            response = await client.get(
                url, params={"search": search, "limit": str(self.limit)}
            )
        except Exception as exc:
            raise SourceUnavailable(f"openFDA request failed: {exc}") from exc

        # openFDA answers "nothing matched" with 404 rather than an empty list.
        if response.status_code == 404:
            return []
        if response.status_code == 429:
            raise SourceUnavailable("openFDA rate limit reached")
        if response.status_code != 200:
            raise SourceUnavailable(f"openFDA returned HTTP {response.status_code}")
        try:
            return response.json().get("results", []) or []
        except ValueError as exc:
            raise SourceUnavailable("openFDA returned malformed JSON") from exc

    async def fetch(self, query: str) -> List[DrugRecord]:
        term = (query or "").strip()
        if not term:
            return []

        # Try each accepted spelling; INN names (paracetamol) are not what the
        # FDA files under (acetaminophen).
        aliases = name_candidates(term)[:3]

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            label_results: List[Dict[str, Any]] = []
            ndc_results: List[Dict[str, Any]] = []
            for alias in aliases:
                if not label_results:
                    label_results = await self._query(
                        client, LABEL_URL, f'openfda.generic_name:"{alias}"'
                    )
                if not ndc_results:
                    ndc_results = await self._query(
                        client, NDC_URL, f'generic_name:"{alias}"'
                    )
                if label_results and ndc_results:
                    break

        if not label_results and not ndc_results:
            return []

        # Product identity comes from NDC; the narrative from the label.
        identity = self._identity_from_ndc(ndc_results)
        records: List[DrugRecord] = []

        for label in label_results or [{}]:
            openfda = label.get("openfda", {}) or {}
            brand = (_unique(openfda.get("brand_name")) or identity.get("brands") or [None])[0]
            generic = (
                (_unique(openfda.get("generic_name")) or identity.get("generics") or [term])[0]
            ).title()

            attribution = SourceAttribution(
                source_name=self.name,
                source_url="https://open.fda.gov/apis/drug/label/",
                source_identifier=label.get("id") or (openfda.get("spl_id") or [None])[0],
                data_version=label.get("effective_time"),
                published_at=label.get("effective_time"),
                attribution="U.S. Food and Drug Administration — Structured Product Labeling",
                confidence="verified",
            )

            record = DrugRecord(
                generic_name=generic,
                brand_name=brand,
                active_ingredients=_unique(openfda.get("substance_name")) or identity.get("ingredients", []),
                drug_class=(_unique(openfda.get("pharm_class_epc")) or identity.get("classes") or [None])[0],
                therapeutic_class=(_unique(openfda.get("pharm_class_moa")) or [None])[0],
                dosage_forms=identity.get("dosage_forms", []),
                strengths=identity.get("strengths", []),
                routes=_unique(openfda.get("route")) or identity.get("routes", []),
                manufacturer=(_unique(openfda.get("manufacturer_name")) or identity.get("manufacturers") or [None])[0],
                attribution=attribution,
            )
            for target, keys in _LABEL_FIELD_MAP.items():
                setattr(record, target, _first_text(label, keys))

            records.append(record)

        # Label had nothing but NDC did: still worth a product-identity record.
        if not records and identity.get("generics"):
            records.append(
                DrugRecord(
                    generic_name=identity["generics"][0].title(),
                    brand_name=(identity.get("brands") or [None])[0],
                    active_ingredients=identity.get("ingredients", []),
                    drug_class=(identity.get("classes") or [None])[0],
                    dosage_forms=identity.get("dosage_forms", []),
                    strengths=identity.get("strengths", []),
                    routes=identity.get("routes", []),
                    manufacturer=(identity.get("manufacturers") or [None])[0],
                    attribution=SourceAttribution(
                        source_name=self.name,
                        source_url="https://open.fda.gov/apis/drug/ndc/",
                        attribution="U.S. FDA National Drug Code Directory",
                        confidence="verified",
                    ),
                )
            )
        return records

    @staticmethod
    def _identity_from_ndc(results: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Collapse NDC rows into product-identity lists."""
        out: Dict[str, List[str]] = {
            "brands": [], "generics": [], "ingredients": [], "classes": [],
            "dosage_forms": [], "strengths": [], "routes": [], "manufacturers": [],
        }

        def add(key: str, value: Optional[str]) -> None:
            text = (value or "").strip()
            if text and text not in out[key]:
                out[key].append(text)

        for row in results:
            add("brands", row.get("brand_name"))
            add("generics", row.get("generic_name"))
            add("dosage_forms", row.get("dosage_form"))
            add("manufacturers", row.get("labeler_name"))
            for route in row.get("route", []) or []:
                add("routes", route)
            for pharm_class in row.get("pharm_class", []) or []:
                add("classes", pharm_class)
            for ingredient in row.get("active_ingredients", []) or []:
                add("ingredients", ingredient.get("name"))
                strength = ingredient.get("strength")
                if strength:
                    add("strengths", strength)
        return out
