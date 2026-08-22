"""ORM tables for the FDA catalogue datasets that are not drug monographs.

`drug_models.py` holds one normalised row per drug. These are different
entities and do not belong on it: an approval application is not a drug, a
recall is an event, a shortage is a supply state. Forcing them onto `DrugORM`
would mean either sparse columns most rows never use, or losing the natural
key each of them already has.

Shares `Base` from `database.py`, so `init_db()` creates them alongside
everything else and they live in whichever database `DATABASE_URL` points at.

Not included here:

* Orange Book — the application already ingests FDA's own Orange Book zip in
  `services/orange_book.py`, which carries patent.txt and exclusivity.txt.
  openFDA's `orangebook` dataset has neither; it stops at therapeutic
  equivalence codes. Loading it would replace a better source with a worse one.
* FAERS (`drug/event`) — 20.7 million reports, ~114 GB. Needs a deliberate
  decision about storage and sampling, not a default bulk load.
"""
from __future__ import annotations

from sqlalchemy import Column, DateTime, Index, Integer, String, Text, UniqueConstraint, func

from .database import Base


class FDAApplicationORM(Base):
    """One FDA application (NDA/ANDA/BLA) from drug/drugsfda."""

    __tablename__ = "fda_applications"

    application_number = Column(String, primary_key=True, index=True)
    sponsor_name = Column(String, nullable=True, index=True)
    # Denormalised for the common "what is this application for" lookup, which
    # otherwise needs a join to products on every row.
    brand_names = Column(Text, nullable=False, default="[]")
    generic_names = Column(Text, nullable=False, default="[]")
    data_version = Column(String, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class FDAApplicationProductORM(Base):
    __tablename__ = "fda_application_products"

    id = Column(String, primary_key=True, index=True)
    application_number = Column(String, nullable=False, index=True)
    product_number = Column(String, nullable=True)
    brand_name = Column(String, nullable=True, index=True)
    active_ingredients = Column(Text, nullable=False, default="[]")
    strengths = Column(Text, nullable=False, default="[]")
    dosage_form = Column(String, nullable=True)
    route = Column(String, nullable=True)
    marketing_status = Column(String, nullable=True, index=True)
    reference_drug = Column(String, nullable=True)
    reference_standard = Column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint("application_number", "product_number", name="uq_app_product"),
    )


class FDASubmissionORM(Base):
    """Approval history: each submission against an application.

    This is what answers "when was it first approved" and "how many supplements
    since" — `submission_type` ORIG number 1 is the original approval.
    """

    __tablename__ = "fda_submissions"

    id = Column(String, primary_key=True, index=True)
    application_number = Column(String, nullable=False, index=True)
    submission_type = Column(String, nullable=True, index=True)
    submission_number = Column(String, nullable=True)
    submission_status = Column(String, nullable=True)
    submission_status_date = Column(String, nullable=True, index=True)
    submission_class_code = Column(String, nullable=True)
    submission_class_description = Column(String, nullable=True)
    review_priority = Column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint("application_number", "submission_type", "submission_number",
                         name="uq_app_submission"),
        Index("ix_submission_app_date", "application_number", "submission_status_date"),
    )


class DrugRecallORM(Base):
    """FDA enforcement report. Class I is the most serious."""

    __tablename__ = "drug_recalls"

    recall_number = Column(String, primary_key=True, index=True)
    event_id = Column(String, nullable=True, index=True)
    product_description = Column(Text, nullable=True)
    reason_for_recall = Column(Text, nullable=True)
    classification = Column(String, nullable=True, index=True)
    status = Column(String, nullable=True, index=True)
    recalling_firm = Column(String, nullable=True, index=True)
    product_type = Column(String, nullable=True)
    product_quantity = Column(String, nullable=True)
    voluntary_mandated = Column(String, nullable=True)
    distribution_pattern = Column(Text, nullable=True)
    country = Column(String, nullable=True)
    state = Column(String, nullable=True)
    city = Column(String, nullable=True)
    recall_initiation_date = Column(String, nullable=True, index=True)
    report_date = Column(String, nullable=True)
    termination_date = Column(String, nullable=True)
    # Searchable lower-cased description, same trick as DrugORM.search_blob:
    # one indexed LIKE instead of scanning several text columns.
    search_blob = Column(Text, nullable=False, default="")
    data_version = Column(String, nullable=True)

    __table_args__ = (Index("ix_recall_search_blob", "search_blob"),)


class DrugShortageORM(Base):
    """Current and resolved supply shortages from drug/shortages."""

    __tablename__ = "drug_shortages"

    id = Column(String, primary_key=True, index=True)
    generic_name = Column(String, nullable=True, index=True)
    company_name = Column(String, nullable=True, index=True)
    status = Column(String, nullable=True, index=True)
    availability = Column(Text, nullable=True)
    shortage_reason = Column(Text, nullable=True)
    therapeutic_category = Column(String, nullable=True, index=True)
    dosage_form = Column(String, nullable=True)
    presentation = Column(Text, nullable=True)
    package_ndc = Column(String, nullable=True, index=True)
    initial_posting_date = Column(String, nullable=True, index=True)
    update_date = Column(String, nullable=True)
    update_type = Column(String, nullable=True)
    contact_info = Column(Text, nullable=True)
    data_version = Column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint("generic_name", "company_name", "presentation", "initial_posting_date",
                         name="uq_shortage_entry"),
    )
