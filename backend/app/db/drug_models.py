"""ORM tables for the Drug Intelligence module.

Shares the existing `Base`, engine, and session factory from `database.py`, so
the new tables are created by the same `init_db()` call and live in whichever
database `DATABASE_URL` points at. Nothing here alters the existing tables.

Design notes:

* `Drug` holds one normalised drug. List-valued fields (ingredients, strengths)
  are stored as JSON text rather than child tables — they are always read and
  written whole, never queried element-wise, so a join table would add cost
  without buying anything.
* `DrugSource` is a child of `Drug` rather than columns on it, because the same
  drug legitimately carries facts from several sources and each needs its own
  retrieval timestamp and confidence.
* `DrugInteraction` stores the pair normalised (alphabetically ordered) so
  A-vs-B and B-vs-A cannot both be inserted.
"""
from __future__ import annotations

import json
from typing import Any, List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from .database import Base


def dumps(values: Optional[List[str]]) -> str:
    return json.dumps(values or [])


def loads(raw: Optional[str]) -> List[str]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
        return [str(v) for v in parsed] if isinstance(parsed, list) else []
    except (ValueError, TypeError):
        return []


class DrugORM(Base):
    __tablename__ = "drugs"

    id = Column(String, primary_key=True, index=True)

    # Identity. `search_blob` is a lower-cased concatenation maintained on write
    # so search is one indexed LIKE rather than a scan across many columns.
    generic_name = Column(String, nullable=False, index=True)
    brand_name = Column(String, nullable=True, index=True)
    search_blob = Column(Text, nullable=False, default="")

    active_ingredients = Column(Text, nullable=False, default="[]")
    drug_class = Column(String, nullable=True, index=True)
    therapeutic_class = Column(String, nullable=True, index=True)
    dosage_forms = Column(Text, nullable=False, default="[]")
    strengths = Column(Text, nullable=False, default="[]")
    routes = Column(Text, nullable=False, default="[]")
    manufacturer = Column(String, nullable=True)

    # Clinical narrative. Nullable throughout: absent must stay distinguishable
    # from empty so the UI can say "Information not available".
    indications = Column(Text, nullable=True)
    dosage = Column(Text, nullable=True)
    contraindications = Column(Text, nullable=True)
    warnings = Column(Text, nullable=True)
    precautions = Column(Text, nullable=True)
    adverse_effects = Column(Text, nullable=True)
    drug_interactions = Column(Text, nullable=True)
    pregnancy_information = Column(Text, nullable=True)
    lactation_information = Column(Text, nullable=True)
    mechanism = Column(Text, nullable=True)

    status = Column(String, nullable=False, default="active", index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    sources = relationship(
        "DrugSourceORM", back_populates="drug",
        cascade="all, delete-orphan", lazy="selectin",
    )

    __table_args__ = (
        # One row per generic+brand pairing; re-ingestion updates rather than duplicates.
        UniqueConstraint("generic_name", "brand_name", name="uq_drug_generic_brand"),
        Index("ix_drug_search_blob", "search_blob"),
    )


class DrugSourceORM(Base):
    """Provenance for one drug record. Never optional — see module docstring."""

    __tablename__ = "drug_sources"

    id = Column(String, primary_key=True, index=True)
    drug_id = Column(String, ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False, index=True)

    source_name = Column(String, nullable=False, index=True)
    source_url = Column(String, nullable=True)
    source_identifier = Column(String, nullable=True)
    data_version = Column(String, nullable=True)
    published_at = Column(String, nullable=True)
    attribution = Column(Text, nullable=True)
    confidence = Column(String, nullable=False, default="unverified")
    retrieved_at = Column(String, nullable=False)

    drug = relationship("DrugORM", back_populates="sources")

    __table_args__ = (
        UniqueConstraint("drug_id", "source_name", name="uq_drug_source"),
    )


class DrugInteractionORM(Base):
    __tablename__ = "drug_interactions"

    id = Column(String, primary_key=True, index=True)
    # Stored alphabetically ordered so a pair can only be recorded once.
    drug_a = Column(String, nullable=False, index=True)
    drug_b = Column(String, nullable=False, index=True)
    severity = Column(String, nullable=False, default="unknown", index=True)
    description = Column(Text, nullable=True)
    management = Column(Text, nullable=True)

    source_name = Column(String, nullable=False, default="unknown")
    source_url = Column(String, nullable=True)
    retrieved_at = Column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint("drug_a", "drug_b", "source_name", name="uq_interaction_pair"),
        Index("ix_interaction_pair", "drug_a", "drug_b"),
    )


class IngestionLogORM(Base):
    """Audit of every refresh attempt, so a silent source failure is visible."""

    __tablename__ = "drug_ingestion_log"

    id = Column(String, primary_key=True, index=True)
    query = Column(String, nullable=False)
    source_name = Column(String, nullable=False, index=True)
    succeeded = Column(Boolean, nullable=False, default=False)
    records_written = Column(String, nullable=False, default="0")
    message = Column(Text, nullable=True)
    started_at = Column(String, nullable=False)
    finished_at = Column(String, nullable=True)
