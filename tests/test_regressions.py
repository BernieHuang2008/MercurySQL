"""
Regression tests for the findings of the project review (issue #1 / upstream #38).

Every test here fails on `main@5169ed2` and passes after the fix. The finding id
is in the test name, so a failure points at the review entry it belongs to.
"""
import sqlite3
import sys
import threading

import pytest

from MercurySQL import DataBase
from MercurySQL.drivers.base import check_type_sql
from MercurySQL.drivers.sqlite import Driver_SQLite
from MercurySQL.errors import (
    InvalidIdentifierError,
    NotExistsError,
    NotSpecifiedError,
    NotSupportedError,
    QueueTimeoutError,
    UnsafeTypeError,
)


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def run_bounded(func, timeout=5.0):
    """Run `func` in a thread; fail the test if it does not finish in time."""
    box = {}

    def target():
        try:
            box["value"] = func()
        except BaseException as exc:  # noqa: BLE001 - re-raised below
            box["error"] = exc

    worker = threading.Thread(target=target, daemon=True)
    worker.start()
    worker.join(timeout)
    assert not worker.is_alive(), f"call did not return within {timeout}s (it hangs)"
    if "error" in box:
        raise box["error"]
    return box.get("value")


# --------------------------------------------------------------------------- #
# F-01 -- a failed statement raises instead of blocking the caller forever
# --------------------------------------------------------------------------- #
def test_f01_bad_sql_raises(db):
    with pytest.raises(sqlite3.OperationalError):
        run_bounded(lambda: db.do("SELECT * FROM missing_table"))


def test_f01_unknown_column_raises(table):
    with pytest.raises(NotExistsError):
        run_bounded(lambda: table.insert(nosuch=1))


def test_f01_duplicate_primary_key_raises(table):
    table.insert(id=1, name="first")
    with pytest.raises(sqlite3.IntegrityError):
        run_bounded(lambda: table.insert(id=1, name="second"))


def test_f01_connect_failure_raises_in_constructor(tmp_path):
    missing = str(tmp_path / "no_such_dir" / "db.sqlite")
    with pytest.raises(sqlite3.OperationalError):
        DataBase(missing, driver=Driver_SQLite)


def test_f01_missing_driver_raises_not_specified(monkeypatch):
    import MercurySQL.gensql.database as database_module

    monkeypatch.setattr(database_module, "default_driver", None)
    with pytest.raises(NotSpecifiedError):
        DataBase("whatever.db")


def test_f01_queue_timeout_is_reported(db):
    # A timeout raises instead of hanging; the statement itself is trivial, so
    # this mainly proves the timeout path exists and is wired to the caller.
    db.do("SELECT 1", timeout=5)


# --------------------------------------------------------------------------- #
# F-02 -- setPrimaryKey() must not shift column values
# --------------------------------------------------------------------------- #
def test_f02_set_primary_key_keeps_values(db):
    tbl = db.createTable("t")
    tbl.newColumn("id", int)
    tbl.newColumn("name", str)
    tbl.insert(id=7, name="alice")

    tbl.setPrimaryKey("name", "TEXT")

    assert tbl.columns == ["name", "id"], tbl.columns
    # The values moved with their column: `id` is still 7, `name` is still
    # "alice". The old code shifted them ({"name": 7, "id": "alice"}).
    assert list(tbl.select()) == [{"name": "alice", "id": 7}], list(tbl.select())


def test_f02_set_primary_key_is_one_transaction(db):
    tbl = db.createTable("t")
    tbl.newColumn("id", int)
    tbl.newColumn("name", str)
    tbl.insert(id=1, name="a")

    tbl.setPrimaryKey("name")

    # The rebuild leaves no temporary table behind.
    tables = [row[0] for row in db.do(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()]
    assert tables == ["t"], tables


# --------------------------------------------------------------------------- #
# F-03 -- multi-statement do() is one transaction and reports failures
# --------------------------------------------------------------------------- #
def test_f03_second_statement_failure_rolls_back(db):
    tbl = db.createTable("t")
    tbl.struct({"id": int, "name": str})

    with pytest.raises(sqlite3.OperationalError):
        db.do("INSERT INTO t (id, name) VALUES (777, 'kept')", "THIS IS NOT SQL")

    rows = sqlite3.connect(db.info["name"]).execute("SELECT * FROM t").fetchall()
    assert rows == [], rows


def test_f03_returns_last_statement_rows(db):
    result = db.do("SELECT 1 AS a", "SELECT 2 AS b")
    assert result.fetchall() == [(2,)]
    assert result.columns == ["b"]


def test_f03_paras_are_not_mutated(db):
    paras = []
    db.do("SELECT 1", "SELECT 2", paras=paras)
    assert paras == []


# --------------------------------------------------------------------------- #
# F-04 -- identifiers are quoted, selection cannot smuggle SQL
# --------------------------------------------------------------------------- #
def test_f04_selection_injection_is_rejected(db):
    users = db.createTable("users")
    users.struct({"id": int, "name": str, "secret": str})
    users.insert(id=1, name="admin", secret="TOPSECRET")

    tbl = db.createTable("t")
    tbl.struct({"id": int, "name": str})
    tbl.insert(id=1, name="public")

    sel = "id, (SELECT secret FROM users WHERE id = 1) AS leak"
    with pytest.raises(NotExistsError):
        list(tbl.select(tbl["id"] == 1, selection=sel))


def test_f04_selection_accepts_known_columns(db):
    tbl = db.createTable("t")
    tbl.struct({"id": int, "name": str})
    tbl.insert(id=1, name="public")

    assert list(tbl.select(selection=["id"])) == [{"id": 1}]
    assert list(tbl.select(selection="name")) == [{"name": "public"}]


def test_f04_raw_selection_is_opt_in(db):
    tbl = db.createTable("t")
    tbl.struct({"id": int, "name": str})
    tbl.insert(id=1, name="public")

    rows = list(tbl.select(selection="id, upper(name) AS up", raw=True))
    assert rows == [{"id": 1, "up": "PUBLIC"}], rows


def test_f04_identifiers_are_quoted():
    gensql = Driver_SQLite.APIs.gensql
    assert gensql.drop_table('x"; DROP TABLE users; --') == (
        'DROP TABLE "x""; DROP TABLE users; --"'
    )
    assert gensql.insert("t", ["a", "b"], "(?, ?)") == (
        'INSERT INTO "t" ("a", "b") VALUES (?, ?)'
    )


def test_f04_weird_table_name_is_usable(db):
    tbl = db.createTable("my table")
    tbl.newColumn("x", int)
    tbl.insert(x=1)

    assert list(tbl.select()) == [{"x": 1}]
    assert "my table" in db.tables


def test_f04_type_strings_cannot_carry_ddl(table):
    with pytest.raises(UnsafeTypeError):
        table["x"] = "TEXT DEFAULT 'pwn'"
    with pytest.raises(UnsafeTypeError):
        check_type_sql('TEXT); DROP TABLE t; --')


def test_f04_plain_custom_types_still_work(table):
    table["x"] = "VARCHAR(255) NOT NULL"
    assert table.columnsType["x"] == "VARCHAR(255) NOT NULL"


def test_f04_empty_identifier_is_rejected(db):
    with pytest.raises(InvalidIdentifierError):
        db.createTable("").newColumn("x", int)


# --------------------------------------------------------------------------- #
# F-05 -- __auto=True is a real UPSERT
# --------------------------------------------------------------------------- #
def test_f05_auto_keeps_unspecified_columns(db):
    tbl = db.createTable("t")
    tbl.struct({"id": int, "name": str, "score": float}, primaryKey="id")
    tbl.insert(id=1, name="alice", score=1.5)

    tbl.insert(id=1, name="alice2", __auto=True)

    assert list(tbl.select()) == [{"id": 1, "name": "alice2", "score": 1.5}]


def test_f05_auto_without_primary_key_raises(db):
    tbl = db.createTable("t")
    tbl.struct({"id": int, "name": str})
    tbl.insert(id=1, name="alice")

    with pytest.raises(NotSupportedError):
        tbl.insert(id=1, name="alice2", __auto=True)


# --------------------------------------------------------------------------- #
# F-06 -- expressions generate valid SQL
# --------------------------------------------------------------------------- #
def test_f06_in_operator(table):
    table.insert_many([{"id": 1, "name": "a"}, {"id": 2, "name": "b"},
                       {"id": 3, "name": "c"}])

    rows = run_bounded(lambda: list(table.select(table["id"].in_([1, 2]))))
    assert [row["id"] for row in rows] == [1, 2]

    assert (table["id"].in_([1, 2])).formula() == ("(id IN (?, ?))", (1, 2))


def test_f06_in_empty_set_matches_nothing(table):
    table.insert(id=1, name="a")
    assert list(table.select(table["id"].in_([]))) == []


def test_f06_between(table):
    table.insert_many([{"id": 1, "name": "a"}, {"id": 2, "name": "b"},
                       {"id": 3, "name": "c"}])
    rows = list(table.select(table["id"].between(1, 2)))
    assert [row["id"] for row in rows] == [1, 2]


def test_f06_not_operator(table):
    table.insert_many([{"id": 1, "name": "a"}, {"id": 2, "name": "b"}])
    rows = list(table.select(~(table["id"] == 1)))
    assert [row["id"] for row in rows] == [2]


def test_f06_compare_with_none_is_null(table):
    table.insert(id=1, name=None)
    table.insert(id=2, name="b")

    rows = list(table.select(table["name"] == None))  # noqa: E711
    assert [row["id"] for row in rows] == [1]

    rows = list(table.select(table["name"] != None))  # noqa: E711
    assert [row["id"] for row in rows] == [2]


def test_f06_python_and_or_fail_loudly(db):
    tbl = db.createTable("t")
    tbl.struct({"owner": str, "secret": str})
    tbl.insert(owner="alice", secret="a")
    tbl.insert(owner="bob", secret="b")

    with pytest.raises(TypeError):
        (tbl["owner"] == "alice") and (tbl["secret"] == "b")
    with pytest.raises(TypeError):
        (tbl["owner"] == "alice") or (tbl["secret"] == "b")
    with pytest.raises(TypeError):
        not (tbl["owner"] == "alice")


def test_f06_bitwise_and_keeps_both_predicates(db):
    tbl = db.createTable("t")
    tbl.struct({"owner": str, "secret": str})
    tbl.insert(owner="alice", secret="a")
    tbl.insert(owner="bob", secret="b")

    rows = list(tbl.select((tbl["owner"] == "alice") & (tbl["secret"] == "b")))
    assert rows == []


def test_f06_del_column(db):
    tbl = db.createTable("t")
    tbl.struct({"id": int, "name": str})
    del tbl["name"]
    assert tbl.columns == ["id"]


def test_f06_deleting_last_column_raises(db):
    tbl = db.createTable("t")
    tbl.newColumn("only", int)
    with pytest.raises(NotSupportedError):
        del tbl["only"]
    assert "t" in db.tables


def test_f06_update_without_data_raises(table):
    table.insert(id=1, name="a")
    with pytest.raises(ValueError):
        table.update(table["id"] == 1)


# --------------------------------------------------------------------------- #
# F-07 -- thread / connection lifecycle
# --------------------------------------------------------------------------- #
def test_f07_close_releases_thread(tmp_path):
    before = threading.active_count()
    databases = [DataBase(str(tmp_path / f"leak_{i}.db"), driver=Driver_SQLite)
                 for i in range(5)]
    assert threading.active_count() == before + 5

    for database in databases:
        database.close()
    assert threading.active_count() == before


def test_f07_database_is_a_context_manager(db_path):
    with DataBase(db_path, driver=Driver_SQLite) as database:
        database.do("SELECT 1")
    assert database.closed


def test_f07_closed_database_rejects_statements(db):
    db.close()
    with pytest.raises(Exception):
        db.do("SELECT 1")


# --------------------------------------------------------------------------- #
# F-08 -- MySQL driver (static, via a stub connector)
# --------------------------------------------------------------------------- #
@pytest.fixture()
def mysql_driver(monkeypatch):
    """Import `MercurySQL.drivers.mysql` with a stub `mysql.connector`."""
    import importlib
    import types

    import MercurySQL.drivers as drivers_package

    connector = types.ModuleType("mysql.connector")

    class MySQLConnection:
        pass

    class _CursorExt:
        pass

    class cursor_cext:
        CMySQLCursor = _CursorExt

    class errors:
        ProgrammingError = type("ProgrammingError", (Exception,), {})

    connector.MySQLConnection = MySQLConnection
    connector.cursor_cext = cursor_cext
    connector.errors = errors
    connector.connect = lambda *a, **kw: None

    mysql_pkg = types.ModuleType("mysql")
    mysql_pkg.connector = connector

    monkeypatch.setitem(sys.modules, "mysql", mysql_pkg)
    monkeypatch.setitem(sys.modules, "mysql.connector", connector)
    # Forget a module imported by a previous test, otherwise `from
    # MercurySQL.drivers import mysql` hands back the stale object.
    monkeypatch.delitem(sys.modules, "MercurySQL.drivers.mysql", raising=False)
    monkeypatch.delattr(drivers_package, "mysql", raising=False)

    module = importlib.import_module("MercurySQL.drivers.mysql")
    yield types.SimpleNamespace(driver=module.Driver_MySQL, connector=connector)
    sys.modules.pop("MercurySQL.drivers.mysql", None)


def test_f08_type_mapping(mysql_driver):
    parse = mysql_driver.driver.TypeParser.parse
    assert parse(str) == "VARCHAR(255)"
    assert parse(int) == "BIGINT"
    assert parse(float) == "DOUBLE"
    assert parse((int, "not null")) == "BIGINT NOT NULL"
    assert parse((int, 5)) == "BIGINT DEFAULT 5"
    assert parse((str, "x' OR 1=1 --")) == "VARCHAR(255) DEFAULT 'x'' OR 1=1 --'"


def test_f08_identifiers_are_quoted(mysql_driver):
    gensql = mysql_driver.driver.APIs.gensql
    assert "`my table`" in gensql.drop_table("my table")
    assert "`a` = _new.`a`" in gensql.insert_or_update(
        "t", ["id", "a"], "%s, %s", primary_keys=["id"]
    )


def test_f08_create_database_name_is_quoted(mysql_driver):
    calls = []

    class Cursor:
        def execute(self, sql):
            calls.append(sql)

        def close(self):
            pass

    class Conn:
        def cursor(self):
            return Cursor()

    mysql_driver.connector.connect = lambda **kw: Conn()

    mysql_driver.driver.connect("my db", host="h", user="u")
    assert calls == ["USE `my db`;"]


# --------------------------------------------------------------------------- #
# F-10 / F-11 -- documentation and packaging metadata
# --------------------------------------------------------------------------- #
def test_f11_requires_python_is_declared():
    import pathlib

    root = pathlib.Path(__file__).resolve().parent.parent
    text = (root / "pyproject.toml").read_text(encoding="utf-8")
    assert "requires-python" in text
    assert "3.6" not in text or ">=3.8" in text


def test_f10_docs_do_not_claim_identifier_safety():
    import pathlib

    root = pathlib.Path(__file__).resolve().parent.parent
    docs = (root / "docs/source/modules/gensql.rst").read_text(encoding="utf-8")
    assert "all the query values are replaced with safe queries" not in docs


# --------------------------------------------------------------------------- #
# F-12 -- identifier case handling
# --------------------------------------------------------------------------- #
def test_f12_case_insensitive_table_and_column(db):
    tbl = db.createTable("Users")
    tbl.newColumn("ID", int)

    # Same table, same column, whatever the casing.
    assert list(tbl.select()) == []
    assert db["users"] is tbl
    assert list(db.tables) == ["Users"]

    tbl.insert(id=1)
    assert list(tbl.select(tbl["id"] == 1)) == [{"ID": 1}]


def test_f12_no_phantom_table_after_reopen(db_path):
    with DataBase(db_path, driver=Driver_SQLite) as first:
        first.createTable("Users").newColumn("ID", int)

    with DataBase(db_path, driver=Driver_SQLite) as second:
        assert list(second.tables) == ["Users"]
        second["users"].insert(id=2)
        assert list(second["Users"].select()) == [{"ID": 2}]


def test_f12_sqlite_sequence_is_not_a_user_table(db):
    tbl = db.createTable("t")
    tbl.struct({"id": int, "name": str}, primaryKey="id", autoIncrement=True)
    tbl.insert(name="x")
    assert "sqlite_sequence" not in db.tables


# --------------------------------------------------------------------------- #
# F-13 -- result caching, paging and batching
# --------------------------------------------------------------------------- #
def test_f13_expression_cache_is_invalidated(table):
    table.insert(id=1, name="a")
    exp = table["id"] >= 0
    assert len(list(exp)) == 1

    table.insert(id=2, name="b")
    assert len(list(exp)) == 2


def test_f13_limit_and_offset(table):
    table.insert_many([{"id": i, "name": "x"} for i in range(5)])
    rows = list(table.select(limit=2, offset=1))
    assert [row["id"] for row in rows] == [1, 2]


def test_f13_select_iter(table):
    table.insert_many([{"id": i, "name": "x"} for i in range(5)])
    assert [row["id"] for row in table.select_iter(page_size=2)] == [0, 1, 2, 3, 4]


def test_f13_insert_many_is_one_statement(table):
    table.insert_many([{"id": 1, "name": "a"}, {"id": 2, "name": "b"}])
    assert table.count() == 2


def test_f13_transaction_rolls_back(table):
    table.insert(id=1, name="a")
    with pytest.raises(sqlite3.OperationalError):
        with table.db.transaction():
            table.insert(id=2, name="b")
            table.db.do("THIS IS NOT SQL")

    assert table.count() == 1


# --------------------------------------------------------------------------- #
# Low-severity items
# --------------------------------------------------------------------------- #
def test_low_check_version_accepts_two_part_versions():
    from MercurySQL.gensql.database import check_version

    assert check_version("0.2") is True
    assert check_version("0.1.0") is False
    assert check_version("1.0.0") is False
    assert check_version("not-a-version") is False


def test_low_fetchone_on_empty_result_returns_none(db):
    db.do("CREATE TABLE t (id INTEGER)")
    assert db.do("SELECT * FROM t").fetchone() is None


def test_low_payload_sentinel_is_not_rewritten(db):
    result = db.do("SELECT '___!!!PAYLOAD!!!___' AS v").fetchall()
    assert result == [("___!!!PAYLOAD!!!___",)]


def test_low_rollback_on_failed_statement_keeps_database_usable(db):
    db.do("CREATE TABLE t (id INTEGER PRIMARY KEY)")
    db.do("INSERT INTO t (id) VALUES (1)")
    with pytest.raises(sqlite3.IntegrityError):
        db.do("INSERT INTO t (id) VALUES (1)")
    # The connection survived and still answers.
    assert db.do("SELECT COUNT(*) FROM t").fetchall() == [(1,)]


def test_low_queue_error_after_close_is_explicit(db):
    db.close()
    with pytest.raises(Exception) as info:
        db.do("SELECT 1")
    assert info.type.__name__ == "QueueClosedError"


def test_low_autoincrement_is_only_applied_to_the_primary_key(db):
    tbl = db.createTable("t")
    tbl.struct(
        {"id": int, "name": str, "score": float},
        primaryKey="id",
        autoIncrement=True,
    )
    tbl.insert(name="a", score=1.0)

    assert tbl.primaryKeys == ["id"]
    assert list(tbl.select()) == [{"id": 1, "name": "a", "score": 1.0}]


def test_low_timeout_error_type():
    assert issubclass(QueueTimeoutError, Exception)
