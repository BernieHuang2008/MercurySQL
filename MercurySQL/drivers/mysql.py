"""
Requirements:
  - mysql-connector-python

Install it with the ``mysql`` extra::

    pip install "MercurySQL[mysql]"
"""
from .base import BaseDriver, check_type_sql

import re

import mysql.connector
from typing import Any, List


_ENGINE_OR_CHARSET_RE = re.compile(r"^[A-Za-z0-9_]*$")


def _literal(value: Any) -> str:
    """Render a Python value as an SQL literal (for DEFAULT clauses only)."""
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, bytes):
        value = value.decode("utf-8", "replace")
    if isinstance(value, str):
        return "'" + value.replace("\\", "\\\\").replace("'", "''") + "'"
    raise TypeError(f"Cannot use `{type(value).__name__}` as a column default.")


class Driver_MySQL(BaseDriver):
    """
    The built-in driver for MySQL (via ``mysql-connector-python``).

    .. note::
        Supported MySQL Version: **8.2** (the UPSERT uses the
        ``INSERT ... AS alias ON DUPLICATE KEY UPDATE`` form, which needs
        MySQL 8.0.19 or newer).
    """
    dependencies = ['mysql-connector-python']
    version = '0.2.0'
    payload = '%s'

    #: On Linux MySQL compares table names case-sensitively (it depends on
    #: ``lower_case_table_names``), so MercurySQL does not fold them.
    table_name_case_insensitive = False
    #: Column names are always case-insensitive in MySQL.
    column_name_case_insensitive = True

    Conn = mysql.connector.MySQLConnection
    Cursor = mysql.connector.cursor_cext.CMySQLCursor

    class APIs(BaseDriver.APIs):
        ident_quote = '`'

        class gensql:
            @staticmethod
            def drop_table(table_name: str) -> str:
                q = Driver_MySQL.APIs.quote_ident
                return f"DROP TABLE {q(table_name)};"

            @staticmethod
            def get_all_tables() -> str:
                return "SHOW TABLES;"

            @staticmethod
            def get_all_columns(table_name: str) -> str:
                q = Driver_MySQL.APIs.quote_ident
                return f"DESCRIBE {q(table_name)};"

            @staticmethod
            def get_primary_keys(table_name: str) -> str:
                q = Driver_MySQL.APIs.quote_ident
                return f"SHOW KEYS FROM {q(table_name)} WHERE Key_name = 'PRIMARY';"

            @staticmethod
            def create_table_if_not_exists(table_name: str, column_name: str, column_type: str, primaryKey=False, autoIncrement=False, engine='', charset='') -> str:
                q = Driver_MySQL.APIs.quote_ident
                for option, value in (("engine", engine), ("charset", charset)):
                    if value and not _ENGINE_OR_CHARSET_RE.match(value):
                        raise ValueError(
                            f"Invalid `{option}` value `{value}`: only letters, "
                            "digits and underscores are allowed."
                        )
                tail = f" {engine}" if engine else ""
                tail += f" DEFAULT CHARSET={charset}" if charset else ""
                return (
                    f"CREATE TABLE IF NOT EXISTS {q(table_name)} ("
                    f"{q(column_name)} {column_type}"
                    f"{' PRIMARY KEY' if primaryKey else ''}"
                    f"{' AUTO_INCREMENT' if autoIncrement else ''}"
                    f"){tail};"
                )

            @staticmethod
            def add_column(table_name: str, column_name: str, column_type: str) -> str:
                q = Driver_MySQL.APIs.quote_ident
                return (
                    f"ALTER TABLE {q(table_name)} "
                    f"ADD COLUMN {q(column_name)} {column_type};"
                )

            @staticmethod
            def drop_column(table_name: str, column_name: str) -> str:
                q = Driver_MySQL.APIs.quote_ident
                return (
                    f"ALTER TABLE {q(table_name)} "
                    f"DROP COLUMN {q(column_name)};"
                )

            @staticmethod
            def set_primary_key(table, keyname: str, keytype: str) -> list:
                q = Driver_MySQL.APIs.quote_ident
                return [
                    f"ALTER TABLE {q(table.table_name)} DROP PRIMARY KEY;",
                    f"ALTER TABLE {q(table.table_name)} "
                    f"ADD PRIMARY KEY ({q(keyname)});",
                ]

            @staticmethod
            def insert(table_name: str, columns: List[str], values: str) -> str:
                q = Driver_MySQL.APIs.quote_ident
                cols = ", ".join(map(q, columns))
                return f"INSERT INTO {q(table_name)} ({cols}) VALUES {values};"

            @staticmethod
            def insert_or_update(table_name: str, columns: List[str], values: str, primary_keys: List[str]) -> str:
                q = Driver_MySQL.APIs.quote_ident
                cols = ", ".join(map(q, columns))
                # `VALUES(col)` is deprecated since MySQL 8.0.20; the row alias
                # form is the supported replacement and keeps the same
                # semantics as the SQLite driver (only the supplied columns are
                # updated).
                updates = ", ".join(
                    f"{q(c)} = _new.{q(c)}"
                    for c in columns
                    if c not in primary_keys
                )
                if not updates:
                    # Everything supplied is part of the key: nothing to update.
                    updates = f"{q(columns[0])} = {q(columns[0])}"
                return (
                    f"INSERT INTO {q(table_name)} ({cols}) VALUES {values} "
                    f"AS _new ON DUPLICATE KEY UPDATE {updates};"
                )

            @staticmethod
            def update(table_name: str, columns: List[str], condition: str) -> str:
                q = Driver_MySQL.APIs.quote_ident
                sets = ", ".join(f"{q(c)} = {Driver_MySQL.payload}" for c in columns)
                return f"UPDATE {q(table_name)} SET {sets} WHERE {condition};"

            @staticmethod
            def query(table_name: str, selection: str, condition: str, limit=None, offset=None) -> str:
                q = Driver_MySQL.APIs.quote_ident
                cmd = f"SELECT {selection} FROM {q(table_name)} WHERE {condition}"
                if limit is not None:
                    cmd += f" LIMIT {int(limit)}"
                    if offset is not None:
                        cmd += f" OFFSET {int(offset)}"
                return cmd + ";"

            @staticmethod
            def delete(table_name: str, condition: str) -> str:
                q = Driver_MySQL.APIs.quote_ident
                return f"DELETE FROM {q(table_name)} WHERE {condition};"

        @classmethod
        def get_all_tables(cls, db) -> List[str]:
            cursor = db.do(cls.gensql.get_all_tables())
            return list(map(lambda x: x[0], cursor.fetchall()))

        @classmethod
        def get_all_columns(cls, db, table_name: str) -> List[str]:
            cursor = db.do(cls.gensql.get_all_columns(table_name))
            # [name, type, null, key, default, extra]
            return list(map(lambda x: [x[0], x[1], x[2], x[3], x[4], x[5]], cursor.fetchall()))

        @classmethod
        def get_primary_keys(cls, db, table_name: str) -> List[str]:
            cursor = db.do(cls.gensql.get_primary_keys(table_name))
            # SHOW KEYS -> (Table, Non_unique, Key_name, Seq_in_index,
            #               Column_name, Collation, Cardinality, ...)
            keyed = [
                (row[3], row[4])
                for row in cursor.fetchall()
                if len(row) > 4 and row[2] == 'PRIMARY'
            ]
            keyed.sort(key=lambda item: item[0])
            return [name for _, name in keyed]

    class TypeParser:
        """
        Parse the type from `Python Type` -> `MySQL Type`.
        """

        @staticmethod
        def parse(type_: Any) -> str:
            """
            Compile the type to MySQL type.

            :param type_: The type to parse.
            :type type_: Any

            :return: The MySQL type.
            :rtype: str

            +-------------------+--------------+
            | Supported Types   | MySQL Type   |
            +===================+==============+
            | bool              | BOOLEAN      |
            +-------------------+--------------+
            | int               | BIGINT       |
            +-------------------+--------------+
            | float             | DOUBLE       |
            +-------------------+--------------+
            | str               | VARCHAR(255) |
            +-------------------+--------------+
            | bytes             | BLOB         |
            +-------------------+--------------+
            | datetime.datetime | DATETIME     |
            +-------------------+--------------+
            | datetime.date     | DATE         |
            +-------------------+--------------+
            | datetime.time     | TIME         |
            +-------------------+--------------+

            Example Usage:

            .. code-block:: python

                TypeParser.parse(int)                  # BIGINT
                TypeParser.parse(str)                  # VARCHAR(255)
                TypeParser.parse((int, 'not null'))    # BIGINT NOT NULL
                TypeParser.parse((int, 10))            # BIGINT DEFAULT 10

            .. versionchanged:: 0.2.0
               ``int`` maps to 64-bit ``BIGINT`` (it used to be 32-bit ``INT``,
               which silently overflowed data migrated from SQLite), ``str``
               maps to ``VARCHAR(255)`` (it used to be ``VARCHAR(225)``, a typo
               that truncated longer values), the ``DFAULT`` typo is gone, and
               default values are properly quoted.
            """
            import datetime

            supported_types = {
                bool: 'BOOLEAN',
                int: 'BIGINT',
                float: 'DOUBLE',
                str: 'VARCHAR(255)',
                bytes: 'BLOB',

                datetime.datetime: 'DATETIME',
                datetime.date: 'DATE',
                datetime.time: 'TIME',
            }

            if not isinstance(type_, tuple):
                type_ = (type_,)

            head, modifiers = type_[0], list(type_[1:])

            default = None
            if isinstance(head, str) and head.startswith('\t'):     # custom type
                res = check_type_sql(head.strip())
            elif isinstance(head, type):
                if head not in supported_types:
                    raise TypeError(f"Type `{head}` is not supported.")
                res = supported_types[head]
            elif type(head) in supported_types:                     # a value
                res = supported_types[type(head)]
                default = head
            elif isinstance(head, str):                             # plain string type
                res = check_type_sql(head)
            else:
                raise TypeError(f"Type `{head!r}` is not supported.")

            parts = [res]
            if default is not None:
                parts.append(f"DEFAULT {_literal(default)}")
            for mod in modifiers:
                if isinstance(mod, str) and mod.strip().lower() == 'not null':
                    parts.append('NOT NULL')
                else:
                    parts.append(f"DEFAULT {_literal(mod)}")

            return " ".join(parts)

    @staticmethod
    def connect(db_name: str, host: str, user: str, passwd: str = '', force=False, **kwargs) -> "Driver_MySQL.Conn":
        """
        Connect to a MySQL database.

        :param db_name: The database name.
        :param host: The server host.
        :param user: The user name.
        :param passwd: The password.
        :param force: Connect directly to ``db_name`` (and fail if it does not
            exist). When ``False`` (default), the database is created on demand.
        :param kwargs: Extra keyword arguments for ``mysql.connector.connect``.
        """
        q = Driver_MySQL.APIs.quote_ident

        if force:
            kwargs['database'] = db_name
            return mysql.connector.connect(
                host=host, user=user, passwd=passwd, **kwargs
            )

        conn = mysql.connector.connect(host=host, user=user, passwd=passwd, **kwargs)
        cursor = conn.cursor()
        try:
            try:
                cursor.execute(f"USE {q(db_name)};")
            except mysql.connector.errors.ProgrammingError:
                cursor.execute(f"CREATE DATABASE {q(db_name)};")
                cursor.execute(f"USE {q(db_name)};")
        finally:
            try:
                cursor.close()
            except Exception:
                pass
        return conn
