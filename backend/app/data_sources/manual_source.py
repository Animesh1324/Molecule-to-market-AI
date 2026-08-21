"""Manual-import adapter: drug records the team enters or uploads itself.

The escape hatch for everything no public API carries — India-only molecules,
CDSCO-approved combinations absent from FDA registers, and facts taken from a
licensed report the organisation has paid for. Records arrive already
normalised; the adapter's job is to stamp provenance so a hand-entered fact is
never mistaken for a regulator-sourced one.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .base import DrugDataSource, DrugRecord, SourceAttribution

logger = logging.getLogger(__name__)


class ManualImportSource(DrugDataSource):
    name = "Manual import"
    enabled = True
    access_policy = (
        "Records entered by the team or imported from a report the organisation "
        "holds. Always stamped confidence='user-entered' so hand-keyed facts are "
        "visibly distinct from regulator-sourced ones."
    )

    #: Fields a caller may set. Anything else in the payload is ignored rather
    #: than written, so a malformed import cannot inject unexpected columns.
    ALLOWED_FIELDS = {
        "generic_name", "brand_name", "active_ingredients", "drug_class",
        "therapeutic_class", "dosage_forms", "strengths", "routes",
        "indications", "dosage", "contraindications", "warnings", "precautions",
        "adverse_effects", "drug_interactions", "pregnancy_information",
        "lactation_information", "mechanism", "manufacturer", "status",
    }

    LIST_FIELDS = {"active_ingredients", "dosage_forms", "strengths", "routes"}

    def __init__(self, payloads: Optional[List[Dict[str, Any]]] = None):
        self._payloads = payloads or []

    async def fetch(self, query: str) -> List[DrugRecord]:
        term = (query or "").strip().lower()
        matches = [
            p for p in self._payloads
            if term in str(p.get("generic_name", "")).lower()
            or term in str(p.get("brand_name", "")).lower()
        ]
        return [self.to_record(p) for p in matches]

    @classmethod
    def to_record(
        cls,
        payload: Dict[str, Any],
        *,
        source_note: Optional[str] = None,
        entered_by: Optional[str] = None,
    ) -> DrugRecord:
        """Build a normalised record from a caller-supplied dict."""
        clean: Dict[str, Any] = {}
        for key, value in payload.items():
            if key not in cls.ALLOWED_FIELDS or value is None:
                continue
            if key in cls.LIST_FIELDS:
                if isinstance(value, str):
                    clean[key] = [v.strip() for v in value.split(",") if v.strip()]
                else:
                    clean[key] = [str(v).strip() for v in value if str(v).strip()]
            else:
                clean[key] = str(value).strip() or None

        if not clean.get("generic_name"):
            raise ValueError("generic_name is required for a manual drug record.")

        record = DrugRecord(generic_name=str(clean.pop("generic_name")).title())
        for key, value in clean.items():
            setattr(record, key, value)

        record.attribution = SourceAttribution(
            source_name=cls.name,
            source_url=None,
            source_identifier=None,
            attribution=source_note or "Entered in the application by the brand team",
            confidence="user-entered",
        )
        if entered_by:
            record.extra["entered_by"] = entered_by
        return record
