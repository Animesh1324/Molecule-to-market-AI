"""Persist FDA's Orange Book zip into queryable tables.

Reuses `orange_book._load_archive()` so the download, caching and monthly
refresh logic stays in one place; this module only parses and writes.

Deliberately sources FDA's own zip rather than openFDA's `orangebook` dataset:
openFDA carries neither patent.txt nor exclusivity.txt, stopping at therapeutic
equivalence codes, so it cannot answer the question this table exists for.
"""
from __future__ import annotations

import csv
import hashlib
import io
import logging
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from ..db.database import SessionLocal
from ..db.orange_book_models import (
    OrangeBookExclusivityORM,
    OrangeBookPatentORM,
    OrangeBookProductORM,
)
from .orange_book import _load_archive

logger = logging.getLogger(__name__)

BATCH = 500


class OrangeBookUnavailable(RuntimeError):
    """The Orange Book archive could not be loaded."""


def _key(*parts: Any) -> str:
    return hashlib.sha1("|".join("" if p is None else str(p) for p in parts).encode()).hexdigest()


# FDA writes this literal string for products approved before the Orange Book
# began. It is a real value, not a malformed date, so it must not inflate the
# unparsed-date count and train people to ignore that warning.
LEGACY_APPROVAL = "approved prior to jan 1, 1982"


def _iso(text: Optional[str]) -> Optional[str]:
    """FDA writes dates as 'Aug 24, 2026'. Return ISO, or None if unparseable.

    None rather than a fallback date: a wrong expiry silently shifts a
    loss-of-exclusivity forecast, so an absent one is far safer.
    """
    text = (text or "").strip()
    if not text:
        return None
    for fmt in ("%b %d, %Y", "%B %d, %Y", "%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(text, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def _is_sentinel(text: Optional[str]) -> bool:
    return " ".join((text or "").split()).lower() == LEGACY_APPROVAL


def _clean(value: Optional[str], limit: int = 500) -> Optional[str]:
    value = " ".join((value or "").split())
    return value[:limit] or None


@dataclass
class OrangeBookResult:
    products: int = 0
    patents: int = 0
    exclusivity: int = 0
    unparsed_dates: int = 0
    legacy_approvals: int = 0
    failed: int = 0

    def as_dict(self) -> Dict[str, int]:
        return {"products": self.products, "patents": self.patents,
                "exclusivity": self.exclusivity,
                "unparsed_dates": self.unparsed_dates,
                "legacy_approvals": self.legacy_approvals, "failed": self.failed}


def _rows(archive: zipfile.ZipFile, filename: str) -> List[dict]:
    raw = archive.read(filename).decode("utf-8", "replace").splitlines()
    return list(csv.DictReader(raw, delimiter="~"))


def ingest(archive_bytes: Optional[bytes] = None,
           progress: Optional[Callable[[OrangeBookResult], None]] = None) -> OrangeBookResult:
    """Load products, patents and exclusivity into their tables.

    Rows key on (appl_type, appl_no, product_no[, patent_no|code]), so
    re-running after FDA's monthly refresh updates rather than duplicating.
    """
    data = archive_bytes if archive_bytes is not None else _load_archive()
    if not data:
        raise OrangeBookUnavailable("Orange Book archive unavailable")

    result = OrangeBookResult()
    session = SessionLocal()
    pending = 0
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            names = set(archive.namelist())

            for row in _rows(archive, "products.txt") if "products.txt" in names else []:
                try:
                    appl_no, prod_no = row.get("Appl_No"), row.get("Product_No")
                    approval = row.get("Approval_Date")
                    iso = _iso(approval)
                    if _is_sentinel(approval):
                        result.legacy_approvals += 1
                    if approval and not iso and not _is_sentinel(approval):
                        result.unparsed_dates += 1
                    session.merge(OrangeBookProductORM(
                        id=_key(row.get("Appl_Type"), appl_no, prod_no),
                        appl_type=_clean(row.get("Appl_Type"), 10),
                        appl_no=_clean(appl_no, 20) or "",
                        product_no=_clean(prod_no, 20),
                        ingredient=_clean(row.get("Ingredient"), 400),
                        trade_name=_clean(row.get("Trade_Name"), 300),
                        applicant=_clean(row.get("Applicant"), 300),
                        applicant_full_name=_clean(row.get("Applicant_Full_Name"), 400),
                        strength=_clean(row.get("Strength"), 1000),
                        dosage_form_route=_clean(row.get("DF;Route"), 300),
                        te_code=_clean(row.get("TE_Code"), 20),
                        approval_date=_clean(approval, 50),
                        approval_date_iso=iso,
                        rld=_clean(row.get("RLD"), 10),
                        rs=_clean(row.get("RS"), 10),
                        marketing_type=_clean(row.get("Type"), 30),
                    ))
                    result.products += 1
                    pending += 1
                except Exception:  # noqa: BLE001
                    result.failed += 1
                if pending >= BATCH:
                    session.commit(); pending = 0
                    if progress: progress(result)

            for row in _rows(archive, "patent.txt") if "patent.txt" in names else []:
                try:
                    expire = row.get("Patent_Expire_Date_Text")
                    iso = _iso(expire)
                    if expire and not iso:
                        result.unparsed_dates += 1
                    session.merge(OrangeBookPatentORM(
                        # Use code belongs in the key: FDA lists one patent
                        # against a product once per covered indication, and
                        # those rows differ only by Patent_Use_Code. Dropping it
                        # collapsed 4,635 rows and with them the per-indication
                        # detail that skinny-label carve-outs turn on.
                        id=_key(row.get("Appl_Type"), row.get("Appl_No"),
                                row.get("Product_No"), row.get("Patent_No"),
                                row.get("Patent_Use_Code")),
                        appl_type=_clean(row.get("Appl_Type"), 10),
                        appl_no=_clean(row.get("Appl_No"), 20) or "",
                        product_no=_clean(row.get("Product_No"), 20),
                        patent_no=_clean(row.get("Patent_No"), 40),
                        patent_expire_date=_clean(expire, 50),
                        patent_expire_date_iso=iso,
                        drug_substance_flag=_clean(row.get("Drug_Substance_Flag"), 10),
                        drug_product_flag=_clean(row.get("Drug_Product_Flag"), 10),
                        patent_use_code=_clean(row.get("Patent_Use_Code"), 40),
                        delist_flag=_clean(row.get("Delist_Flag"), 10),
                        submission_date=_clean(row.get("Submission_Date"), 50),
                    ))
                    result.patents += 1
                    pending += 1
                except Exception:  # noqa: BLE001
                    result.failed += 1
                if pending >= BATCH:
                    session.commit(); pending = 0
                    if progress: progress(result)

            for row in _rows(archive, "exclusivity.txt") if "exclusivity.txt" in names else []:
                try:
                    date = row.get("Exclusivity_Date")
                    iso = _iso(date)
                    if date and not iso:
                        result.unparsed_dates += 1
                    session.merge(OrangeBookExclusivityORM(
                        # Date included: one product can carry the same
                        # exclusivity code with different expiry dates. Rows
                        # identical across all five fields are true duplicates
                        # in FDA's file and do collapse, correctly.
                        id=_key(row.get("Appl_Type"), row.get("Appl_No"),
                                row.get("Product_No"), row.get("Exclusivity_Code"),
                                row.get("Exclusivity_Date")),
                        appl_type=_clean(row.get("Appl_Type"), 10),
                        appl_no=_clean(row.get("Appl_No"), 20) or "",
                        product_no=_clean(row.get("Product_No"), 20),
                        exclusivity_code=_clean(row.get("Exclusivity_Code"), 40),
                        exclusivity_date=_clean(date, 50),
                        exclusivity_date_iso=iso,
                    ))
                    result.exclusivity += 1
                    pending += 1
                except Exception:  # noqa: BLE001
                    result.failed += 1
                if pending >= BATCH:
                    session.commit(); pending = 0
                    if progress: progress(result)

        session.commit()
        return result
    finally:
        session.close()
