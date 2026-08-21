"""Drug Intelligence endpoints.

Mounted alongside the existing routers and protected by the same
`require_access` dependency, so no new authentication surface is introduced.
"""
from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, Body, HTTPException, Path, Query, status

from ..data_sources.manual_source import ManualImportSource
from ..models.drug import (
    DrugComparison,
    DrugOut,
    DrugPage,
    DrugSearchResult,
    InteractionOut,
    InteractionReport,
    ManualDrugIn,
    PMTAnalysis,
    RefreshReport,
    RefreshRequest,
    DrugSourceOut,
)
from ..repositories import drug_repository as repo
from ..services import drug_compare_service, drug_ingestion_service, drug_pmt_service
from ..services import drug_search_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/drugs", tags=["Drug Intelligence"])

MAX_PAGE_SIZE = 100


@router.get("", response_model=DrugPage)
async def list_drugs(
    page: int = Query(1, ge=1, description="1-indexed page number"),
    page_size: int = Query(25, ge=1, le=MAX_PAGE_SIZE),
    drug_class: Optional[str] = Query(None, max_length=200, description="Filter by drug or therapeutic class"),
):
    """Paginated list of every ingested drug."""
    items, total = repo.list_drugs(page=page, page_size=page_size, drug_class=drug_class)
    return DrugPage(
        items=items, total=total, page=page, page_size=page_size,
        has_more=(page * page_size) < total,
    )


@router.get("/search", response_model=DrugSearchResult)
async def search_drugs(
    q: str = Query(..., min_length=1, max_length=200, description="Brand, generic, ingredient, class, strength, or form"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=MAX_PAGE_SIZE),
    ingest_if_missing: bool = Query(True, description="Fetch from permitted sources when nothing is cached"),
):
    """Search the cache, falling back to on-demand ingestion."""
    return await drug_search_service.search(
        q, page=page, page_size=page_size, ingest_if_missing=ingest_if_missing
    )


@router.get("/by-brand/{brand_name}", response_model=List[DrugOut])
async def drugs_by_brand(brand_name: str = Path(..., min_length=1, max_length=200)):
    rows = repo.find_by_name(brand_name, field="brand")
    if not rows:
        await drug_ingestion_service.ensure_ingested(brand_name)
        rows = repo.find_by_name(brand_name, field="brand")
    return rows


@router.get("/by-generic/{generic_name}", response_model=List[DrugOut])
async def drugs_by_generic(generic_name: str = Path(..., min_length=1, max_length=200)):
    rows = repo.find_by_name(generic_name, field="generic")
    if not rows:
        await drug_ingestion_service.ensure_ingested(generic_name)
        rows = repo.find_by_name(generic_name, field="generic")
    return rows


@router.get("/class/{drug_class}", response_model=DrugPage)
async def drugs_by_class(
    drug_class: str = Path(..., min_length=1, max_length=200),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=MAX_PAGE_SIZE),
):
    items, total = repo.list_drugs(page=page, page_size=page_size, drug_class=drug_class)
    return DrugPage(
        items=items, total=total, page=page, page_size=page_size,
        has_more=(page * page_size) < total,
    )


@router.post("/compare", response_model=DrugComparison)
async def compare_drugs(
    drug_a: str = Body(..., embed=True, min_length=1, max_length=200),
    drug_b: str = Body(..., embed=True, min_length=1, max_length=200),
    ingest_if_missing: bool = Body(True, embed=True),
):
    """Side-by-side comparison of two drugs."""
    return await drug_compare_service.compare(drug_a, drug_b, ingest_if_missing=ingest_if_missing)


@router.get("/sources/registry")
async def source_registry():
    """Which adapters exist, whether each is enabled, and its access policy."""
    return {
        "sources": drug_ingestion_service.available_sources(),
        "policy": (
            "Drug facts are ingested only from sources that permit programmatic "
            "access. Drugs.com is implemented as a licensed-feed adapter and stays "
            "disabled without a licence key; the site is never scraped."
        ),
    }


@router.post("/manual", response_model=DrugOut, status_code=status.HTTP_201_CREATED)
async def add_manual_drug(payload: ManualDrugIn):
    """Add a drug record by hand, stamped as user-entered."""
    try:
        record = ManualImportSource.to_record(
            payload.model_dump(exclude={"source_note", "entered_by"}, exclude_none=True),
            source_note=payload.source_note,
            entered_by=payload.entered_by,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    drug_id = repo.upsert_drug(record)
    stored = repo.get_drug(drug_id)
    if not stored:
        raise HTTPException(status_code=500, detail="Record was not persisted.")
    return stored


@router.post("/refresh", response_model=RefreshReport)
async def refresh_drugs(payload: RefreshRequest):
    """Re-ingest the named queries from the permitted sources.

    Administrative: it drives outbound requests, so it sits behind the same
    access token as everything else and caps the batch size to keep one call
    from hammering upstream APIs.
    """
    outcomes = []
    for query in payload.queries[:25]:
        outcomes.extend(await drug_ingestion_service.ingest_query(query, payload.sources))
    return RefreshReport(
        outcomes=outcomes,
        total_records_written=sum(o.records_written for o in outcomes),
        sources_available=drug_ingestion_service.available_sources(),
    )


@router.get("/refresh/history")
async def refresh_history(limit: int = Query(25, ge=1, le=200)):
    """Recent ingestion attempts, so a silently failing source is visible."""
    return {"entries": repo.recent_ingestions(limit)}


@router.get("/pmt/{molecule}", response_model=PMTAnalysis)
async def pmt_analysis(
    molecule: str = Path(..., min_length=1, max_length=200),
    competitors: Optional[str] = Query(None, description="Comma-separated competitor names"),
):
    """Software-generated strategic reading. Labelled as analysis, not source fact."""
    names = [c.strip() for c in (competitors or "").split(",") if c.strip()]
    return await drug_pmt_service.build_analysis(molecule, names)


# Dynamic single-segment routes are declared last so they cannot shadow the
# literal paths above ("/search", "/compare", "/manual", "/refresh").

@router.get("/{drug_id}", response_model=DrugOut)
async def get_drug(drug_id: str = Path(..., min_length=1, max_length=64)):
    record = repo.get_drug(drug_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"No drug found with id '{drug_id}'.")
    return record


@router.get("/{drug_id}/sources", response_model=List[DrugSourceOut])
async def get_drug_sources(drug_id: str = Path(..., min_length=1, max_length=64)):
    record = repo.get_drug(drug_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"No drug found with id '{drug_id}'.")
    return record.get("sources", [])


@router.get("/{drug_id}/interactions", response_model=InteractionReport)
async def get_drug_interactions(drug_id: str = Path(..., min_length=1, max_length=64)):
    record = repo.get_drug(drug_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"No drug found with id '{drug_id}'.")

    name = record.get("generic_name") or ""
    rows = repo.interactions_for(name)
    if rows:
        note = f"{len(rows)} pairwise interaction(s) recorded for {name}."
    else:
        note = (
            f"No structured pairwise interactions are stored for {name}. The label's "
            "own interactions narrative is on the drug record under 'drug_interactions'. "
            "Structured pairs require a licensed interaction feed."
        )
    return InteractionReport(
        drug=name, interactions=rows, total=len(rows), coverage_note=note
    )
