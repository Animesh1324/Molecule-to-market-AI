"""FDA Orange Book: patents, exclusivity, and every marketed product per molecule.

The Orange Book is the authoritative public record of which company holds the
innovator application, when each listed patent expires, and which generic
filers have been approved with what trade names. FDA publishes it as a zip of
tilde-delimited files rather than an API, so it is downloaded once and cached.

This is the source behind "who is the innovator", "when does the patent
expire", and "who entered after expiry" — all of which are otherwise manual
lookups on the FDA site.
"""
import csv
import io
import logging
import os
import threading
import time
import zipfile
from datetime import datetime
from typing import Dict, List, Optional

import httpx

from .inn_synonyms import candidates as name_candidates

logger = logging.getLogger(__name__)

ORANGE_BOOK_URL = "https://www.fda.gov/media/76860/download?attachment"

_CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "orange_book")
_CACHE_FILE = os.path.join(_CACHE_DIR, "orange_book.zip")
_MAX_AGE_SECONDS = 30 * 24 * 3600  # FDA refreshes monthly.

# Exclusivity codes carry real commercial meaning; spell out the common ones.
EXCLUSIVITY_CODES: Dict[str, str] = {
    "NCE": "New Chemical Entity (5-year)",
    "NP": "New Product (3-year)",
    "NDF": "New Dosage Form",
    "NS": "New Strength",
    "NC": "New Combination",
    "NI": "New Indication",
    "NE": "New Ester/Salt",
    "ODE": "Orphan Drug Exclusivity (7-year)",
    "PED": "Pediatric Exclusivity (6-month add-on)",
    "PC": "Patent Challenge",
    "GAIN": "Qualified Infectious Disease Product (5-year add-on)",
    "M": "Miscellaneous",
    "RTO": "Reference to Other",
    "I": "Indication",
    "D": "Delayed",
}

_lock = threading.Lock()
_index: Optional[Dict[str, object]] = None
_index_built_at: float = 0.0


def _download(timeout: float = 90.0) -> Optional[bytes]:
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            response = client.get(ORANGE_BOOK_URL)
            if response.status_code != 200:
                logger.warning("Orange Book download returned HTTP %s", response.status_code)
                return None
            return response.content
    except Exception as exc:
        logger.warning("Orange Book download failed: %s", exc)
        return None


def _load_archive() -> Optional[bytes]:
    """Return the zip bytes, refreshing the on-disk cache when stale."""
    os.makedirs(_CACHE_DIR, exist_ok=True)
    fresh = (
        os.path.exists(_CACHE_FILE)
        and (time.time() - os.path.getmtime(_CACHE_FILE)) < _MAX_AGE_SECONDS
    )
    if fresh:
        try:
            with open(_CACHE_FILE, "rb") as handle:
                return handle.read()
        except OSError:
            pass

    payload = _download()
    if payload:
        try:
            with open(_CACHE_FILE, "wb") as handle:
                handle.write(payload)
        except OSError as exc:
            logger.warning("Could not cache Orange Book: %s", exc)
        return payload

    # Download failed — fall back to a stale cache rather than losing the data.
    if os.path.exists(_CACHE_FILE):
        logger.info("Using stale Orange Book cache after failed refresh")
        with open(_CACHE_FILE, "rb") as handle:
            return handle.read()
    return None


def _rows(archive: zipfile.ZipFile, filename: str) -> List[dict]:
    try:
        raw = archive.read(filename).decode("utf-8", errors="replace")
    except KeyError:
        logger.warning("Orange Book archive missing %s", filename)
        return []
    return list(csv.DictReader(io.StringIO(raw), delimiter="~"))


def _index_from_tables() -> Optional[Dict[str, object]]:
    """Build the index from the persisted tables instead of re-parsing the zip.

    `orange_book_ingest` loads the same three files into
    orange_book_products/patents/exclusivity. Reading them here means one
    source of truth rather than two code paths over one file, removes the
    per-worker re-parse, and drops the runtime dependency on the zip being
    present on disk.

    Returns None — not an empty index — when the tables are absent or empty, so
    the caller falls back to the archive. A fresh deployment has the code but
    not yet the rows, and silently reporting "no patents" there would read as
    "off patent".

    Row dicts use the FDA column names the archive produced, because
    `products_for`/`patents_for` and Module 11 read those keys directly.
    """
    try:
        from ..db.database import SessionLocal
        from ..db.orange_book_models import (
            OrangeBookExclusivityORM,
            OrangeBookPatentORM,
            OrangeBookProductORM,
        )
    except Exception:  # noqa: BLE001 - models unavailable, use the archive
        return None

    session = SessionLocal()
    try:
        products = session.query(OrangeBookProductORM).all()
        if not products:
            return None
        patents = session.query(OrangeBookPatentORM).all()
        exclusivity = session.query(OrangeBookExclusivityORM).all()
    except Exception:  # noqa: BLE001 - table missing on an un-migrated database
        logger.debug("Orange Book tables unavailable; falling back to archive", exc_info=True)
        return None
    finally:
        session.close()

    products_by_ingredient: Dict[str, List[dict]] = {}
    for row in products:
        record = {
            "Ingredient": row.ingredient or "",
            "DF;Route": row.dosage_form_route or "",
            "Trade_Name": row.trade_name or "",
            "Applicant": row.applicant or "",
            "Applicant_Full_Name": row.applicant_full_name or "",
            "Strength": row.strength or "",
            "Appl_Type": row.appl_type or "",
            "Appl_No": row.appl_no or "",
            "Product_No": row.product_no or "",
            "TE_Code": row.te_code or "",
            "Approval_Date": row.approval_date or "",
            "RLD": row.rld or "",
            "RS": row.rs or "",
            "Type": row.marketing_type or "",
        }
        for ingredient in (row.ingredient or "").split(";"):
            key = ingredient.strip().lower()
            if key:
                products_by_ingredient.setdefault(key, []).append(record)

    patents_by_app: Dict[str, List[dict]] = {}
    for row in patents:
        patents_by_app.setdefault((row.appl_no or "").strip(), []).append({
            "Appl_Type": row.appl_type or "",
            "Appl_No": row.appl_no or "",
            "Product_No": row.product_no or "",
            "Patent_No": row.patent_no or "",
            "Patent_Expire_Date_Text": row.patent_expire_date or "",
            "Drug_Substance_Flag": row.drug_substance_flag or "",
            "Drug_Product_Flag": row.drug_product_flag or "",
            "Patent_Use_Code": row.patent_use_code or "",
            "Delist_Flag": row.delist_flag or "",
            "Submission_Date": row.submission_date or "",
        })

    exclusivity_by_app: Dict[str, List[dict]] = {}
    for row in exclusivity:
        exclusivity_by_app.setdefault((row.appl_no or "").strip(), []).append({
            "Appl_Type": row.appl_type or "",
            "Appl_No": row.appl_no or "",
            "Product_No": row.product_no or "",
            "Exclusivity_Code": row.exclusivity_code or "",
            "Exclusivity_Date": row.exclusivity_date or "",
        })

    logger.info(
        "Orange Book indexed from tables: %d ingredients, %d products, %d patent listings",
        len(products_by_ingredient), len(products), len(patents),
    )
    return {
        "products_by_ingredient": products_by_ingredient,
        "patents": patents_by_app,
        "exclusivity": exclusivity_by_app,
        "available": True,
        "source": "database",
    }


def _build_index() -> Dict[str, object]:
    """Parse the archive into lookup tables keyed for ingredient search.

    Prefers the persisted tables; falls back to the zip when they are empty,
    which is the state of a freshly deployed database before the loader runs.
    """
    from_tables = _index_from_tables()
    if from_tables is not None:
        return from_tables

    payload = _load_archive()
    if not payload:
        return {"products_by_ingredient": {}, "patents": {}, "exclusivity": {}, "available": False}

    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        products = _rows(archive, "products.txt")
        patents = _rows(archive, "patent.txt")
        exclusivity = _rows(archive, "exclusivity.txt")

    products_by_ingredient: Dict[str, List[dict]] = {}
    for row in products:
        for ingredient in (row.get("Ingredient") or "").split(";"):
            key = ingredient.strip().lower()
            if key:
                products_by_ingredient.setdefault(key, []).append(row)

    patents_by_app: Dict[str, List[dict]] = {}
    for row in patents:
        patents_by_app.setdefault((row.get("Appl_No") or "").strip(), []).append(row)

    exclusivity_by_app: Dict[str, List[dict]] = {}
    for row in exclusivity:
        exclusivity_by_app.setdefault((row.get("Appl_No") or "").strip(), []).append(row)

    logger.info(
        "Orange Book indexed: %d ingredients, %d products, %d patents",
        len(products_by_ingredient), len(products), len(patents),
    )
    return {
        "products_by_ingredient": products_by_ingredient,
        "patents": patents_by_app,
        "exclusivity": exclusivity_by_app,
        "available": True,
        "source": "archive",
    }


def get_index() -> Dict[str, object]:
    """Return the parsed index, building it on first use."""
    global _index, _index_built_at
    with _lock:
        stale = (time.time() - _index_built_at) > _MAX_AGE_SECONDS
        if _index is None or stale:
            _index = _build_index()
            _index_built_at = time.time()
        return _index


def products_for(ingredient: str) -> List[dict]:
    """Rows whose ingredient list contains this molecule.

    Tries every INN/USAN spelling and the salt-stripped moiety, because the
    Orange Book files under US names ("acetaminophen", "clavulanate") while a
    brand team types the INN ("paracetamol", "clavulanic acid").
    """
    index = get_index()
    table: Dict[str, List[dict]] = index["products_by_ingredient"]  # type: ignore[assignment]
    if not ingredient.strip():
        return []

    for key in name_candidates(ingredient):
        if key in table:
            return table[key]

    # No exact hit under any spelling: fall back to a contains match.
    for key in name_candidates(ingredient):
        matches: List[dict] = []
        for name, rows in table.items():
            if key in name or name in key:
                matches.extend(rows)
        if matches:
            return matches
    return []


def patents_for(application_number: str) -> List[dict]:
    return get_index()["patents"].get(application_number.strip(), [])  # type: ignore[union-attr]


def exclusivity_for(application_number: str) -> List[dict]:
    return get_index()["exclusivity"].get(application_number.strip(), [])  # type: ignore[union-attr]


def parse_date(value: Optional[str]) -> Optional[datetime]:
    """Orange Book dates look like 'Jun 11, 2034'; some rows say 'Approved Prior to Jan 1, 1982'."""
    if not value:
        return None
    text = value.strip()
    if not text or text.lower().startswith("approved prior"):
        return None
    for fmt in ("%b %d, %Y", "%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None
