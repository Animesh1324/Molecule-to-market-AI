"""Generic cache for expensive, slowly-changing external lookups.

openFDA's own live latency (2-5s per query, sometimes more, entirely outside
this app's control) was measured as the dominant cost of loading Module 1
and Module 4 for any non-curated molecule — paid again on every single page
load of the same project, even though a drug's FDA label and application
history change on the order of months or years, not between one page view
and the next.

Deliberately generic (one table, a string key naming which computation it
caches) rather than a bespoke table per data type: the shape here — key,
JSON payload, fetched-at — is identical for the molecule profile and the
regulatory dossier, and a third slow external lookup would need nothing new.
"""
from __future__ import annotations

from sqlalchemy import Column, String, Text

from .database import Base


class ResponseCacheORM(Base):
    __tablename__ = "response_cache"

    # e.g. "molecule_profile:rosuvastatin" or "regulatory:rosuvastatin" — the
    # computation name and the molecule, so the same molecule can be cached
    # independently under each expensive call that covers it.
    cache_key = Column(String, primary_key=True)
    payload_json = Column(Text, nullable=False)
    fetched_at = Column(String, nullable=False)
