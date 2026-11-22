"""
MercurySQL.gensql.table
=======================
This file contains the `Table` class and related classes for handling tables & queries in the SQL database.

Classes
-------
- `Table`: Represents a table in the SQL database and provides methods for adding columns, deleting columns, inserting rows, and executing queries.
- `QueryResult`: Represents the result of a query and provides methods for accessing the query results.

.. versionchanged:: 0.2.0
   * Identifiers are resolved case-insensitively where the backend is
     case-insensitive, so `db["users"]` no longer creates a phantom duplicate of
     `db["Users"]`.
   * `selection` only accepts known column names (or an explicit
     ``raw=True`` opt-out); it is quoted, never pasted in raw.
   * `insert(..., __auto=True)` is a real UPSERT and needs a primary key.
   * `delColumn()` refuses to drop the last column instead of silently
     dropping the whole table.
"""

from typing import Any, Dict, Iterable, List, Optional, Tuple

from ..errors import *
from .exp import Exp


class Table:
    """
    Represents a table in a SQL database. Can be created by `db.createTable()`.

    It provides methods for adding columns, deleting columns, inserting rows, and executing queries, etc.
    """

    def __init__(self, db, table_name: str, known_tables: List[str] = None):
        """
        Initialize a table object.

        :param db: The database object.
        :type db: DataBase
        :param table_name: The name of the table.
        :type table_name: str
        :param known_tables: The table names already read from the database, to
            avoid one `get_all_tables()` round trip per table.

        Example Usage:

        .. code-block:: python

            db = DataBase('test.db')
            table = db['test']

        How It Works:
            - gather all infomations of the table, including columns name and their types.
            - set `isEmpty` to True if the table doesn't have any columns. This variable will effect how the `newColumn()` method works.
        """
        self.db = db
        self.driver = db.driver

        if known_tables is None:
            known_tables = self.driver.APIs.get_all_tables(self.db)
        physical = self._match_table_name(table_name, known_tables)

        # Use the name the database knows, not the casing the caller used:
        # SQLite treats `Users` and `users` as the same table.
        self.table_name = physical if physical is not None else table_name
        self.isEmpty = physical is None
        self._primary_keys = None

        self._gather_info()

    def _match_table_name(self, name: str, candidates: Iterable[str]) -> Optional[str]:
        """Return the existing name that refers to the same table, if any."""
        candidates = list(candidates)
        if name in candidates:
            return name
        if self.driver.table_name_case_insensitive:
            lowered = name.lower()
            for candidate in candidates:
                if candidate.lower() == lowered:
                    return candidate
        return None

    def _gather_info(self):
        """
        [Helper] Gather all infomations of the table, including:
            - `columns`: list[str] .................. name of all columns
            - `columnsType`: dict[str, str] .......... the type of each column
        """
        if not self.isEmpty:
            self.column_info = self.driver.APIs.get_all_columns(
                self.db, self.table_name
            )
        else:
            self.column_info = []

        self.columns = list(map(lambda x: x[0], self.column_info))  # [name, type]
        self.columnsType = {
            self.column_info[i][0]: self.column_info[i][1]
            for i in range(len(self.column_info))
        }
        self._primary_keys = None

    # ------------------------------------------------------------------ #
    # Identifier resolution
    # ------------------------------------------------------------------ #
    def resolveColumn(self, name: str) -> str:
        """
        Return the column name as the database spells it.

        SQLite (and MySQL columns) are case-insensitive: `table["ID"]` must
        refer to the same column as `table["id"]`. The cached schema is compared
        case-insensitively, and the canonical name is returned.

        :raises NotExistsError: when the column does not exist.
        """
        if not isinstance(name, str):
            raise TypeError(
                f"Column name must be a `str`, got `{type(name).__name__}`."
            )
        if name in self.columns:
            return name
        if self.driver.column_name_case_insensitive:
            lowered = name.lower()
            for column in self.columns:
                if column.lower() == lowered:
                    return column
        raise NotExistsError(f"Column `{name}` not exists.")

    @property
    def primaryKeys(self) -> List[str]:
        """The primary-key columns of the table, in key order."""
        if self._primary_keys is None:
            self._primary_keys = list(
                self.driver.APIs.get_primary_keys(self.db, self.table_name)
            )
        return self._primary_keys

    def _quote(self, name: str) -> str:
        return self.driver.APIs.quote_ident(name)

    def _build_selection(self, selection="*", raw: bool = False) -> Tuple[str, List[str]]:
        """
        Validate and quote a projection.

        :param selection: ``"*"``, a comma separated string of column names, or
            an iterable of column names.
        :param raw: Accept the string as raw SQL. Only use it with trusted input.
        :return: ``(quoted_sql, column_names)``. ``column_names`` is ``None``
            for a raw projection (the real names are taken from the cursor).
        """
        if raw:
            if not isinstance(selection, str):
                raise TypeError("`raw=True` requires a `str` selection.")
            return selection, None

        if selection is None:
            selection = "*"

        if isinstance(selection, str):
            if selection.strip() == "*":
                return "*", list(self.columns)
            parts = [part.strip() for part in selection.split(",")]
            parts = [part for part in parts if part]
        elif isinstance(selection, (list, tuple, set)):
            parts = [str(part).strip() for part in selection]
        else:
            raise TypeError(
                "`selection` must be '*', a comma separated string of column "
                f"names, or an iterable of column names, not `{type(selection).__name__}`."
            )

        if not parts:
            raise ValueError("`selection` must name at least one column.")

        keys: List[str] = []
        for part in parts:
            canonical = self.resolveColumn(part)
            if canonical not in keys:
                keys.append(canonical)

        quoted = ", ".join(self._quote(key) for key in keys)
        return quoted, keys

    def __getitem__(self, key: str) -> Exp:
        """
        get a column from the table, mainly used to construct query.

        :param key: The name of the column.
        :type key: str

        :return: An Exp object.

        Example Usage:

        1. Construct a query expression.

        .. code-block:: python

            table = db['test']
            exp = table['id'] == 1
            res = table.select(exp)

        2. Get the definition of a column.

        .. code-block:: python

            table = db['test']
            print(table['id'])  # INTEGER PRIMARY KEY

        How It Works:
            - return an `Exp` object with `table` and `_str` attributes setted.
            - `table` is used to execute the query using `list(...)`, even if table not specified. **[NOT RECOMMENDED]**
            - `_str` is used to print the definition of a column using `str(...)`.
            - raise an Exception if column not exists.
        """
        key = self.resolveColumn(key)
        return Exp(key, table=self, _str=self.columnsType[key])

    def __setitem__(self, key: str, value: Any) -> None:
        """
        Create a new column in the table.

        :param key: The name of the column.
        :type key: str
        :param value: The type of the column.
        :type value: Any. Can be single un-parsed type (e.g. `int`, `str(5)`, ...) OR a tuple in the form of `(type, options)`. (e.g. `(int, 'primary key', 'auto increment')`)

        Options in `value`:

        - **'primary key'** — Set the column as the primary key of the table.
        - **'auto increment'** — Set the column as an auto-incremented column.

        Example Usage:

        .. code-block:: python

            table = db['test']
            table['name'] = str
            table['id'] = int, 'primary key', 'auto increment'

        How It Works:
            - get options from `value` if it has parameters (Judge it by whether it's a tuple, so you can use it as the L3 of example showed).
            - Actually create the column, using `newColumn()` method.
        """
        options = {
            "primary key": False,
            "auto increment": False,
        }

        if isinstance(value, tuple):
            # (type, options)
            for i in range(1, len(value)):
                option = str(value[i]).lower()
                if option not in options:
                    raise NotSupportedError(
                        f"Unknown column option `{value[i]}`. "
                        f"Supported options: {', '.join(options)}."
                    )
                options[option] = True
            value = value[0]

        self.newColumn(
            key,
            value,
            primaryKey=options["primary key"],
            autoIncrement=options["auto increment"],
            force=True,
        )

    def __delitem__(self, key: str) -> None:
        """
        Delete an existing column in this table.
        An Exception will be raised if column not exist.
        Same as `delColumn()`.

        :param key: The name of the column.
        :type key: str

        Example Usage:

        .. code-block:: python

            table = db['test']
            del table['name']  # same as table.delColumn('name')

        """
        self.delColumn(key)

    def select(
        self,
        exp: Exp = None,
        selection="*",
        limit: int = None,
        offset: int = None,
        raw: bool = False,
    ) -> "QueryResult":
        """
        Select data from the table.

        :param exp: The query expression.
        :type exp: Exp
        :param selection: The columns to select: `'*'`, a comma separated string
            of column names, or a list of column names. Default is `'*'`.
        :param limit: Return at most `limit` rows.
        :param offset: Skip `offset` rows (requires `limit`).
        :param raw: Treat `selection` as raw SQL. **Only use with trusted input**;
            it disables the identifier validation.

        :return: A list of data.
        :rtype: QueryResult

        Example Usage:

        .. code-block:: python

            table = db['test']
            table.select(table['id'] == 1)              # all columns where id = 1
            table.select(table['id'] == 1, ["id"])      # only the id column
            table.select(limit=10, offset=20)           # paging

        .. versionchanged:: 0.2.0
           `selection` is validated against the table's columns and quoted. A
           projection such as
           ``"id, (SELECT secret FROM users) AS leak"`` now raises
           :class:`NotExistsError` instead of exfiltrating data.
        """
        if exp is None:
            exp = Exp(1, "=", 1)

        return QueryResult(self, exp, selection, limit=limit, offset=offset, raw=raw)

    def select_iter(self, exp: Exp = None, selection="*", page_size: int = 1000):
        """
        Yield rows one by one, fetching them in pages.

        Unlike :meth:`select`, the whole table is never materialised in memory,
        which matters for large tables (see F-13 in the risk review).

        Example Usage:

        .. code-block:: python

            for row in table.select_iter(page_size=500):
                ...

        """
        if exp is None:
            exp = Exp(1, "=", 1)
        if page_size <= 0:
            raise ValueError("`page_size` must be positive.")

        selection_sql, keys = self._build_selection(selection)
        offset = 0
        while True:
            cmd, paras = exp.build_query(
                self, selection_sql, limit=page_size, offset=offset
            )
            rows = self.db.do(cmd, paras=[paras]).fetchall()
            for row in rows:
                yield dict(zip(keys, row))
            if len(rows) < page_size:
                return
            offset += page_size

    def count(self, exp: Exp = None) -> int:
        """Return the number of rows matching `exp`."""
        if exp is None:
            exp = Exp(1, "=", 1)
        cmd, paras = exp.build_query(self, "COUNT(*)")
        rows = self.db.do(cmd, paras=[paras]).fetchall()
        return int(rows[0][0]) if rows else 0

    def newColumn(
        self, name: str, type_: Any, force=False, primaryKey=False, autoIncrement=False
    ) -> None:
        """
        Add a new column to the table.

        :param name: The name of the column.
        :type name: str
        :param type_: The type of the column.
        :type type_: Any
        :param force: Allow to skip when processing an existing column.
        :type force: bool
        :param primaryKey: Whether the column is a primary key.
        :type primaryKey: bool
        :param autoIncrement: Whether the column is auto-incremented.
        :type autoIncrement: bool

        Example Usage:

        .. code-block:: python

            table = db['test']
            table.newColumn('name', str)
            table.newColumn('id', int, primaryKey=True)

        How It Works:
            - Create a new table with this column, if table is empty.
            - Add the column to an existing table.
            - Set as the `primary key` column if `primaryKey` is True.
            - Record its name and type in `self.columns` and `self.columnsType`.
        """
        try:
            existing = self.resolveColumn(name)
        except NotExistsError:
            existing = None

        if existing is not None:
            if not force:
                raise DuplicateError(f"Column `{name}` already exists.")
            return
        else:
            # Make sure the name is a usable identifier before anything runs.
            self._quote(name)

        type_ = self.driver.TypeParser.parse(type_)

        if self.isEmpty:
            # create it first
            cmd = self.driver.APIs.gensql.create_table_if_not_exists(
                self.table_name,
                name,
                type_,
                primaryKey=primaryKey,
                autoIncrement=autoIncrement,
            )
            self.db.do(cmd)
            self.isEmpty = False
        else:
            cmd = self.driver.APIs.gensql.add_column(self.table_name, name, type_)
            self.db.do(cmd)

            self.columns.append(name)
            self.columnsType[name] = type_
            self._primary_keys = None

            if primaryKey:
                # SQLite cannot add a primary key in place: this rebuilds the
                # table (in one transaction) and refreshes the cached schema.
                self.setPrimaryKey(name)

            return

        self.columns.append(name)
        self.columnsType[name] = type_
        self._primary_keys = None

    def struct(
        self,
        columns: dict,
        skipError=True,
        primaryKey: str = None,
        autoIncrement=False,
        force=True,
    ) -> None:
        """
        Set the structure of the table.

        :param columns: The structure of the table.
        :type columns: dict
        :param skipError: Allow to skip when column exist and have the same type at the same time.
        :type skipError: bool
        :param primaryKey: The primary key of the table.
        :type primaryKey: str

        Example Usage:

        .. code-block:: python

            table = db['test']
            table.struct({
                'id': int,
                'name': str
            }, primaryKey='id')

        """

        # Warning: `force` will be removed in next big version
        skipError = skipError and force

        for name, type_ in columns.items():
            type_origin = type_
            type_ = self.driver.TypeParser.parse(type_)
            isPrimaryKey = name == primaryKey

            existing = None
            try:
                existing = self.resolveColumn(name)
            except NotExistsError:
                pass

            if existing is not None:
                if type_.lower() != self.columnsType[existing].lower():
                    raise ConfilictError(
                        f"Column `{name}` with different types (`{self.columnsType[existing]}`) already exists. While trying to add column `{name}` with type `{type_}`."
                    )
                elif not skipError:
                    raise DuplicateError(
                        f"Column `{name}` already exists. You can use `force=True` to avoid this error."
                    )
            else:
                self.newColumn(
                    name,
                    type_origin,
                    primaryKey=isPrimaryKey,
                    # AUTOINCREMENT only makes sense on the primary key.
                    autoIncrement=autoIncrement and isPrimaryKey,
                )

    def delColumn(self, name: str) -> None:
        """
        Delete a column.

        .. versionchanged:: 0.2.0
           Deleting the last column used to silently drop the whole table; it now
           raises :class:`NotSupportedError` -- call :meth:`DataBase.deleteTable`
           if that is really what you want.
        """
        name = self.resolveColumn(name)

        if len(self.columns) == 1:
            raise NotSupportedError(
                f"Column `{name}` is the last column of table "
                f"`{self.table_name}`; deleting it would drop the whole table. "
                "Use `db.deleteTable()` if that is intended."
            )

        cmd = self.driver.APIs.gensql.drop_column(self.table_name, name)
        self.db.do(cmd)

        self.columns.remove(name)
        self.columnsType.pop(name, None)
        self._primary_keys = None

    def setPrimaryKey(self, keyname: str, keytype: str = None) -> None:
        """
        Set a column as the primary key of the table.

        :param keyname: The name of the column.
        :type keyname: str
        :param keytype: The type of the column. Defaults to the column's current
            type; a value is parsed by `TypeParser`.

        Example Usage:

        .. code-block:: python

            table = db['test']
            table.setPrimaryKey('id')

        .. versionchanged:: 0.2.0
           The rebuild names every column explicitly in the ``CREATE`` and the
           ``INSERT ... SELECT``, and runs inside one transaction, so values no
           longer shift by one position and an interrupted rebuild cannot leave
           the data in a temporary table.
        """
        keyname = self.resolveColumn(keyname)

        if keytype is None:
            keytype = self.columnsType[keyname]
        else:
            keytype = self.driver.TypeParser.parse(keytype)

        cmds = self.driver.APIs.gensql.set_primary_key(self, keyname, keytype)
        if isinstance(cmds, str):
            cmds = [cmds]
        # One batch -> one transaction: either the rebuilt table is in place or
        # nothing changed.
        self.db.do(*cmds)

        self._gather_info()

    def insert(self, __auto=False, **kwargs) -> None:
        """
        Insert a row into the table.

        :param \\_\\_auto: Whether to update the row if it already exists.
        :type \\_\\_auto: bool
        :param \\*\\*kwargs: The data to insert.

        Example Usage:

        .. code-block:: python

            table = db['test']
            table.insert(id=1, name='Bernie', age=15, __auto=True)

        .. versionchanged:: 0.2.0
           ``__auto=True`` uses a real UPSERT (``ON CONFLICT ... DO UPDATE`` /
           ``ON DUPLICATE KEY UPDATE``): columns that are not supplied keep their
           value. It requires a primary key and raises
           :class:`NotSupportedError` otherwise.
        """
        # get keys and clean them
        keys = list(kwargs.keys())
        if "__auto" in keys:
            __auto = kwargs["__auto"]
            keys.remove("__auto")

        if not keys:
            raise ValueError("`insert()` needs at least one column.")

        resolved = [self.resolveColumn(key) for key in keys]
        values = tuple(kwargs[key] for key in keys)

        one_row = "(" + ", ".join([self.driver.payload] * len(resolved)) + ")"

        if __auto:
            primary_keys = self.primaryKeys
            if not primary_keys:
                raise NotSupportedError(
                    f"`__auto=True` needs a primary key, but table "
                    f"`{self.table_name}` has none. Use a plain `insert()`, or "
                    "give the table a primary key first."
                )
            cmd = self.driver.APIs.gensql.insert_or_update(
                self.table_name,
                resolved,
                one_row,
                primary_keys=primary_keys,
            )
        else:
            cmd = self.driver.APIs.gensql.insert(
                self.table_name, resolved, one_row
            )

        self.db.do(cmd, paras=[values])

    def insert_many(self, rows: List[Dict[str, Any]]) -> None:
        """
        Insert several rows with one statement (and one commit).

        Every row must provide the same columns.

        Example Usage:

        .. code-block:: python

            table.insert_many([
                {"id": 1, "name": "a"},
                {"id": 2, "name": "b"},
            ])

        .. versionadded:: 0.2.0
        """
        rows = list(rows)
        if not rows:
            return

        keys = list(rows[0].keys())
        if "__auto" in keys:
            raise ValueError("`insert_many()` does not support `__auto`.")
        for row in rows:
            if list(row.keys()) != keys:
                raise ValueError("Every row of `insert_many()` must have the same columns.")

        resolved = [self.resolveColumn(key) for key in keys]
        one_row = "(" + ", ".join([self.driver.payload] * len(resolved)) + ")"
        placeholders = ", ".join([one_row] * len(rows))

        params = tuple(row[key] for row in rows for key in keys)

        cmd = self.driver.APIs.gensql.insert(self.table_name, resolved, placeholders)
        self.db.do(cmd, paras=[params])

    def update(self, exp: Exp, data: dict = None, **kwargs) -> None:
        """
        Update the table.

        .. note:: We Recommend to use `(tb['id'] == 1).update(...)` then this function, for cleaner code style.

        .. warning::
           The argument of `Exp.update(...)` doesn't supports kwargs format (`name=bernie`). It only supports dict format (`{"name": "bernie"}`).
           We recommended to use 'dict format' in both `table.update` and `Exp.update`.

        ..

        :param exp: The query expression.
        :type exp: Exp
        :param data: The data to update.
        :type data: dict

        Example Usage:

        .. code-block:: python

            table = db['test']
            table.update(table['id'] == 1, name='Bernie', age=15)
            # OR
            (table['id'] == 1).update({"name": "Bernie", "age": 15})    # recommended

        """
        if not data:
            data = kwargs

        if not data:
            raise ValueError(
                "`update()` needs at least one column to update; "
                "`UPDATE t SET WHERE ...` is not valid SQL."
            )

        resolved = [self.resolveColumn(key) for key in data.keys()]
        values = tuple(data.values())

        condition, paras = exp.formula(self.driver.payload)

        cmd = self.driver.APIs.gensql.update(self.table_name, resolved, condition)
        self.db.do(cmd, paras=[values + paras])


class QueryResult:
    """
    [Helper Class]
    The result of a query.

    Example Usage:

    .. code-block:: python

        res = table.select(exp)
        for row in res:
            print(row)

    """

    class QueryResultRow:
        """
        [Helper Class]
        Representing a single row of the query result.
        You can use QueryResult[i] to get it, and use it by `row.column_name`.

        Example Usage:

        .. code-block:: python

            res = table.select(exp)
            row = res[0]
            print(row.id)

        """

        def __init__(self, data: dict):
            self.data = data

        def __getitem__(self, __name: str) -> Any:
            """
            The main method of this class, used to get the value of a column.

            :param __name: The name of the column.
            :type __name: str

            :return: The value of the column.
            """
            data = object.__getattribute__(self, "data")
            if __name__ == "data":
                return data
            else:
                return data[__name]

        def __iter__(self):
            """
            Make it possible to iterate through.
            It will work as a `dict`.
            """
            return iter(self.data)

        def __getattr__(self, name):
            try:
                return self.data[name]
            except KeyError:
                raise AttributeError(name) from None

    def __init__(
        self,
        table: Table,
        exp: Exp,
        selection="*",
        limit: int = None,
        offset: int = None,
        raw: bool = False,
    ):
        selection_sql, keys = table._build_selection(selection, raw=raw)
        cmd, paras = exp.build_query(table, selection_sql, limit=limit, offset=offset)

        result = table.db.do(cmd, paras=[paras])
        values = result.fetchall()

        if keys is None:
            keys = list(result.columns) if result.columns else []

        self.data = [dict(zip(keys, row)) for row in values]

    def __getitem__(self, index: int) -> "QueryResult.QueryResultRow":
        return self.QueryResultRow(self.data[index])

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)

    def __repr__(self):
        return f"<QueryResult rows={len(self.data)}>"
