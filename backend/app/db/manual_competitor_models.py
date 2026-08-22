"""Manually-attested competitors — for exactly the gap a licensed extract can
leave: a brand a team knows is real and marketed, that the loaded audit file
doesn't cover because it's newer than the file's period, or because no
licensed extract has ever been loaded for that market.

Deliberately separate from `market_models.MarketBrandORM`, which holds rows
from a licensed audit extract (IQVIA/IMS, PharmaTrac) — those are independently
compiled, auditable, and carry a dataset/period a reviewer can trace back to a
file. A manual entry is one person's attestation: real, but not independently
verified the same way, so it must never be presented at the same authority
tier. It is stored, displayed, and exported with its own provenance tag,
never merged into the licensed layer's numbers.
"""
from __future__ import annotations

from sqlalchemy import Column, Float, Index, String, Text

from .database import Base


class ManualCompetitorORM(Base):
    """One team-attested competitor brand for a molecule."""

    __tablename__ = "manual_competitors"

    id = Column(String, primary_key=True, index=True)
    molecule_key = Column(String, nullable=False, index=True)  # normalised, for lookup
    molecule_desc = Column(String, nullable=False)              # as entered, for display

    brand = Column(String, nullable=False)
    company = Column(String, nullable=True)
    market = Column(String, nullable=True)             # e.g. "India"

    # Optional, since a manual entry is often added precisely because a
    # licensed value isn't available yet — the brand's existence is the fact
    # being attested, not necessarily its exact sales figure.
    value_estimate = Column(Float, nullable=True)
    value_unit = Column(String, nullable=True)
    value_basis = Column(Text, nullable=True)   # how the figure was arrived at, if given

    # Provenance is mandatory: an entry with no source is indistinguishable
    # from a guess, which is exactly what this table must never become.
    source_note = Column(Text, nullable=False)
    added_by = Column(String, nullable=False)
    added_at = Column(String, nullable=False)


Index("ix_manual_competitors_molecule", ManualCompetitorORM.molecule_key)
