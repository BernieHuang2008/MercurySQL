"""Shared fixtures for the MercurySQL test-suite."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from MercurySQL import DataBase, set_driver
from MercurySQL.drivers.sqlite import Driver_SQLite


set_driver(Driver_SQLite)


@pytest.fixture()
def db_path(tmp_path):
    return str(tmp_path / "test.db")


@pytest.fixture()
def db(db_path):
    database = DataBase(db_path, driver=Driver_SQLite)
    try:
        yield database
    finally:
        database.close()


@pytest.fixture()
def table(db):
    tbl = db.createTable("t")
    tbl.struct({"id": int, "name": str}, primaryKey="id")
    return tbl
