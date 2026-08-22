"""ORM tables for the FDA Orange Book.

`services/orange_book.py` already parses FDA's Orange Book zip, but only into a
process-global dict rebuilt on demand. That serves a single molecule lookup and
nothing else: it cannot be joined, filtered, sorted, or queried alongside the
rest of the catalogue, and every worker process pays to rebuild it.

These tables persist the same three files so patent expiry — the field that
answers "when does this go generic", and the one dataset no other source in the
application carries — becomes ordinary queryable data.

`patent_expire_date` is stored twice on purpose: the FDA's own display string
("Aug 24, 2026") and an ISO normalisation for sorting and range queries. Losing
the original would make a parse failure invisible, so both are kept and the ISO
column stays NULL when the text cannot be parsed.
"""
from __future__ import annotations

from sqlalchemy import Column, Index, String, Text

from .database import Base


class OrangeBookProductORM(Base):
    __tablename__ = "orange_book_products"

    id = Column(String, primary_key=True, index=True)          # appl_type|appl_no|product_no
    appl_type = Column(String, nullable=True, index=True)      # N = NDA, A = ANDA
    appl_no = Column(String, nullable=False, index=True)
    product_no = Column(String, nullable=True)
    ingredient = Column(String, nullable=True, index=True)
    trade_name = Column(String, nullable=True, index=True)
    applicant = Column(String, nullable=True)
    applicant_full_name = Column(String, nullable=True)
    strength = Column(Text, nullable=True)
    dosage_form_route = Column(String, nullable=True)
    # AB means therapeutically equivalent to the RLD - the substitutability
    # signal a generic entrant needs.
    te_code = Column(String, nullable=True, index=True)
    approval_date = Column(String, nullable=True)
    approval_date_iso = Column(String, nullable=True, index=True)
    rld = Column(String, nullable=True, index=True)            # reference listed drug
    rs = Column(String, nullable=True)                         # reference standard
    marketing_type = Column(String, nullable=True, index=True) # RX / OTC / DISCN

    __table_args__ = (Index("ix_ob_product_appl", "appl_no", "product_no"),)


class OrangeBookPatentORM(Base):
    __tablename__ = "orange_book_patents"

    id = Column(String, primary_key=True, index=True)
    appl_type = Column(String, nullable=True)
    appl_no = Column(String, nullable=False, index=True)
    product_no = Column(String, nullable=True)
    patent_no = Column(String, nullable=True, index=True)
    patent_expire_date = Column(String, nullable=True)
    # ISO form for ORDER BY and range filters; NULL if the text would not parse.
    patent_expire_date_iso = Column(String, nullable=True, index=True)
    drug_substance_flag = Column(String, nullable=True)
    drug_product_flag = Column(String, nullable=True)
    patent_use_code = Column(String, nullable=True, index=True)
    delist_flag = Column(String, nullable=True)
    submission_date = Column(String, nullable=True)

    __table_args__ = (Index("ix_ob_patent_appl", "appl_no", "product_no"),)


class OrangeBookExclusivityORM(Base):
    __tablename__ = "orange_book_exclusivity"

    id = Column(String, primary_key=True, index=True)
    appl_type = Column(String, nullable=True)
    appl_no = Column(String, nullable=False, index=True)
    product_no = Column(String, nullable=True)
    exclusivity_code = Column(String, nullable=True, index=True)
    exclusivity_date = Column(String, nullable=True)
    exclusivity_date_iso = Column(String, nullable=True, index=True)

    __table_args__ = (Index("ix_ob_excl_appl", "appl_no", "product_no"),)
