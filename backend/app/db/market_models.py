"""ORM tables for secondary market data (IQVIA/IMS TSA, PharmaTrac, AWACS).

These are the rows no public API carries: which brands of a molecule are
actually sold in a market, who sells them, and what they turn over. Public
sources (openFDA, PubChem, ClinicalTrials.gov) answer "what exists"; this
answers "what competes".

Shares `Base` from `database.py`, so `init_db()` creates these tables too.

Design notes:

* `MarketDataset` is one ingested file. Every brand row points back to it, so a
  re-upload of a newer period replaces a whole dataset atomically and the UI can
  always say which file a number came from.
* `MarketBrand` is one pack row as the source file carries it. Pack rows are NOT
  pre-aggregated to brand level on write, because the same brand legitimately
  appears across strengths and pack sizes, and a brand-level rollup would throw
  away the pack detail a launch team needs. Aggregation happens at query time.
* `molecule_key` is the normalised, salt-stripped molecule used for lookup;
  `molecule_desc` keeps the source's exact wording for display and audit.
  Both are stored because the normalisation is lossy and must stay reversible
  to the original row.
"""
from __future__ import annotations

from sqlalchemy import Column, Float, Index, Integer, String, Text

from .database import Base


class MarketDatasetORM(Base):
    """One ingested secondary-data file."""

    __tablename__ = "market_datasets"

    id = Column(String, primary_key=True, index=True)
    original_filename = Column(String, nullable=False)
    source_label = Column(String, nullable=False, default="Secondary data")
    market = Column(String, nullable=False, default="India")
    # Free text as the file labels it, e.g. "MAT AUG'24".
    period_label = Column(String, nullable=True)
    value_unit = Column(String, nullable=False, default="INR Cr")
    row_count = Column(Integer, nullable=False, default=0)
    brand_count = Column(Integer, nullable=False, default=0)
    molecule_count = Column(Integer, nullable=False, default=0)
    company_count = Column(Integer, nullable=False, default=0)
    total_value = Column(Float, nullable=False, default=0.0)
    # Set when the file arrived through a project upload rather than a path.
    project_id = Column(String, nullable=True, index=True)
    upload_file_id = Column(String, nullable=True)
    status = Column(String, nullable=False, default="ready")
    message = Column(Text, nullable=True)
    ingested_at = Column(String, nullable=False)


class MarketBrandORM(Base):
    """One pack row from a secondary-data extract."""

    __tablename__ = "market_brands"

    id = Column(String, primary_key=True)
    dataset_id = Column(String, nullable=False, index=True)

    molecule_desc = Column(String, nullable=False)     # source wording, verbatim
    molecule_key = Column(String, nullable=False, index=True)  # normalised lookup key
    is_combination = Column(Integer, nullable=False, default=0)

    brand = Column(String, nullable=False, index=True)
    company = Column(String, nullable=True, index=True)
    manufacturer = Column(String, nullable=True)
    ownership = Column(String, nullable=True)          # INDIAN / MNC

    subgroup = Column(String, nullable=True, index=True)
    group_name = Column(String, nullable=True, index=True)
    supergroup = Column(String, nullable=True)
    acute_chronic = Column(String, nullable=True)
    dosage_form = Column(String, nullable=True)
    pack_desc = Column(String, nullable=True)

    # Three trailing MAT periods where the file carries them; latest first.
    value_latest = Column(Float, nullable=False, default=0.0)
    value_prev = Column(Float, nullable=True)
    value_prev2 = Column(Float, nullable=True)
    units_latest = Column(Float, nullable=True)

    period_latest = Column(String, nullable=True)
    period_prev = Column(String, nullable=True)
    period_prev2 = Column(String, nullable=True)


# Molecule lookup is the hot path: every competitor query filters on
# molecule_key, and the class-competitor query filters on group_name.
Index("ix_market_brands_mol_value", MarketBrandORM.molecule_key, MarketBrandORM.value_latest)
Index("ix_market_brands_group_value", MarketBrandORM.group_name, MarketBrandORM.value_latest)
