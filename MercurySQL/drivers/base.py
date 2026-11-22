import re
from typing import Any, List, Union

from ..errors import InvalidIdentifierError, UnsafeTypeError

__all__ = ["BaseDriver", "quote_ident", "normalize_ident", "check_type_sql"]

# ---------------------------------------------------------------------------
# Identifier helpers
#
# Table names and column names are *never* bound as parameters: they are pasted
# into the statement, so they must be validated and quoted by the driver. Every
# gensql helper below goes through these two functions.
# ---------------------------------------------------------------------------

_IDENT_TYPE_ERROR = "Identifier must be a `str`, got `{type}`."


def _check_ident(name) -> str:
    if not isinstance(name, str):
        raise InvalidIdentifierError(
            _IDENT_TYPE_ERROR.format(type=type(name).__name__)
        )
    if not name:
        raise InvalidIdentifierError("Identifier must not be empty.")
    if "\x00" in name:
        raise InvalidIdentifierError("Identifier must not contain a NUL character.")
    return name


def quote_ident(name: str) -> str:
    """
    Quote an SQL identifier the SQL-standard way (``"name"``).

    Drivers whose dialect uses another quoting character override this method
    (MySQL uses backticks).

    :raises InvalidIdentifierError: when the name cannot be a valid identifier.
    """
    return '"' + _check_ident(name).replace('"', '""') + '"'


def normalize_ident(name: str) -> str:
    """Fold an identifier for comparison (never for use in a statement)."""
    return name.lower()


_TYPE_RE = re.compile(
    r"""
    ^\s*
    [A-Za-z_][A-Za-z0-9_]*                              # type name
    (?:\s+(?:precision|varying|unsigned|zerofill|signed))*  # multi-word types
    (?:\s*\(\s*\d+(?:\s*,\s*\d+)?\s*\))?                # (size) / (size, digits)
    (?:\s+(?:NOT\s+NULL|NULL|PRIMARY\s+KEY|UNIQUE
           |AUTOINCREMENT|AUTO_INCREMENT))*             # column modifiers
    (?:\s+DEFAULT\s+-?\d+(?:\.\d+)?)?                   # numeric default
    \s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)


def check_type_sql(type_sql: str) -> str:
    """
    Validate a custom SQL type string.

    MercurySQL pastes the parsed type into ``CREATE TABLE`` / ``ALTER TABLE``,
    so a type is an *identifier-like* token. Only plain type names, an optional
    size, the column modifiers MercurySQL understands, and a numeric ``DEFAULT``
    are accepted. Without this check ``table['x'] = "TEXT DEFAULT 'pwn'"`` is
    DDL injection.

    :param type_sql: The type to validate.
    :return: The validated type, unchanged.
    :raises UnsafeTypeError: when the string is not a plain SQL type.
    """
    if not isinstance(type_sql, str):
        raise UnsafeTypeError(
            f"SQL type must be a `str`, got `{type(type_sql).__name__}`."
        )
    if not _TYPE_RE.match(type_sql):
        raise UnsafeTypeError(
            f"`{type_sql}` is not a plain SQL type. Only type names with an "
            "optional size (e.g. `VARCHAR(255)`), column modifiers "
            "(`NOT NULL`, `PRIMARY KEY`, `UNIQUE`, `AUTOINCREMENT`) and a "
            "numeric `DEFAULT` are accepted."
        )
    return type_sql


class BaseDriver:
    """
    The base class of all drivers.
    """

    dependencies = []   # just for hints about what dependencies are needed
    version = '0.0.0'
    payload = '?'

    #: Whether table names are compared case-insensitively (SQLite: True,
    #: MySQL on Linux: False -- it depends on ``lower_case_table_names``).
    table_name_case_insensitive = True
    #: Whether column names are compared case-insensitively (True everywhere).
    column_name_case_insensitive = True

    class Cursor:
        """
        .. note::
            The `Cursor` class here is only used for type hints, indicating the return type or parameter type of functions. In practice, instances of this class are not directly created or called.

        A cursor object for database operations.
        Usually, SQL libraries will provide these methods for executing SQL queries and interacting with databases.
        E.g., `sqlite3.Cursor <https://docs.python.org/3/library/sqlite3.html#cursor-objects>`_ or `pymysql.cursors.Cursor <https://pymysql.readthedocs.io/en/latest/modules/cursors.html>`_.
        """

        description = None

        def execute(self, sql: str, paras: List[tuple] = None) -> "BaseDriver.Cursor":
            """
            This method is used to execute SQL queries.

            :param sql: The SQL query to be executed.
            :param paras: The parameters of the SQL query.
            :return: The cursor object itself.
            """
            pass

        def fetchone(self) -> tuple:
            """
            This method is used to fetch the next row of the query result.

            :return: The next row of the query result.
            """
            pass

        def fetchall(self) -> List[tuple]:
            """
            This method is used to fetch all rows of the query result.

            :return: All rows of the query result.
            """
            pass

        def close(self) -> None:
            """This method is used to close the cursor."""
            pass

    class Conn:
        """
        .. note::
            The `Conn` class here is only used for type hints, indicating the return type or parameter type of functions. In practice, instances of the `Cursor` class are not directly created or called.

        A Connection object for database operations.

        Also, a SQL library will provide these methods for interacting with databases.
        E.g., `sqlite3.Connection <https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection>`_ or `pymysql.connections.Connection <https://pymysql.readthedocs.io/en/latest/modules/connections.html>`_.
        """

        def cursor(self) -> "BaseDriver.Cursor":
            """
            This method is used to create a cursor object for database operations.

            :return: A cursor object for database operations.
            """
            pass

        def commit(self) -> None:
            """
            This method is used to commit (it means 'save') the changes to the database.
            """
            pass

        def rollback(self) -> None:
            """
            This method is used to discard the current transaction.
            """
            pass

        def close(self) -> None:
            """
            This method is used to close the connection to the database.
            """
            pass

    class APIs:
        """
        APIs is a class that provides SQL statements for database operations.

        .. warning::
            You must implement all the methods in this class.

        Every definition will be followed by an example of it's return value (in SQLite).

        .. versionchanged:: 0.2.0
            Identifiers are quoted by the driver (see :func:`quote_ident`), never
            pasted in raw. ``insert``/``update`` take a **list of column names**,
            and ``insert_or_update`` also takes the primary-key columns, so the
            driver can build a real UPSERT.
        """

        #: Character used to quote identifiers in this dialect.
        ident_quote = '"'

        @classmethod
        def quote_ident(cls, name: str) -> str:
            """
            Quote a single SQL identifier for this dialect.

            :param name: The table/column name.
            :type name: str
            :return: The quoted identifier.
            """
            quote = cls.ident_quote
            return quote + _check_ident(name).replace(quote, quote * 2) + quote

        class gensql:
            """
            APIs in this class will return a SQL code for database operations.
            Generally, these returned codes will be executed **DIRECTLY**.

            Every identifier handed to these functions is a plain name; the
            implementation is responsible for quoting it.
            """

            @staticmethod
            def drop_table(table_name: str) -> str:
                """
                Drop (Delete) a table.

                :param table_name: The name of the table to be dropped.
                :type table_name: str
                :return: The SQL statement to drop the table.

                Example Implementation (SQLite):

                .. code-block:: python

                    q = Driver_SQLite.APIs.quote_ident
                    return f"DROP TABLE {q(table_name)}"

                """
                pass

            @staticmethod
            def get_all_tables() -> str:
                """
                Get all table's informations in the database.

                :return: The SQL statement to get all table's informations in the database.

                Example Implementation (SQLite):

                .. code-block:: python

                    return "SELECT name FROM sqlite_master WHERE type='table';"
                """
                pass

            @staticmethod
            def get_all_columns(table_name: str) -> str:
                """
                Get all column's informations in the table.

                :param table_name: The name of the table.
                :type table_name: str

                Example Implementation (SQLite):

                .. code-block:: python

                    q = Driver_SQLite.APIs.quote_ident
                    return f"PRAGMA table_info({q(table_name)});"

                """
                pass

            @staticmethod
            def get_primary_keys(table_name: str) -> str:
                """
                Return the SQL statement that lists the primary-key columns.

                The result set must contain the column name in the first field,
                in primary-key order.

                Example Implementation (SQLite): the same ``PRAGMA`` as
                ``get_all_columns`` is used; its last field is the pk order.
                """
                pass

            @staticmethod
            def create_table_if_not_exists(table_name: str, column_name: str, column_type: str, primaryKey=False, autoIncrement=False) -> Union[str, List[str]]:
                """
                Create a table if it does not exist.

                :param table_name: The name of the table to be created.
                :type table_name: str
                :param column_name: The name of the column to be created.
                :type column_name: str
                :param column_type: The type of the column to be created (already parsed and validated).
                :type column_type: str

                Example Implementation (SQLite):

                .. code-block:: python

                    q = Driver_SQLite.APIs.quote_ident
                    return (f"CREATE TABLE IF NOT EXISTS {q(table_name)} "
                            f"({q(column_name)} {column_type}"
                            f"{' PRIMARY KEY' if primaryKey else ''})")

                """
                pass

            @staticmethod
            def add_column(table_name: str, column_name: str, column_type: str) -> Union[str, List[str]]:
                """
                Add a column to a table.

                :param table_name: The name of the table to be added.
                :type table_name: str
                :param column_name: The name of the column to be added.
                :type column_name: str
                :param column_type: The type of the column to be added (has been parsed by TypeParser).
                :type column_type: str

                Example Implementation (SQLite):

                .. code-block:: python

                    q = Driver_SQLite.APIs.quote_ident
                    return (f"ALTER TABLE {q(table_name)} "
                            f"ADD COLUMN {q(column_name)} {column_type}")

                """
                pass

            @staticmethod
            def drop_column(table_name: str, column_name: str) -> Union[str, List[str]]:
                """
                Drop (Delete) a column from a table.

                :param table_name: The name of the target table.
                :type table_name: str
                :param column_name: The name of the column to be dropped.
                :type column_name: str

                Example Implementation (SQLite):

                .. code-block:: python

                    q = Driver_SQLite.APIs.quote_ident
                    return (f"ALTER TABLE {q(table_name)} "
                            f"DROP COLUMN {q(column_name)}")

                """
                pass

            @staticmethod
            def set_primary_key(table, keyname: str, keytype: str) -> Union[str, List[str]]:
                """
                Set a primary key for the specified table.

                .. warning::
                   SQLite cannot add a primary key in place, so its implementation
                   rebuilds the table. It **must** name the columns explicitly in
                   both the ``CREATE`` and the ``INSERT ... SELECT`` -- a
                   positional ``SELECT *`` silently shifts every value when the
                   column order changes -- and the command queue runs the whole
                   list inside one transaction.

                :param table: The table to be set.
                :type table: Table
                :param keyname: The name of the primary key.
                :type keyname: str
                :param keytype: The type of the primary key (already parsed).
                :type keytype: str

                Example Implementation (SQLite):

                .. code-block:: python

                    q = Driver_SQLite.APIs.quote_ident
                    others = [(n, t) for n, t in table.columnsType.items()
                              if n != keyname]
                    cols = [keyname] + [n for n, _ in others]
                    defs = [f"{q(keyname)} {keytype} PRIMARY KEY"]
                    defs += [f"{q(n)} {t}" for n, t in others]
                    tmp = "___mercurysql_tmp"
                    return [
                        f"CREATE TABLE {q(tmp)} ({', '.join(defs)})",
                        f"INSERT INTO {q(tmp)} ({', '.join(map(q, cols))}) "
                        f"SELECT {', '.join(map(q, cols))} FROM {q(table.table_name)}",
                        f"DROP TABLE {q(table.table_name)}",
                        f"ALTER TABLE {q(tmp)} RENAME TO {q(table.table_name)}",
                    ]

                """
                pass

            @staticmethod
            def insert(table_name: str, columns: List[str], values: str) -> str:
                """
                Insert a row into the specified table.

                :param table_name: The name of the table to be inserted.
                :type table_name: str
                :param columns: The column names to be inserted.
                :type columns: List[str]
                :param values: The placeholders for the values, already separated by ','.
                :type values: str

                Example Implementation (SQLite):

                .. code-block:: python

                    q = Driver_SQLite.APIs.quote_ident
                    cols = ", ".join(map(q, columns))
                    return f"INSERT INTO {q(table_name)} ({cols}) VALUES ({values})"

                """
                pass

            @staticmethod
            def insert_or_update(table_name: str, columns: List[str], values: str, primary_keys: List[str]) -> str:
                """
                Insert a row, or update the existing row with the same primary key.

                .. versionchanged:: 0.2.0
                   A real UPSERT is generated, so columns that are not supplied
                   keep their previous value. The old ``INSERT OR REPLACE``
                   (SQLite) deleted and re-inserted the row, silently wiping
                   every unspecified column, and behaved differently from the
                   MySQL driver.

                :param table_name: The name of the table to be inserted.
                :type table_name: str
                :param columns: The column names to be inserted.
                :type columns: List[str]
                :param values: The placeholders for the values, already separated by ','.
                :type values: str
                :param primary_keys: The primary-key column names.
                :type primary_keys: List[str]

                Example Implementation (SQLite):

                .. code-block:: python

                    q = Driver_SQLite.APIs.quote_ident
                    cols = ", ".join(map(q, columns))
                    updates = ", ".join(
                        f"{q(c)} = excluded.{q(c)}"
                        for c in columns if c not in primary_keys)
                    if not updates:
                        return (f"INSERT INTO {q(table_name)} ({cols}) "
                                f"VALUES ({values}) ON CONFLICT DO NOTHING")
                    return (f"INSERT INTO {q(table_name)} ({cols}) VALUES ({values}) "
                            f"ON CONFLICT ({', '.join(map(q, primary_keys))}) "
                            f"DO UPDATE SET {updates}")

                """
                pass

            @staticmethod
            def update(table_name: str, columns: List[str], condition: str) -> str:
                """
                Update the specified table.

                :param table_name: The name of the table to be updated.
                :type table_name: str
                :param columns: The column names to be updated.
                :type columns: List[str]
                :param condition: The condition of the update, in the general SQL format, generated by Exp.
                :type condition: str

                Example Implementation (SQLite):

                .. code-block:: python

                    q = Driver_SQLite.APIs.quote_ident
                    sets = ", ".join(f"{q(c)} = {Driver_SQLite.payload}" for c in columns)
                    return f"UPDATE {q(table_name)} SET {sets} WHERE {condition}"

                """
                pass

            @staticmethod
            def query(table_name: str, selection: str, condition: str, limit=None, offset=None) -> str:
                """
                Query the specified table.

                :param table_name: The name of the table to be queried.
                :type table_name: str
                :param selection: The projection, **already quoted and validated** by the caller.
                :type selection: str
                :param condition: The condition of the query, in the general SQL format, generated by Exp.
                :type condition: str
                :param limit: Optional maximum number of rows.
                :type limit: int
                :param offset: Optional number of rows to skip (requires ``limit``).
                :type offset: int

                Example Implementation (SQLite):

                .. code-block:: python

                    q = Driver_SQLite.APIs.quote_ident
                    cmd = f"SELECT {selection} FROM {q(table_name)} WHERE {condition}"
                    if limit is not None:
                        cmd += f" LIMIT {int(limit)}"
                        if offset is not None:
                            cmd += f" OFFSET {int(offset)}"
                    return cmd

                """
                pass

            @staticmethod
            def delete(table_name: str, condition: str) -> str:
                """
                Delete the rows in specified table, which matches the condition.

                :param table_name: The name of the table to be deleted.
                :type table_name: str
                :param condition: The condition of the delete, in the general SQL format, generated by Exp.
                :type condition: str

                Example Implementation (SQLite):

                .. code-block:: python

                    q = Driver_SQLite.APIs.quote_ident
                    return f"DELETE FROM {q(table_name)} WHERE {condition}"
                """
                pass

        @classmethod
        def get_all_tables(cls, session) -> List[str]:
            """
            Get all tables in the database.

            .. note:
                You can copy the implementation of this method directly.

            The default implementation is based on the `cls.gensql.get_all_tables()` method.

            :param session: The database session (a ``DataBase`` object).
            :type session: DataBase

            :return: All table names in the database.
            """
            cursor = session.do(cls.gensql.get_all_tables())
            return list(map(lambda x: x[0], cursor.fetchall()))

        @classmethod
        def get_all_columns(cls, session, table_name: str) -> List[str]:
            """
            Get all columns of the table.

            .. note:
                You can copy the implementation of this method directly.

            The default implementation is based on the `cls.gensql.get_all_columns(table_name)` method.

            :param session: The database session (a ``DataBase`` object).
            :type session: DataBase
            :param table_name: The name of the table.
            :type table_name: str

            :return: `[[column_name, column_type], ...]`
            """
            cursor = session.do(cls.gensql.get_all_columns(table_name))
            return cursor.fetchall()

        @classmethod
        def get_primary_keys(cls, session, table_name: str) -> List[str]:
            """
            Return the primary-key column names of a table, in key order.

            The default implementation returns an empty list, which means
            "unknown": ``__auto`` upserts then raise instead of guessing.
            """
            return []

        @classmethod
        def begin(cls, conn) -> None:
            """
            Start an explicit transaction on an idle connection.

            The default implementation runs ``BEGIN`` on a fresh cursor, which
            is correct for SQLite (opened in autocommit mode) and MySQL.
            """
            cursor = conn.cursor()
            try:
                cursor.execute("BEGIN")
            finally:
                try:
                    cursor.close()
                except Exception:
                    pass

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

            .. note::
                I've provided a example implementation of this method, for SQLite.
                Look at the source code.

            Example Usage:

            .. code-block:: python

                TypeParser.parse(str)       # TEXT
                TypeParser.parse(int)       # INTEGER
                TypeParser.parse(float)     # REAL
                ...

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

            # round 2: Custom Types (validated: a type cannot carry extra DDL)
            if isinstance(type_, str):
                return check_type_sql(type_)

            # Not Supported
            raise TypeError(f"Type `{str(type_)}` not supported.")

    @staticmethod
    def connect(db_name: str, **kwargs) -> "BaseDriver.Conn":
        """
        Connect to the database.

        :param db_name: The name of the database to connect.
        :type db_name: str
        :param kwargs: The parameters of the connection. E.g., `host`, `port`, `user`, `password`, ...

        :return: The connection object of the database.
        :rtype: BaseDriver.Conn
        """
        pass
