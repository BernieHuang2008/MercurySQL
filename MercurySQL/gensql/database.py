"""
Copyright (c) Bernie Huang 2023, all rights reserved.

MercurySQL.gensql.database
==========================
This file contains the DataBase class, and a tool function `set_driver` as well.

Classes
-------
- `DataBase`: Represents a SQL database and provides methods for creating tables, executing SQL commands, and retrieving table objects.

Methods
-------
- `set_driver`: Set the default driver for the `DataBase` class.
"""
import os
import re
from contextlib import contextmanager
from typing import List

from ..orm.command_queue import CommandQueue
from ..drivers import BaseDriver
from ..errors import *

from .table import Table


# ========= Collect Infos =========
real_path = os.path.dirname(os.path.realpath(__file__))

with open(os.path.join(real_path, "..", "VERSION"), encoding="utf-8") as f:
    __version__ = f.read().strip()


# ========= Tool Functions =========
default_driver = None

#: Statements starting with these keywords do not change the data, so the
#: generation counter (used to invalidate cached query results) is not bumped.
_READ_ONLY_RE = re.compile(r"^\s*(?:SELECT|PRAGMA|EXPLAIN|SHOW|DESCRIBE)\b", re.I)


def set_driver(driver):
    """
    Set the default driver for the database, so you won't need to specify the driver for each DB every time.
    """
    global default_driver
    default_driver = driver


def _parse_version(version: str) -> List[int]:
    parts = [part for part in str(version).strip().split(".") if part != ""]
    if not parts:
        raise ValueError(f"`{version}` is not a version number.")
    try:
        return [int(part) for part in parts]
    except ValueError:
        raise ValueError(f"`{version}` is not a version number.") from None


def check_version(version: str) -> bool:
    """
    Check whether the version is supported.

    A driver is compatible when it has the same major version and is not older
    than MercurySQL itself. Two-part versions such as ``"0.2"`` are padded with
    zeros instead of raising :class:`IndexError`.

    :param version: The version to check.
    :type version: str

    :return: Whether the version is supported.
    :rtype: bool
    """
    try:
        cv = _parse_version(__version__)   # current version
        dv = _parse_version(version)       # driver version
    except ValueError:
        return False

    length = max(len(cv), len(dv))
    cv += [0] * (length - len(cv))
    dv += [0] * (length - len(dv))

    # major version must match
    if cv[0] != dv[0]:
        return False
    # the driver must not be older than the core
    if dv[1] < cv[1]:
        return False

    return True


# ========== Classes ==========
class DataBase:
    """
    Select/Create/Connect a SQL database.

    The instance of this class represents a SQL database, and provides methods for creating tables, executing SQL, and retrieving table objects.

    Example Usage:

    .. code-block:: python

        from MercurySQL import DataBase
        from MercurySQL.drivers.sqlite import Driver_SQLite

        with DataBase("test.db", driver=Driver_SQLite) as db:
            table = db["test"]
            table.struct({"id": int, "name": str}, primaryKey="id")
            table.insert(id=1, name="Bernie")

    .. versionchanged:: 0.2.0
       A failed statement now raises instead of blocking the caller forever,
       ``do()`` is transactional, and the database can (and should) be closed
       with :meth:`close` or by using it as a context manager.
    """

    def __init__(self, db_name: str, driver=None, timeout: float = None, **kwargs):
        """
        Create a new database object.

        :param db_name: The name of the database.
        :type db_name: str
        :param driver: The driver class. Defaults to the one set by
            :func:`set_driver`.
        :param timeout: Seconds to wait for a statement before raising
            :class:`QueueTimeoutError`. ``None`` means "wait until it finishes".
        :param kwargs: Connection arguments forwarded to ``driver.connect()``.

        Example Usage:

        .. code-block:: python

            db = DataBase('test.db')

        How It Works:
            - start a connection to the SQL database, using the driver specified by `driver` parameter or `set_driver()` method.
            - create a new `CommandQueue` to handle all SQL commands in this DB.
            - gather all infomations of the database, for further usages.
        """
        if driver is None:
            driver = default_driver

        if driver is None:
            raise NotSpecifiedError(
                "Driver not specified. Pass `driver=...` or call "
                "`MercurySQL.set_driver(...)` first."
            )
        if not isinstance(driver, type) or not issubclass(driver, BaseDriver):
            raise NotSpecifiedError(
                f"`{driver!r}` is not a MercurySQL driver (it must be a subclass "
                "of `MercurySQL.drivers.BaseDriver`)."
            )

        self.driver = driver

        if not check_version(driver.version):  # check version
            raise DriverIncompatibleError(driver.__name__, driver.version, __version__)

        self.info = {"name": db_name}

        self.template = None
        self.template_params = {}

        self._closed = False
        self._generation = 0

        # The worker thread opens the connection, so a connect failure is
        # raised here instead of hanging on the first statement.
        self.cq = CommandQueue(driver, db_name, timeout=timeout, **kwargs)

        self._gather_info()

    # ------------------------------------------------------------------ #
    # Schema
    # ------------------------------------------------------------------ #
    def _gather_info(self):
        """
        [Helper]
        Gather all infomations of the database, including:
          - all tables
        """
        names = self.driver.APIs.get_all_tables(self)
        self.tables = {
            name: Table(self, name, known_tables=names) for name in names
        }

    def _resolve_table(self, name: str):
        """
        Return the key in ``self.tables`` that refers to `name`, or ``None``.

        SQLite table names are case-insensitive, so ``db["users"]`` must find the
        table created as ``db.createTable("Users")`` instead of inventing a
        second, empty object for it.
        """
        if name in self.tables:
            return name
        if self.driver.table_name_case_insensitive:
            lowered = name.lower()
            for key in self.tables:
                if key.lower() == lowered:
                    return key
        return None

    # ------------------------------------------------------------------ #
    # Execution
    # ------------------------------------------------------------------ #
    @property
    def generation(self) -> int:
        """
        A counter that grows every time the database is written.

        It lets cached query results (e.g. :class:`Exp` iteration) know that
        they are stale.
        """
        return self._generation

    def do(self, *sql: str, paras: List[tuple] = None, timeout: float = None):
        """
        Execute a sql command on the database.

        :param sql: The sql command(s).
        :type sql: str
        :param paras: The parameters for the sql command(s), one tuple per statement.
        :type paras: List[tuple]
        :param timeout: Seconds to wait before raising. Defaults to the timeout
            given to the constructor.

        :return: The result of the **last** statement (a :class:`CQResult`).
        :rtype: CQResult

        Example Usage:

        .. code-block:: python

            db = DataBase('test.db')
            db.do("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
            db.do("INSERT INTO test (name) VALUES (?)", paras=[('Bernie',)])
            db.do(
                "SQL1",
                "SQL2",
                paras=[
                       (paras1, paras2),
                       (paras3, paras4)
                ])

        How It Works:
            - execute sql commands one by one, with parameters
            - **all commands run in one transaction**: they are committed only if
              every statement succeeded, and the whole batch is rolled back if
              one of them fails. The failure is raised to the caller.

        .. versionchanged:: 0.2.0
           Errors are raised instead of being printed and silently ignored, and
           a failed batch no longer commits the statements that came before it.
        """
        if not sql:
            raise ValueError("`do()` needs at least one SQL statement.")

        # Recommended to use `db.do(sql1, sql2)` instead of `db.do([sql1, sql2])`.
        if isinstance(sql[0], list):
            sql = tuple(sql[0])

        statements = list(sql)
        for statement in statements:
            if not isinstance(statement, str):
                raise TypeError(
                    f"SQL statement must be a `str`, got `{type(statement).__name__}`."
                )

        # Never mutate the caller's list (the old code did `paras += ...`).
        param_list = list(paras) if paras else []
        if len(param_list) < len(statements):
            param_list += [()] * (len(statements) - len(param_list))

        batch = [
            (statement, () if params is None else params)
            for statement, params in zip(statements, param_list)
        ]

        result = self.cq.execute_batch(batch, timeout=timeout)

        if not all(_READ_ONLY_RE.match(statement) for statement in statements):
            self._generation += 1

        return result

    @contextmanager
    def transaction(self, timeout: float = None):
        """
        Group several ``do()`` / ORM calls into one transaction.

        Example Usage:

        .. code-block:: python

            with db.transaction():
                table.insert(id=1, name="a")
                table.insert(id=2, name="b")

        The transaction is committed on success and rolled back if the block
        raises. If a statement inside the block fails, the transaction is
        rolled back immediately and the following ``commit`` raises
        :class:`TransactionError`.

        .. versionadded:: 0.2.0
        """
        self.cq.begin(timeout)
        try:
            yield self
        except BaseException:
            self.cq.rollback(timeout)
            raise
        else:
            self.cq.commit(timeout)
            self._generation += 1

    # ------------------------------------------------------------------ #
    # Tables
    # ------------------------------------------------------------------ #
    def setTemplate(self, template: dict, **kwargs) -> None:
        """
        Set the template, so new table's structure will be setted to this template.
        You can specifd the template by using `template=...` parameter into `db.createTable()` method.
        Or set it after the table is created, using `table.struct()`.

        :param template: The template to set.
        :type template: dict
        :param \\*\\*kwargs: The parameters for the template. E.g., `primaryKey='id'`.

        Example Usage:

        .. code-block:: python

            db = DataBase('test.db')
            db.setTemplate({
                'id': int,
                'name': str
            })
            table = db.createTable('test')

        """
        self.template = template
        self.template_params = kwargs

    def createTable(
        self, *table_names: str, force: bool = False, template=None
    ) -> Table:
        """
        create a table in the database.

        :param table_names: The name of the table.
        :type table_names: str
        :param force: Allow to return an existing table.
        :type force: bool

        :return: A Table object.
        :rtype: Table

        Example Usage:

        .. code-block:: python

            db = DataBase('test.db')
            table = db.createTable('test')

        How It Works:
            - create table(s) if not exists
            - if already exists, return the existing table(s) in a NEW `Table` Object.
            - if exists and `force` set to False, raise an Exception.
        """
        # using template in `self.template` if not specified
        if template is None:
            template = self.template

        tables = []

        for table_name in table_names:
            physical = self._resolve_table(table_name)

            if physical is not None and not force:
                raise DuplicateError(f"Table `{table_name}` already exists.")

            table = Table(self, physical or table_name)

            # set template only for a table that is really new
            if physical is None and template is not None:
                table.struct(template, **self.template_params)

            # must be executed after `_gather_info()`, because the following code will use a mapping between table name and table object
            self.tables[table.table_name] = table

            tables.append(table)

        return tables if len(tables) > 1 else tables[0]

    def __getitem__(self, key: str) -> Table:
        """
        Create / Choose a table from the database.

        :param key: The name of the table.
        :type key: str

        :return: A Table object.
        :rtype: Table

        Example Usage:

        .. code-block:: python

            db = DataBase('test.db')
            table = db['test']

        How It Works:
            - if exists, return the existing table (the OLD `Table` Object)
            - if not exists, create a new table by `createTable()`.

        .. note::
           The only difference between `__getitem__()` and `createTable()` is that `__getitem__()` will return the **OLD** `Table` Object if exists, while `createTable()` will return a **NEW** `Table` Object.

           **See the "How It Works" section in `createTable()` for more details.**
        """
        physical = self._resolve_table(key)
        if physical is not None:
            return self.tables[physical]
        return self.createTable(key, force=True)

    def deleteTable(self, *table_names: str) -> None:
        """
        delete a table in the database.

        :param table_names: The name of the table.
        :type table_names: str

        Example Usage:

        .. code-block:: python

            db = DataBase('test.db')
            db.deleteTable('test')

        How It Works:
            - delete table(s) if exists
            - raise an Exception if not exists.
        """
        for table_name in table_names:
            physical = self._resolve_table(table_name)
            if physical is None:
                raise NotExistsError(f"Table `{table_name}` not exists.")

            cmd = self.driver.APIs.gensql.drop_table(physical)
            self.do(cmd)

            del self.tables[physical]

    def __delitem__(self, key: str) -> None:
        """
        Delete a table from the database, same as `deleteTable()`.

        :param key: The name of the table.
        :type key: str

        Example Usage:

        .. code-block:: python

            db = DataBase('test.db')
            del db['test']  # same as db.deleteTable('test')

        """
        self.deleteTable(key)

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #
    @property
    def closed(self) -> bool:
        """Whether :meth:`close` has been called."""
        return self._closed

    def close(self) -> None:
        """
        Close the connection and stop the background thread.

        Safe to call more than once. The object cannot be used after this; use it
        as a context manager (``with DataBase(...) as db:``) to be sure it is
        always called.

        .. versionadded:: 0.2.0
        """
        if self._closed:
            return
        self._closed = True
        self.cq.close()

    #: Alias of :meth:`close`, for people used to other ORMs.
    dispose = close

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
