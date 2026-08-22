"""Market intelligence endpoints backed by ingested secondary data.

Everything here reads from files a brand team supplied. There is no upstream to
call and nothing is inferred: if a molecule is absent from every ingested
dataset, these endpoints return an empty set with `has_data: false` rather than
a plausible-looking guess, because share and growth figures drive launch
decisions and an invented one is worse than a blank.
"""
import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..services import market_data_service as market

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/market", tags=["Market Intelligence"])


class IngestPathRequest(BaseModel):
    path: str = Field(..., description="Absolute path to an .xlsx/.csv market extract")
    source_label: str = Field("Secondary data", description="How to credit this source in the UI")
    market: str = Field("India", description="Geography the extract covers")
    value_unit: str = Field("INR Cr", description="Unit of the value columns")
    project_id: Optional[str] = None


@router.get("/datasets")
async def get_datasets() -> List[Dict[str, Any]]:
    """Every ingested secondary-data file, newest first."""
    return market.list_datasets()


@router.post("/ingest/path")
async def ingest_from_path(request: IngestPathRequest) -> Dict[str, Any]:
    """Ingest an extract already on the server's filesystem.

    The upload endpoint covers files a user drags in; this covers the large
    base extracts that are impractical to push through a browser.
    """
    path = os.path.expanduser(request.path)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"No file at {path}")
    try:
        return market.ingest_market_file(
            path,
            source_label=request.source_label,
            market=request.market,
            value_unit=request.value_unit,
            project_id=request.project_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Ingest failed for %s", path)
        raise HTTPException(status_code=500, detail="Could not parse that extract.") from exc


@router.delete("/datasets/{dataset_id}")
async def remove_dataset(dataset_id: str) -> Dict[str, Any]:
    removed = market.delete_dataset(dataset_id)
    return {"dataset_id": dataset_id, "rows_removed": removed}


@router.get("/molecule")
async def molecule_market(
    molecule: str = Query(..., description="Molecule/INN to look up"),
) -> Dict[str, Any]:
    """Market size, brand table, company share, and class rivals in one call."""
    return market.molecule_overview(molecule)


@router.get("/brands")
async def molecule_brands(
    molecule: str = Query(...),
    limit: int = Query(40, ge=1, le=500),
) -> Dict[str, Any]:
    """Every marketed brand of a molecule, aggregated from pack rows."""
    return market.brand_competitors(molecule, limit=limit)


@router.get("/companies")
async def molecule_companies(
    molecule: str = Query(...),
    limit: int = Query(15, ge=1, le=100),
) -> List[Dict[str, Any]]:
    """Corporate share of a molecule's market."""
    return market.company_leaderboard(molecule, limit=limit)


@router.get("/class")
async def molecule_class(
    molecule: str = Query(...),
    limit: int = Query(12, ge=1, le=50),
) -> Dict[str, Any]:
    """Rival molecules sold into the same therapeutic group."""
    return market.class_competitors(molecule, limit=limit)


@router.get("/search")
async def search(
    q: str = Query(..., min_length=2, description="Brand, molecule, or company"),
    limit: int = Query(30, ge=1, le=200),
) -> List[Dict[str, Any]]:
    """Free-text lookup across every ingested extract."""
    return market.search_brands(q, limit=limit)


class ManualCompetitorRequest(BaseModel):
    molecule: str = Field(..., min_length=1, max_length=200,
                          description="Molecule/INN this competitor is for")
    brand: str = Field(..., min_length=1, max_length=160, description="Competitor brand name")
    source_note: str = Field(..., min_length=3, max_length=1000, description=(
        "Where this fact comes from — mandatory. An entry with no stated "
        "source is indistinguishable from a guess."))
    added_by: str = Field(..., min_length=1, max_length=120, description="Who is attesting to this")
    company: Optional[str] = Field(None, max_length=160)
    market: Optional[str] = Field(None, max_length=80)
    value_estimate: Optional[float] = Field(None, ge=0, le=1_000_000_000)
    value_unit: Optional[str] = Field(None, max_length=20)
    value_basis: Optional[str] = Field(
        None, max_length=500, description="How the value was arrived at, if one is given")


@router.get("/competitors/manual")
async def get_manual_competitors(
    molecule: str = Query(..., description="Molecule/INN to look up"),
) -> List[Dict[str, Any]]:
    """Every team-attested competitor on file for a molecule."""
    return market.list_manual_competitors(molecule)


@router.post("/competitors/manual")
async def add_manual_competitor_endpoint(request: ManualCompetitorRequest) -> Dict[str, Any]:
    """Record a competitor a licensed extract doesn't cover.

    For a brand a team knows is real and marketed but which is newer than the
    loaded extract's period, or in a market no extract has ever been loaded
    for. Never merged into the licensed market-size numbers — always shown
    with its own source and who added it.
    """
    try:
        return market.add_manual_competitor(
            molecule=request.molecule,
            brand=request.brand,
            source_note=request.source_note,
            added_by=request.added_by,
            company=request.company,
            market=request.market,
            value_estimate=request.value_estimate,
            value_unit=request.value_unit,
            value_basis=request.value_basis,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.delete("/competitors/manual/{entry_id}")
async def remove_manual_competitor(entry_id: str) -> Dict[str, Any]:
    removed = market.delete_manual_competitor(entry_id)
    if not removed:
        raise HTTPException(status_code=404, detail="No manual competitor entry with that id.")
    return {"deleted": entry_id}
