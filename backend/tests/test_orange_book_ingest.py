"""Tests for Orange Book persistence.

Network-free: a synthetic tilde-delimited archive is passed in directly, so no
download and no dependency on the cached zip.
"""
import io
import zipfile

import pytest

from app.db.database import SessionLocal, init_db
from app.db.orange_book_models import (
    OrangeBookExclusivityORM,
    OrangeBookPatentORM,
    OrangeBookProductORM,
)
from app.services import orange_book_ingest as ob

init_db()

PRODUCTS = (
    "Ingredient~DF;Route~Trade_Name~Applicant~Strength~Appl_Type~Appl_No~Product_No~"
    "TE_Code~Approval_Date~RLD~RS~Type~Applicant_Full_Name\n"
    "APIXABAN~TABLET;ORAL~ELIQUIS~BRISTOL~2.5MG~N~202155~001~AB~Dec 28, 2012~Yes~Yes~RX~"
    "BRISTOL MYERS SQUIBB\n"
)
PATENTS = (
    "Appl_Type~Appl_No~Product_No~Patent_No~Patent_Expire_Date_Text~Drug_Substance_Flag~"
    "Drug_Product_Flag~Patent_Use_Code~Delist_Flag~Submission_Date\n"
    "N~202155~001~6967208~Feb 23, 2027~Y~~U-1234~~Jan 1, 2013\n"
    "N~202155~001~9326945~Not a date~~Y~U-9~~Jan 1, 2016\n"
)
EXCLUSIVITY = (
    "Appl_Type~Appl_No~Product_No~Exclusivity_Code~Exclusivity_Date\n"
    "N~202155~001~NCE~Dec 28, 2017\n"
)


def _archive(products=PRODUCTS, patents=PATENTS, exclusivity=EXCLUSIVITY) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("products.txt", products)
        z.writestr("patent.txt", patents)
        z.writestr("exclusivity.txt", exclusivity)
    return buf.getvalue()


def _clean():
    s = SessionLocal()
    for m in (OrangeBookProductORM, OrangeBookPatentORM, OrangeBookExclusivityORM):
        s.query(m).delete()
    s.commit(); s.close()


def test_loads_all_three_files():
    _clean()
    result = ob.ingest(_archive())
    assert (result.products, result.patents, result.exclusivity) == (1, 2, 1)
    assert result.failed == 0


def test_product_fields_and_te_code():
    _clean(); ob.ingest(_archive())
    s = SessionLocal()
    p = s.query(OrangeBookProductORM).one()
    assert p.ingredient == "APIXABAN"
    assert p.trade_name == "ELIQUIS"
    assert p.te_code == "AB"
    assert p.rld == "Yes"
    assert p.dosage_form_route == "TABLET;ORAL"
    assert p.approval_date_iso == "2012-12-28"
    s.close()


def test_patent_expiry_is_normalised_for_sorting():
    """The ISO column is what a loss-of-exclusivity query orders on."""
    _clean(); ob.ingest(_archive())
    s = SessionLocal()
    p = s.query(OrangeBookPatentORM).filter_by(patent_no="6967208").one()
    assert p.patent_expire_date == "Feb 23, 2027"
    assert p.patent_expire_date_iso == "2027-02-23"
    s.close()


def test_unparseable_date_keeps_original_and_nulls_iso():
    """A wrong expiry silently shifts an LOE forecast - absent is safer."""
    _clean(); result = ob.ingest(_archive())
    s = SessionLocal()
    p = s.query(OrangeBookPatentORM).filter_by(patent_no="9326945").one()
    assert p.patent_expire_date == "Not a date"
    assert p.patent_expire_date_iso is None
    s.close()
    assert result.unparsed_dates == 1


def test_legacy_approval_sentinel_is_not_an_unparsed_date():
    """'Approved Prior to Jan 1, 1982' is a real FDA value, not a bad date.

    Counting it as a parse failure inflates the warning to thousands of rows
    and trains people to ignore a signal that should mean something.
    """
    _clean()
    products = PRODUCTS + (
        "DIGOXIN~TABLET;ORAL~LANOXIN~CONCORDIA~250MCG~N~009330~001~AB~"
        "Approved Prior to Jan 1, 1982~Yes~Yes~RX~CONCORDIA\n"
    )
    result = ob.ingest(_archive(products=products))
    assert result.legacy_approvals == 1
    assert result.unparsed_dates == 1          # only the bad patent date
    s = SessionLocal()
    row = s.query(OrangeBookProductORM).filter_by(trade_name="LANOXIN").one()
    assert row.approval_date == "Approved Prior to Jan 1, 1982"
    assert row.approval_date_iso is None
    s.close()


def test_reingesting_updates_rather_than_duplicating():
    _clean()
    ob.ingest(_archive()); ob.ingest(_archive())
    s = SessionLocal()
    assert s.query(OrangeBookProductORM).count() == 1
    assert s.query(OrangeBookPatentORM).count() == 2
    assert s.query(OrangeBookExclusivityORM).count() == 1
    s.close()


def test_missing_file_in_archive_is_tolerated():
    _clean()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("products.txt", PRODUCTS)
    result = ob.ingest(buf.getvalue())
    assert result.products == 1
    assert result.patents == 0


def test_same_patent_under_two_use_codes_is_kept_separately():
    """One patent listed per covered indication must not collapse to one row.

    FDA repeats a patent against a product once per Patent_Use_Code. Keying
    without the use code silently dropped 4,635 rows from the real file, losing
    the per-indication detail skinny-label strategy depends on.
    """
    _clean()
    patents = (
        "Appl_Type~Appl_No~Product_No~Patent_No~Patent_Expire_Date_Text~Drug_Substance_Flag~"
        "Drug_Product_Flag~Patent_Use_Code~Delist_Flag~Submission_Date\n"
        "N~021695~001~9314447~May 31, 2033~~Y~U-1447~~Jan 1, 2020\n"
        "N~021695~001~9314447~May 31, 2033~~Y~U-1448~~Jan 1, 2020\n"
    )
    result = ob.ingest(_archive(patents=patents))
    assert result.patents == 2
    s = SessionLocal()
    assert s.query(OrangeBookPatentORM).count() == 2
    assert {r.patent_use_code for r in s.query(OrangeBookPatentORM).all()} == {"U-1447", "U-1448"}
    s.close()


def test_exclusivity_same_code_different_dates_kept():
    _clean()
    excl = (
        "Appl_Type~Appl_No~Product_No~Exclusivity_Code~Exclusivity_Date\n"
        "N~202155~001~NCE~Dec 28, 2017\n"
        "N~202155~001~NCE~Mar 15, 2019\n"
    )
    ob.ingest(_archive(exclusivity=excl))
    s = SessionLocal()
    assert s.query(OrangeBookExclusivityORM).count() == 2
    s.close()


def test_absent_archive_raises():
    with pytest.raises(ob.OrangeBookUnavailable):
        ob.ingest(b"")


def test_one_bad_row_does_not_abort_the_rest():
    """A failing row must roll back only itself.

    On PostgreSQL a failed statement invalidates the whole transaction, so
    without the per-row SAVEPOINT every subsequent write would fail while the
    counters still reported success. Asserting the later rows land is what
    pins that.
    """
    _clean()
    products = (
        "Ingredient~DF;Route~Trade_Name~Applicant~Strength~Appl_Type~Appl_No~Product_No~"
        "TE_Code~Approval_Date~RLD~RS~Type~Applicant_Full_Name\n"
        "GOOD ONE~TABLET;ORAL~FIRST~X~1MG~N~111111~001~AB~Jan 1, 2001~Yes~Yes~RX~X\n"
        "BAD~TABLET;ORAL~SECOND~X~1MG~N~222222~001~AB~Jan 1, 2002~Yes~Yes~RX~X\n"
        "GOOD TWO~TABLET;ORAL~THIRD~X~1MG~N~333333~001~AB~Jan 1, 2003~Yes~Yes~RX~X\n"
    )
    real_key = ob._key

    def exploding_key(*parts):
        if "222222" in [str(p) for p in parts]:
            raise RuntimeError("simulated write failure")
        return real_key(*parts)

    ob._key = exploding_key
    try:
        result = ob.ingest(_archive(products=products, patents="", exclusivity=""))
    finally:
        ob._key = real_key

    assert result.failed == 1
    assert result.products == 2
    s = SessionLocal()
    names = {r.trade_name for r in s.query(OrangeBookProductORM).all()}
    s.close()
    # THIRD is the one that proves the transaction survived the failure.
    assert names == {"FIRST", "THIRD"}


def test_rows_are_written_inside_savepoints():
    """Assert the SAVEPOINT is actually emitted, not just that rows land.

    The behavioural test above cannot pin this: SQLite does not invalidate a
    transaction on a failed statement, so it passes whether or not the
    savepoint exists. Only PostgreSQL would show the difference, and the suite
    does not run against it. So this checks the mechanism directly — SQLAlchemy
    emits SAVEPOINT for begin_nested() on every backend, including SQLite.
    """
    from sqlalchemy import event

    from app.db.database import engine

    statements = []

    def record(conn, cursor, statement, params, context, executemany):
        statements.append(statement)

    _clean()
    event.listen(engine, "before_cursor_execute", record)
    try:
        ob.ingest(_archive())
    finally:
        event.remove(engine, "before_cursor_execute", record)

    savepoints = [s for s in statements if s.strip().upper().startswith("SAVEPOINT")]
    # One per row written: 1 product + 2 patents + 1 exclusivity.
    assert len(savepoints) == 4, f"expected 4 SAVEPOINTs, saw {len(savepoints)}"


def test_a_database_error_rolls_back_only_its_own_row():
    """The real failure mode: an error raised by the DATABASE, not by Python.

    merge() only stages a row; the INSERT is emitted at flush. An earlier
    version of this fix wrapped merge() alone, so the failing statement landed
    outside the savepoint and would still have poisoned a PostgreSQL
    transaction. Forcing a NOT NULL violation reproduces a genuine driver-level
    error, which a pure-Python exception does not.
    """
    from sqlalchemy import event

    from app.db.database import engine

    products = (
        "Ingredient~DF;Route~Trade_Name~Applicant~Strength~Appl_Type~Appl_No~Product_No~"
        "TE_Code~Approval_Date~RLD~RS~Type~Applicant_Full_Name\n"
        "GOOD ONE~TABLET;ORAL~FIRST~X~1MG~N~111111~001~AB~Jan 1, 2001~Yes~Yes~RX~X\n"
        "BAD~TABLET;ORAL~SECOND~X~1MG~N~222222~001~AB~Jan 1, 2002~Yes~Yes~RX~X\n"
        "GOOD TWO~TABLET;ORAL~THIRD~X~1MG~N~333333~001~AB~Jan 1, 2003~Yes~Yes~RX~X\n"
    )
    real_key = ob._key

    def null_pk_for_the_bad_row(*parts):
        if "222222" in [str(p) for p in parts]:
            return None          # NOT NULL primary key -> driver-level IntegrityError
        return real_key(*parts)

    statements = []

    def record(conn, cursor, statement, params, context, executemany):
        statements.append(statement.strip().upper())

    _clean()
    ob._key = null_pk_for_the_bad_row
    event.listen(engine, "before_cursor_execute", record)
    try:
        result = ob.ingest(_archive(products=products, patents="", exclusivity=""))
    finally:
        event.remove(engine, "before_cursor_execute", record)
        ob._key = real_key

    assert result.failed == 1
    assert result.products == 2
    s = SessionLocal()
    names = {r.trade_name for r in s.query(OrangeBookProductORM).all()}
    s.close()
    # THIRD proves the transaction stayed usable after a real driver error.
    assert names == {"FIRST", "THIRD"}
    assert any(st.startswith("ROLLBACK TO SAVEPOINT") for st in statements), \
        "the failing row must roll its own savepoint back"
