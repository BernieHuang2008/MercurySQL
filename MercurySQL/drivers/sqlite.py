"""
Requirements:
  - sqlite3
"""
from .base import BaseDriver, check_type_sql

import sqlite3
import uuid
from typing import Any, List


class Driver_SQLite(BaseDriver):
    """
    The built-in driver for SQLite (via the standard-library :mod:`sqlite3`).

    .. note::
        Connections are opened in **autocommit** mode (``isolation_level=None``)
        so that MercurySQL owns the transaction boundaries: one transaction per
        ``db.do(...)`` call, one per ``with db.transaction():`` block. Without
        that, Python's legacy implicit-transaction handling would interleave
        with the explicit ``BEGIN`` used by ``transaction()``.
    """
    dependencies = ['sqlite3']
    version = '0.2.0'
    payload = '?'

    #: SQLite compares table and column names case-insensitively.
    table_name_case_insensitive = True
    column_name_case_insensitive = True

    Conn = sqlite3.Connection
    Cursor = sqlite3.Cursor

    class APIs(BaseDriver.APIs):
        ident_quote = '"'

        class gensql:
            @staticmethod
            def drop_table(table_name: str) -> str:
                q = Driver_SQLite.APIs.quote_ident
                return f"DROP TABLE {q(table_name)}"

            @staticmethod
            def get_all_tables() -> str:
                # `sqlite_%` are internal bookkeeping tables (e.g.
                # sqlite_sequence, created by AUTOINCREMENT); they are not user
                # tables and must not show up in `db.tables`.
                return (
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table' AND name NOT LIKE 'sqlite_%';"
                )

            @staticmethod
            def get_all_columns(table_name: str) -> str:
                q = Driver_SQLite.APIs.quote_ident
                return f"PRAGMA table_info({q(table_name)});"

            @staticmethod
            def get_primary_keys(table_name: str) -> str:
                # PRAGMA table_info -> (cid, name, type, notnull, dflt, pk)
                # `pk` is the 1-based position in the primary key, or 0.
                return Driver_SQLite.APIs.gensql.get_all_columns(table_name)

            @staticmethod
            def create_table_if_not_exists(table_name: str, column_name: str, column_type: str, primaryKey=False, autoIncrement=False) -> str:
                q = Driver_SQLite.APIs.quote_ident
                if autoIncrement and not primaryKey:
                    # SQLite only accepts AUTOINCREMENT on INTEGER PRIMARY KEY.
                    raise ValueError(
                        "SQLite only supports AUTOINCREMENT on a PRIMARY KEY column."
                    )
                return (
                    f"CREATE TABLE IF NOT EXISTS {q(table_name)} "
                    f"({q(column_name)} {column_type}"
                    f"{' PRIMARY KEY' if primaryKey else ''}"
                    f"{' AUTOINCREMENT' if autoIncrement else ''})"
                )

            @staticmethod
            def add_column(table_name: str, column_name: str, column_type: str) -> str:
                q = Driver_SQLite.APIs.quote_ident
                return (
                    f"ALTER TABLE {q(table_name)} "
                    f"ADD COLUMN {q(column_name)} {column_type}"
                )

            @staticmethod
            def drop_column(table_name: str, column_name: str) -> str:
                q = Driver_SQLite.APIs.quote_ident
                return (
                    f"ALTER TABLE {q(table_name)} "
                    f"DROP COLUMN {q(column_name)}"
                )

            @staticmethod
            def set_primary_key(table, keyname: str, keytype: str) -> list:
                """
                Rebuild the table with `keyname` as its primary key.

                Every column is named explicitly in the CREATE and in the
                INSERT ... SELECT: a positional `SELECT *` shifts all values when
                the new key is not the first column. The statement list runs in
                one transaction, so a failure cannot leave the data in the
                temporary table.
                """
                q = Driver_SQLite.APIs.quote_ident
                others = [(n, t) for n, t in table.columnsType.items() if n != keyname]
                columns = [keyname] + [n for n, _ in others]
                definitions = [f"{q(keyname)} {keytype} PRIMARY KEY"]
                definitions += [f"{q(name)} {type_}" for name, type_ in others]

                # Random name: two processes must not fight over the same
                # temporary table, and a crashed rebuild must not be reused.
                temp = f"___mercurysql_tmp_{uuid.uuid4().hex}"

                quoted_columns = ", ".join(map(q, columns))
                return [
                    f"CREATE TABLE {q(temp)} ({', '.join(definitions)})",
                    f"INSERT INTO {q(temp)} ({quoted_columns}) "
                    f"SELECT {quoted_columns} FROM {q(table.table_name)}",
                    f"DROP TABLE {q(table.table_name)}",
                    f"ALTER TABLE {q(temp)} RENAME TO {q(table.table_name)}",
                ]

            @staticmethod
            def insert(table_name: str, columns: List[str], values: str) -> str:
                q = Driver_SQLite.APIs.quote_ident
                cols = ", ".join(map(q, columns))
                return f"INSERT INTO {q(table_name)} ({cols}) VALUES {values}"

            @staticmethod
            def insert_or_update(table_name: str, columns: List[str], values: str, primary_keys: List[str]) -> str:
                if not primary_keys:
                    raise ValueError(
                        "`__auto=True` needs a primary key: SQLite can only "
                        "upsert through `ON CONFLICT(<primary key>)`."
                    )
                q = Driver_SQLite.APIs.quote_ident
                cols = ", ".join(map(q, columns))
                updates = ", ".join(
                    f"{q(c)} = excluded.{q(c)}"
                    for c in columns
                    if c not in primary_keys
                )
                conflict = ", ".join(map(q, primary_keys))
                if not updates:
                    return (
                        f"INSERT INTO {q(table_name)} ({cols}) VALUES {values} "
                        f"ON CONFLICT ({conflict}) DO NOTHING"
                    )
                return (
                    f"INSERT INTO {q(table_name)} ({cols}) VALUES {values} "
                    f"ON CONFLICT ({conflict}) DO UPDATE SET {updates}"
                )

            @staticmethod
            def update(table_name: str, columns: List[str], condition: str) -> str:
                q = Driver_SQLite.APIs.quote_ident
                sets = ", ".join(f"{q(c)} = {Driver_SQLite.payload}" for c in columns)
                return f"UPDATE {q(table_name)} SET {sets} WHERE {condition}"

            @staticmethod
            def query(table_name: str, selection: str, condition: str, limit=None, offset=None) -> str:
                q = Driver_SQLite.APIs.quote_ident
                cmd = f"SELECT {selection} FROM {q(table_name)} WHERE {condition}"
                if limit is not None:
                    cmd += f" LIMIT {int(limit)}"
                    if offset is not None:
                        cmd += f" OFFSET {int(offset)}"
                return cmd

            @staticmethod
            def delete(table_name: str, condition: str) -> str:
                q = Driver_SQLite.APIs.quote_ident
                return f"DELETE FROM {q(table_name)} WHERE {condition}"

        @classmethod
        def get_all_tables(cls, db) -> List[str]:
            cursor = db.do(cls.gensql.get_all_tables())
            return list(map(lambda x: x[0], cursor.fetchall()))

        @classmethod
        def get_all_columns(cls, db, table_name: str) -> List[str]:
            cursor = db.do(cls.gensql.get_all_columns(table_name))
            return list(map(lambda x: [x[1], x[2]], cursor.fetchall()))

        @classmethod
        def get_primary_keys(cls, db, table_name: str) -> List[str]:
            cursor = db.do(cls.gensql.get_primary_keys(table_name))
            # (cid, name, type, notnull, dflt, pk)
            keyed = [row for row in cursor.fetchall() if len(row) > 5 and row[5]]
            keyed.sort(key=lambda row: row[5])
            return [row[1] for row in keyed]

    class TypeParser:
        """
        Parse the type from `Python Type` -> `SQL Type`.
        """

        @staticmethod
        def parse(type_: Any) -> str:
            """
            Compile the type to SQLite type.

            :param type_: The type to parse.
            :type type_: Any

            :return: The SQLite type.
            :rtype: str

            +-----------------+-------------+
            | Supported Types | SQLite Type |
            +=================+=============+
            | str             | TEXT        |
            +-----------------+-------------+
            | int             | INTEGER     |
            +-----------------+-------------+
            | float           | REAL        |
            +-----------------+-------------+
            | bool            | BOOLEAN     |
            +-----------------+-------------+
            | bytes           | BLOB        |
            +-----------------+-------------+

            Example Usage:

            .. code-block:: python

                TypeParser.parse(str)       # TEXT
                TypeParser.parse(int)       # INTEGER
                TypeParser.parse(float)     # REAL
                ...

            A custom type string is validated by
            :func:`MercurySQL.drivers.base.check_type_sql`, so it cannot carry
            extra DDL (``"TEXT DEFAULT 'pwn'"`` is rejected).
            """
            supported_types = {
                str: 'TEXT',
                int: 'INTEGER',
                float: 'REAL',
                bool: 'BOOLEAN',
                bytes: 'BLOB'
            }

            # round 1: Built-in Types
            if type_ in supported_types:
                return supported_types[type_]

            # round 2: Custom Types (validated)
            if isinstance(type_, str):
                return check_type_sql(type_)

            # Not Supported
            raise TypeError(f"Type `{str(type_)}` not supported.")

    @staticmethod
    def connect(db_name: str, **kwargs) -> "Driver_SQLite.Conn":
        # NOTE: the return type must stay a *string*: it is evaluated while the
        # class body is still executing, so a bare `Driver_SQLite.Conn` raises
        # NameError on Python < 3.14 (annotations are lazy only from 3.14 on).
        # `isolation_level=None` -> autocommit; MercurySQL manages transactions
        # explicitly (`db.do()` batches and `db.transaction()`).
        kwargs.setdefault("isolation_level", None)
        return sqlite3.connect(db_name, **kwargs)
