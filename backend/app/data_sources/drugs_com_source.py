"""Drugs.com adapter — implemented, disabled until an authorised feed exists.

Why this adapter does not scrape
--------------------------------
Drugs.com returns HTTP 403 to programmatic requests, which is an explicit
technical access control. Its terms prohibit automated extraction, and the
monograph and review content is proprietary and copyrighted. Beyond the legal
position there is a practical one for this application: content copied from a
consumer drug site cannot be cited in an MLR-reviewed brand plan, so scraped
text would fail review even if it were obtained.

What this adapter is for
------------------------
Drugs.com publishes licensed data feeds through Drugs.com/DrugBank commercial
agreements. This adapter is written against that feed so the day a licence
exists, ingestion is a configuration change — set `DRUGS_COM_API_KEY` (and
`DRUGS_COM_API_BASE` if the endpoint differs) — not a rewrite.

Until then `enabled` is False, the ingestion service skips it, and the
application runs on openFDA and the manual-import path. Calling `fetch()`
without a key raises `SourceNotPermitted`, which the ingestion service records
as a permanent skip rather than retrying.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

import httpx

from .base import (
    DrugDataSource,
    DrugRecord,
    InteractionRecord,
    SourceAttribution,
    SourceNotPermitted,
    SourceUnavailable,
)

logger = logging.getLogger(__name__)

DEFAULT_API_BASE = "https://api.drugs.com/v1"


def _api_key() -> str:
    return os.getenv("DRUGS_COM_API_KEY", "").strip()


def _api_base() -> str:
    return os.getenv("DRUGS_COM_API_BASE", DEFAULT_API_BASE).strip().rstrip("/")


class DrugsComSource(DrugDataSource):
    name = "Drugs.com"

    access_policy = (
        "Licensed data feed only. Drugs.com blocks programmatic access (HTTP 403) "
        "and its terms prohibit automated extraction; its monographs and user "
        "reviews are copyrighted. This adapter targets an authorised Drugs.com / "
        "DrugBank feed and stays disabled until DRUGS_COM_API_KEY is configured. "
        "No scraping is performed under any configuration."
    )

    def __init__(self, timeout: float = 20.0):
        self.timeout = timeout

    @property
    def enabled(self) -> bool:  # type: ignore[override]
        """Only active once a licence key is present."""
        return bool(_api_key())

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {_api_key()}",
            "Accept": "application/json",
            "User-Agent": "PharmaBrandPlanAI/1.0 (licensed feed client)",
        }

    def _require_licence(self) -> None:
        if not _api_key():
            raise SourceNotPermitted(
                "Drugs.com ingestion requires a licensed data feed. Set "
                "DRUGS_COM_API_KEY to enable it. Scraping the website is not "
                "supported: it is blocked by the site and prohibited by its terms."
            )

    async def _get(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{_api_base()}/{path.lstrip('/')}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params, headers=self._headers())
        except Exception as exc:
            raise SourceUnavailable(f"Drugs.com feed unreachable: {exc}") from exc

        if response.status_code in (401, 403):
            raise SourceNotPermitted(
                "Drugs.com feed rejected the credential. Check the licence status "
                "of DRUGS_COM_API_KEY."
            )
        if response.status_code == 429:
            raise SourceUnavailable("Drugs.com feed rate limit reached")
        if response.status_code != 200:
            raise SourceUnavailable(f"Drugs.com feed returned HTTP {response.status_code}")
        try:
            return response.json()
        except ValueError as exc:
            raise SourceUnavailable("Drugs.com feed returned malformed JSON") from exc

    def _attribution(self, payload: Dict[str, Any]) -> SourceAttribution:
        identifier = payload.get("id") or payload.get("slug")
        return SourceAttribution(
            source_name=self.name,
            source_url=payload.get("url") or (
                f"https://www.drugs.com/{identifier}.html" if identifier else "https://www.drugs.com/"
            ),
            source_identifier=str(identifier) if identifier else None,
            data_version=payload.get("version") or payload.get("revision"),
            published_at=payload.get("updated_at") or payload.get("last_reviewed"),
            attribution="Drugs.com licensed data feed",
            confidence="reported",
        )

    async def fetch(self, query: str) -> List[DrugRecord]:
        self._require_licence()
        payload = await self._get("drugs/search", {"q": query, "limit": 5})

        records: List[DrugRecord] = []
        for item in payload.get("results", []) or []:
            records.append(
                DrugRecord(
                    generic_name=(item.get("generic_name") or query).title(),
                    brand_name=item.get("brand_name"),
                    active_ingredients=[
                        str(i) for i in (item.get("active_ingredients") or []) if i
                    ],
                    drug_class=item.get("drug_class"),
                    therapeutic_class=item.get("therapeutic_class"),
                    dosage_forms=[str(f) for f in (item.get("dosage_forms") or []) if f],
                    strengths=[str(s) for s in (item.get("strengths") or []) if s],
                    routes=[str(r) for r in (item.get("routes") or []) if r],
                    indications=item.get("indications"),
                    dosage=item.get("dosage"),
                    contraindications=item.get("contraindications"),
                    warnings=item.get("warnings"),
                    precautions=item.get("precautions"),
                    adverse_effects=item.get("side_effects") or item.get("adverse_effects"),
                    drug_interactions=item.get("interactions"),
                    pregnancy_information=item.get("pregnancy"),
                    lactation_information=item.get("breastfeeding") or item.get("lactation"),
                    mechanism=item.get("mechanism_of_action"),
                    manufacturer=item.get("manufacturer"),
                    attribution=self._attribution(item),
                )
            )
        return records

    async def fetch_interactions(self, query: str) -> List[InteractionRecord]:
        self._require_licence()
        payload = await self._get("interactions", {"drug": query, "limit": 50})

        out: List[InteractionRecord] = []
        for item in payload.get("results", []) or []:
            out.append(
                InteractionRecord(
                    drug_a=item.get("drug_a") or query,
                    drug_b=item.get("drug_b") or "",
                    severity=(item.get("severity") or "unknown").lower(),
                    description=item.get("description"),
                    management=item.get("management"),
                    attribution=self._attribution(item),
                )
            )
        return out
