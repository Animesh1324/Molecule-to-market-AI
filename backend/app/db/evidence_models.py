"""Cached PubMed bibliography.

Why cache at all: NCBI E-utilities is rate-limited (3 req/s without an API key,
10 with) and a molecule like rosuvastatin has thousands of indexed papers.
Paging that live on every screen load would be slow, would hammer a public
service, and would leave the module empty whenever NCBI is briefly unreachable.
Caching turns "the evidence module is empty" into "the evidence module is
complete and instant".

Two tables rather than one:

* `PubMedPaper` is keyed by PMID globally. The same paper legitimately answers
  several molecules (a combination trial, a class meta-analysis), and storing it
  once keeps a single copy of the abstract.
* `PubMedQuery` records one molecule/indication search: the true total PubMed
  reports, which PMIDs matched, and how far the fetch got. Keeping the total
  separate from the fetched rows is what lets the UI say "2,412 papers indexed,
  1,000 loaded" instead of implying the first page is everything.
"""
from __future__ import annotations

from sqlalchemy import Column, Float, Index, Integer, String, Text

from .database import Base


class PubMedPaperORM(Base):
    """One PubMed record, stored once regardless of how many molecules cite it."""

    __tablename__ = "pubmed_papers"

    pmid = Column(String, primary_key=True, index=True)
    pmcid = Column(String, nullable=True)
    doi = Column(String, nullable=True)
    title = Column(Text, nullable=False)
    authors_json = Column(Text, nullable=True)      # JSON list, full author list
    journal = Column(String, nullable=True)
    publication_year = Column(Integer, nullable=True)   # NULL, never a guessed year
    publication_date = Column(String, nullable=True)    # source wording, verbatim
    pub_types_json = Column(Text, nullable=True)    # JSON list of PubMed pubtypes
    study_type = Column(String, nullable=True)
    evidence_level = Column(String, nullable=True)
    abstract = Column(Text, nullable=True)
    fetched_at = Column(String, nullable=False)


class PubMedQueryORM(Base):
    """One molecule/indication search and how completely it has been fetched."""

    __tablename__ = "pubmed_queries"

    id = Column(String, primary_key=True, index=True)   # hash of molecule|indication
    molecule = Column(String, nullable=False, index=True)
    molecule_key = Column(String, nullable=False, index=True)
    indication = Column(String, nullable=True)
    query_string = Column(Text, nullable=False)
    # What PubMed says exists, independent of how much has been pulled down.
    total_available = Column(Integer, nullable=False, default=0)
    fetched_count = Column(Integer, nullable=False, default=0)
    pmids_json = Column(Text, nullable=True)        # ordered JSON list, newest first
    complete = Column(Integer, nullable=False, default=0)
    status = Column(String, nullable=False, default="ready")   # ready | fetching | error
    message = Column(Text, nullable=True)
    fetched_at = Column(String, nullable=False)


Index("ix_pubmed_papers_year", PubMedPaperORM.publication_year)
