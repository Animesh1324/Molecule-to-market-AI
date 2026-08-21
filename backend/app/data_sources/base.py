"""Source-adapter interface for drug information.

Every drug fact enters the application through one of these adapters, so the
application never depends on a single upstream. A source can be unavailable,
unlicensed, or rate-limited without the Drug Intelligence module going down —
the repository still serves whatever was previously ingested and cached.

The contract each adapter honours:

* return normalised `DrugRecord` objects, never raw upstream payloads
* attach provenance (source name, URL, identifier, retrieval time) to every record
* fail soft — raise `SourceUnavailable`, never crash the caller
* never fabricate a field; absent data stays `None` so the UI can say
  "Information not available" instead of implying a fact
"""
from __future__ import annotations

import abc
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class SourceUnavailable(RuntimeError):
    """The upstream could not be reached, is not licensed, or returned garbage."""


class SourceNotPermitted(SourceUnavailable):
    """The upstream forbids automated ingestion without a licence/feed.

    Distinct from a transient outage: retrying will never help, so the
    ingestion service records it and moves on rather than backing off.
    """


@dataclass
class SourceAttribution:
    """Provenance for one ingested record. Required — never optional."""

    source_name: str
    source_url: Optional[str] = None
    source_identifier: Optional[str] = None
    data_version: Optional[str] = None
    published_at: Optional[str] = None
    attribution: Optional[str] = None
    confidence: str = "unverified"          # verified | reported | derived | unverified
    retrieved_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    )


@dataclass
class DrugRecord:
    """One normalised drug, independent of which source produced it.

    Every clinical field is Optional on purpose: a missing indication must be
    distinguishable from an empty one, because "not available" and "none" mean
    very different things on a label.
    """

    generic_name: str
    brand_name: Optional[str] = None
    active_ingredients: List[str] = field(default_factory=list)
    drug_class: Optional[str] = None
    therapeutic_class: Optional[str] = None
    dosage_forms: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    routes: List[str] = field(default_factory=list)
    indications: Optional[str] = None
    dosage: Optional[str] = None
    contraindications: Optional[str] = None
    warnings: Optional[str] = None
    precautions: Optional[str] = None
    adverse_effects: Optional[str] = None
    drug_interactions: Optional[str] = None
    pregnancy_information: Optional[str] = None
    lactation_information: Optional[str] = None
    mechanism: Optional[str] = None
    manufacturer: Optional[str] = None
    status: str = "active"
    attribution: Optional[SourceAttribution] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def merge_key(self) -> str:
        """Identity used to deduplicate across sources."""
        brand = (self.brand_name or "").strip().lower()
        generic = (self.generic_name or "").strip().lower()
        return f"{generic}|{brand}"


@dataclass
class InteractionRecord:
    """A pairwise interaction, normalised across sources."""

    drug_a: str
    drug_b: str
    severity: Optional[str] = None          # major | moderate | minor | unknown
    description: Optional[str] = None
    management: Optional[str] = None
    attribution: Optional[SourceAttribution] = None


class DrugDataSource(abc.ABC):
    """Base class every adapter implements."""

    #: Stable identifier stored on each record's provenance row.
    name: str = "unknown"

    #: False when the adapter needs a licence or credential it does not have.
    #: The ingestion service skips it rather than attempting a forbidden fetch.
    enabled: bool = True

    #: Human-readable statement of what this source is and how it is accessed.
    access_policy: str = ""

    @abc.abstractmethod
    async def fetch(self, query: str) -> List[DrugRecord]:
        """Return normalised drug records matching `query`.

        Must raise `SourceUnavailable` (or `SourceNotPermitted`) on failure
        rather than propagating transport errors.
        """

    async def fetch_interactions(self, query: str) -> List[InteractionRecord]:
        """Return interactions for `query`. Sources without them return []."""
        return []

    def describe(self) -> Dict[str, Any]:
        """Metadata for the sources endpoint and the admin refresh report."""
        return {
            "name": self.name,
            "enabled": self.enabled,
            "access_policy": self.access_policy,
            "supports_interactions": type(self).fetch_interactions is not DrugDataSource.fetch_interactions,
        }
