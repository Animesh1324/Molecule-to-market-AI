"""Orange Book lookups read the persisted tables, with an archive fallback."""
from app.db.database import SessionLocal, init_db
from app.db.orange_book_models import OrangeBookPatentORM, OrangeBookProductORM
from app.services import orange_book as ob

init_db()


def _reset():
    ob._index = None
    ob._index_built_at = 0.0


def _clean():
    s = SessionLocal()
    s.query(OrangeBookProductORM).delete()
    s.query(OrangeBookPatentORM).delete()
    s.commit(); s.close()


def test_tables_are_preferred_when_populated():
    _clean()
    s = SessionLocal()
    s.add(OrangeBookProductORM(id="p1", appl_no="202155", ingredient="APIXABAN",
                               trade_name="ELIQUIS", te_code="AB", rld="Yes"))
    s.add(OrangeBookPatentORM(id="x1", appl_no="202155", patent_no="6967208",
                              patent_expire_date="Feb 23, 2027", patent_use_code="U-1"))
    s.commit(); s.close()
    _reset()

    assert ob.get_index().get("source") == "database"
    rows = ob.products_for("apixaban")
    assert len(rows) == 1
    # FDA column names are preserved: products_for callers and Module 11 read
    # these keys directly, so the shape is part of the contract.
    assert rows[0]["Trade_Name"] == "ELIQUIS"
    assert rows[0]["TE_Code"] == "AB"
    patents = ob.patents_for("202155")
    assert patents[0]["Patent_Expire_Date_Text"] == "Feb 23, 2027"
    assert patents[0]["Patent_Use_Code"] == "U-1"


def test_empty_tables_fall_back_to_the_archive(monkeypatch):
    """A fresh deployment has the code but not the rows.

    Returning an empty index there would report "no patents", which reads as
    "off patent" — the opposite of the truth.
    """
    _clean(); _reset()
    called = {"archive": False}

    def fake_archive():
        called["archive"] = True
        return None                      # no zip either; index just unavailable

    monkeypatch.setattr(ob, "_load_archive", fake_archive)
    index = ob.get_index()
    assert called["archive"], "empty tables must fall back rather than report nothing"
    assert index["available"] is False


def test_missing_tables_do_not_raise(monkeypatch):
    _clean(); _reset()
    monkeypatch.setattr(ob, "_index_from_tables", lambda: None)
    monkeypatch.setattr(ob, "_load_archive", lambda: None)
    assert ob.get_index()["available"] is False
    assert ob.products_for("anything") == []
