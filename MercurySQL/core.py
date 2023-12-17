"""
Copyright (c) Bernie Huang 2023, all rights reserved.

MercurySQL.core
===============
Core logic of MercurySQL.

This file contains the implementation of a SQL database wrapper class and related classes for table and query expressions.

(Note): This code is a simplified implementation and may not cover all possible use cases. Please refer to the official documentation for more information.


Classes
-------
- `DataBase`: Represents a SQL database and provides methods for creating tables, executing SQL commands, and retrieving table objects.
- `Table`: Represents a table in the SQL database and provides methods for adding columns, deleting columns, inserting rows, and executing queries.

Methods
-------
- `set_driver`: Set the default driver for the `DataBase` class.
"""
from typing import Any, Union, List, Tuple
from .drivers.base import BaseDriver
from .errors import *


# ========= Basic Info =========
import os

real_path = os.path.dirname(os.path.realpath(__file__))

with open(os.path.join(real_path, 'VERSION'), encoding='utf-8') as f:
    __version__ = f.read().strip()

# ========= Tool Functions =========
default_driver = None
def set_driver(driver):
    global default_driver
    default_driver = driver

def check_version(version: str) -> bool:
    """
    Check whether the version is supported.

    :param version: The version to check.
    :type version: str

    :return: Whether the version is supported.
    :rtype: bool
    """
    cv = list(map(int, __version__.split('.'))) # current version
    dv = list(map(int, version.split('.')))     # driver version

    vdiff = [cv[i] - dv[i] for i in range(len(cv))]

    # major version
    if vdiff[0] != 0:
        return False
    # minor version (driver is older)
    if vdiff[1] > 0:
        return False
    
    return True


# ========= Class Decorations =========


class BasicExp:
    pass    # [Helper Class]


class DataBase:
    pass


class Table:
    pass


class Exp:
    pass


# ========= Classes =========
class DataBase:
    """
    Select/Create/Connect a SQL database.
    """

    def __init__(self, db_name: str, driver=None, **kwargs):
        """
        Create a new database object.

        :param db_name: The name of the database.
        :type db_name: str

        Example Usage:

        .. code-block:: python

            db = DataBase('test.db')

        How It Works:
            - start a connection to the SQL database, using the driver specified by `driver` parameter or `set_driver()` method.
            - get a cursor to execute sql commands.
            - gather all infomations of the database, for further usages.
        """
        if driver is None:
            driver = default_driver

        if driver is None or not issubclass(driver, BaseDriver):
            raise NotSpecifiedError("Driver not specified.")
        
        if not check_version(driver.version):    # check version
            raise DriverIncompatibleError(driver.__name__, driver.version, __version__)

        self.driver = driver()
        self.conn = driver.connect(db_name, **kwargs)
        self.cursor = self.conn.cursor()

        self.info = {
            "name": db_name
        }

        self.template = None
        self.template_params = {}

        self._gather_info()

    def _gather_info(self):
        """
        [Helper]
        Gather all infomations of the database, including:
          - all tables
        """
        self.tables = self.driver.APIs.get_all_tables(self.conn)
        self.tables = {tname: Table(self, tname) for tname in self.tables}

    def do(self, *sql: str, paras: List[tuple] = []):
        """
        Execute a sql command on the database.

        :param sql: The sql command(s).
        :type sql: str
        :param paras: The parameters for the sql command(s).
        :type paras: List[tuple]

        :return: The cursor of the database.
        :rtype: Driver.Cursor

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
            - commit after all commands are executed
        """
        # Recommended to use `db.do(sql1, sql2)` instead of `db.do([sql1, sql2])`.
        if isinstance(sql[0], list):
            sql = sql[0]

        if len(paras) < len(sql):
            paras += [()] * (len(sql) - len(paras))

        # start a new cursor
        c = self.conn.cursor()

        # for each sql command
        for i in range(len(sql)):
            cmd = sql[i].replace('___!!!PAYLOAD!!!___',
                                 self.driver.payload)  # replace payload

            c.execute(cmd, paras[i])

        # commit changes
        try:
            self.conn.commit()
        except: # unread errors
            pass

        return c

    def setTemplate(self, template: dict, **kwargs) -> None:
        """
        Set the template, so new table's structure will be setted to this template. 
        You can specifd the template by using `template=...` parameter into `db.createTable()` method.
        Or set it after the table is created, using `table.struct()`.

        :param template: The template to set.
        :type template: dict
        :param \*\*kwargs: The parameters for the template. E.g., `primaryKey='id'`.

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

    def createTable(self, *table_names: str, force: bool = False, template=None) -> Table:
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
        already_exists = False

        for table_name in table_names:
            if table_name in self.tables:
                already_exists = True
                if not force:
                    raise DuplicateError(f"Table `{table_name}` already exists.")

            table = Table(self, table_name)

            # set template
            if not already_exists and template is not None:
                table.struct(template, **self.template_params)

            # must be executed after `_gather_into()`, because the following code will use a mapping between table name and table object
            self.tables[table_name] = table

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

        .. note:: The only difference between `__getitem__()` and `createTable()` is that `__getitem__()` will return the **OLD** `Table` Object if exists, while `createTable()` will return a **NEW** `Table` Object.
        """
        if key in self.tables:
            return self.tables[key]
        else:
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
            if table_name not in self.tables:
                raise NotExistsError(f"Table `{table_name}` not exists.")

            cmd = self.driver.APIs.gensql.drop_table(table_name)
            self.do(cmd)

            del self.tables[table_name]

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

    def __del__(self):
        """
        Close the connection when the object is deleted.
        """
        try:
            self.conn.close()
        except AttributeError:
            # Not initialized
            pass


class Table:
    """
    A table in a SQL database.
    """

    def __init__(self, db: DataBase, table_name: str):
        """
        Initialize a table object.

        :param db: The database object.
        :type db: DataBase
        :param table_name: The name of the table.
        :type table_name: str

        Example Usage:

        .. code-block:: python

            db = DataBase('test.db')
            table = db['test']

        How It Works:
            - gather all infomations of the table, including columns name and their types.
            - set `isEmpty` to True if the table doesn't have any columns. This variable will effect how the `newColumn()` method works.
        """
        self.db = db
        self.table_name = table_name
        self.driver = db.driver

        all_tables = self.driver.APIs.get_all_tables(self.db.conn)
        self.isEmpty = (table_name not in all_tables)

        self._gather_info()

    def _gather_info(self):
        """
        [Helper] Gather all infomations of the table, including:
            - `columns`: list[str] .................. name of all columns
            - `columnsType`: dict[str, str] .......... the type of each column
        """
        if not self.isEmpty:
            self.column_info = self.driver.APIs.get_all_columns(self.db.conn, self.table_name)
        else:
            self.column_info = []

        self.columns = list(map(lambda x: x[0], self.column_info))  # [name, type]
        self.columnsType = {self.column_info[i][0]: self.column_info[i][1] for i in range(
            len(self.column_info))}

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
        if key not in self.columns:
            raise NotExistsError(f"Column `{key}` not exists.")

        return Exp(key, table=self, _str=self.columnsType[key])

    def __setitem__(self, key: str, value: Any) -> None:
        """ 
        Create a new column in the table.

        :param key: The name of the column.
        :type key: str
        :param value: The type of the column.
        :type value: Any. Can be single un-parsed type (e.g. `int`, `str(5)`, ...) OR a tuple in the form of `(type, options)`. (e.g. `(int, 'primary key', 'auto increment')`)

        Options in `value`:
        - 'primary key': Set the column as the primary key of the table.
        - 'auto increment': Set the column as an auto-incremented column.

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
            'primary key': False,
            'auto increment': False,
        }

        if isinstance(value, tuple):
            # (type, options)
            for i in range(1, len(value)):
                options[value[i].lower()] = True
            value = value[0]

        self.newColumn(
            key, value, 
            primaryKey=options['primary key'], 
            autoIncrement=options['auto increment'],
            force=True
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

            def __getattribute__(self, __name: str) -> Any:
                """
                The main method of this class, used to get the value of a column.

                :param __name: The name of the column.
                :type __name: str

                :return: The value of the column.
                """
                data = object.__getattribute__(self, 'data')
                return data[__name]

            def __iter__(self):
                """
                Make it possible to iterate through.
                It will work as a `dict`.
                """
                return iter(self.data)

        def __init__(self, table: Table, exp: Exp, selection: str = '*'):
            values = exp.query(table, selection)
            keys = table.columns if selection == '*' else list(
                map(lambda x: x.strip(), selection.split(',')))
            self.data = [
                {
                    keys[i]: value[i] for i in range(len(keys))
                } for value in values
            ]

        def __getitem__(self, index: int) -> Any:
            return self.QueryResultRow(self.data[index])

        def __iter__(self):
            return iter(self.data)

        def __len__(self):
            return len(self.data)

    def select(self, exp: Exp = None, selection: str = '*') -> list:
        """
        Select data from the table.

        :param exp: The query expression.
        :type exp: Exp
        :param selection: The columns to select, default is '*'(all columns).
        :type selection: str

        :return: A list of data.
        :rtype: list

        Example Usage:

        .. code-block:: python

            table = db['test']
            table.select(table['id'] == 1)  # select all columns where id = 1

        How It Works:
            - Construct a `QueryResult` object, which will execute the query whthin it's `QueryResult.__init__()` method.
            - return a `QueryResult` object with results.
        """
        if exp is None:
            exp = Exp(1, '=', 1)

        return self.QueryResult(self, exp, selection)

    def newColumn(self, name: str, type_: Any, force=False, primaryKey=False, autoIncrement=False) -> None:
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
        if name in self.columns:
            if not force:
                raise DuplicateError(f"Column `{name}` already exists.")
            else:
                return

        type_ = self.driver.TypeParser.parse(type_)

        if self.isEmpty:
            # create it first
            cmd = self.driver.APIs.gensql.create_table_if_not_exists(
                self.table_name, name, type_, 
                primaryKey=primaryKey,
                autoIncrement=autoIncrement,
            )
            self.db.do(cmd)
            self.isEmpty = False
        else:
            cmd = self.driver.APIs.gensql.add_column(self.table_name, name, type_)
            self.db.do(cmd)

            if primaryKey:
                self.setPrimaryKey(name, type_)

        self.columns.append(name)
        self.columnsType[name] = type_

    def struct(self, columns: dict, force=True, primaryKey: str = None, autoIncrement=False) -> None:
        """
        Set the structure of the table.

        :param columns: The structure of the table.
        :type columns: dict
        :param force: Allow to skip when column exist and have the same type at the same time.
        :type force: bool
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
        for name, type_ in columns.items():
            type_origin = type_
            type_ = self.driver.TypeParser.parse(type_)
            isPrimaryKey = (name == primaryKey)

            if name in self.columns:
                if type_.lower() != self.columnsType[name].lower():
                    raise ConfilictError(
                        f"Column `{name}` with different types (`{self.columnsType[name]}`) already exists. While trying to add column `{name}` with type `{type_}`.")
                elif not force:
                    raise DuplicateError(
                        f"Column `{name}` already exists. You can use `force=True` to avoid this error.")
            else:
                self.newColumn(name, type_origin, primaryKey=isPrimaryKey, autoIncrement=autoIncrement)

    def delColumn(self, name: str) -> None:
        if name not in self.columns:
            # column not exist
            raise NotExistsError(f"Column `{name}` not exist!")
        elif len(self.columns) == 1:
            # the last column, delete the table instead
            self.db.deleteTable(self.table_name)
        else:
            # delete the column
            self.columns.remove(name)
            cmd = self.driver.APIs.gensql.drop_column(name)
            self.db.do(cmd)

    def setPrimaryKey(self, keyname: str, keytype: str) -> None:
        """
        Set a column as the primary key of the table.

        :param keyname: The name of the column.
        :type keyname: str
        :param keytype: The type of the column, been parsed by `TypeParser`.
        :type keytype: str

        Example Usage:

        .. code-block:: python

            table = db['test']
            table.setPrimaryKey('id')

        """
        cmd = self.driver.APIs.gensql.set_primary_key(self, keyname, keytype)
        self.db.do(cmd)

    def insert(self, __auto=False, **kwargs) -> None:
        """
        Insert a row into the table.

        :param \_\_auto: Whether to update the row if it already exists.
        :type \_\_auto: bool
        :param \*\*kwargs: The data to insert.

        Example Usage:

        .. code-block:: python

            table = db['test']
            table.insert(id=1, name='Bernie', age=15, __auto=True)

        """
        # get keys and clean them
        keys = list(kwargs.keys())
        keys.remove('__auto')

        columns = ', '.join(keys)
        values = ', '.join([self.driver.payload for _ in range(len(keys))])

        # Determine the SQL command based on the value of `__auto`
        if __auto:
            cmd = self.driver.APIs.gensql.insert_or_update(
                self.table_name, columns, values)
        else:
            cmd = self.driver.APIs.gensql.insert(
                self.table_name, columns, values)

        self.db.do(cmd, paras=[tuple(kwargs[k] for k in keys)])

    def update(self, exp: Exp, **kwargs) -> None:
        """
        Update the table.

        :param exp: The query expression.
        :type exp: Exp
        :param \*\*kwargs: The data to update.

        Example Usage:

        .. code-block:: python

            table = db['test']
            table.update(table['id'] == 1, name='Bernie', age=15)

        """
        columns = ', '.join(
            [f"{key} = {self.driver.payload}" for key in kwargs.keys()])
        values = tuple(kwargs.values())

        condition, paras = exp.formula()

        cmd = self.driver.APIs.gensql.update(
            self.table_name, columns, condition)
        self.db.do(cmd, paras=[values + paras])


class BasicExp:
    def __init__(self, exp1, oper='', exp2=None):
        self.exp1 = exp1
        self.oper = oper
        self.exp2 = exp2
        self._formula = ('', ())

        self.gen_formula()

    @staticmethod
    def convert(value: Any) -> Tuple[str, tuple]:
        """
        Convert value into a form that can be used in a SQL query.

        :param value: The value to convert.
        :type value: Any

        :return: The converted value in the form of `(sql_command, paras)`.
        :rtype: Tuple[str, tuple]

        Example Usage:

        .. code-block:: python

            BasicExp.convert(1)                 # ('?', (1,))
            BasicExp.convert('Bernie')          # ('?', ('Bernie',))
            BasicExp.convert(None)              # ('', ())
            BasicExp.convert(Exp('id') == 1)    # ('(id = ?)', (1,))
            ...

        """
        if isinstance(value, BasicExp):
            formula, paras = value.formula()
        elif value is None:
            formula, paras = '', ()
        else:
            formula, paras = '___!!!PAYLOAD!!!___', (value,)

        return formula, paras

    def gen_formula(self) -> None:
        """
        [Helper] Generate the formula of the expression.

        .. note :: You can also construct a formula by yourself, just set the `_formula` attribute to a tuple in the form of `(sql_command, paras)`.
        """
        if self.oper == '':
            self._formula = self.exp1, ()
        else:
            exp1 = BasicExp.convert(self.exp1)
            exp2 = BasicExp.convert(self.exp2)

            self._formula = f"({exp1[0]} {self.oper} {exp2[0]})", tuple(
                exp1[1] + exp2[1])

    def formula(self) -> Tuple[str, tuple]:
        """
        Return the formula of the expression in the form of (sql_command, paras).
        """
        return self._formula


class Exp(BasicExp):
    def __init__(self, o1, op='', o2='', **kwargs):
        """
        Acceptable addition attributes:
        - table: Table ...................... the table to search
        - _str: str ......................... the string to show when print the object
        """
        super().__init__(o1, op, o2)

        self.table = kwargs.get('table', None)
        self._str = kwargs.get('_str', '<MercurySQL.core.Exp object>')

        if isinstance(o1, Exp):
            self.table = self.table or o1.table
        if isinstance(o2, Exp):
            self.table = self.table or o2.table

    def __eq__(self, __value: Union[Exp, int, str]) -> Exp:
        return Exp(self, '=', __value)

    def __ne__(self, __value: Union[Exp, int, str]) -> Exp:
        return Exp(self, '<>', __value)

    def __lt__(self, __value: Union[Exp, int, str]) -> Exp:
        return Exp(self, '<', __value)

    def __le__(self, __value: Union[Exp, int, str]) -> Exp:
        return Exp(self, '<=', __value)

    def __gt__(self, __value: Union[Exp, int, str]) -> Exp:
        return Exp(self, '>', __value)

    def __ge__(self, __value: Union[Exp, int, str]) -> Exp:
        return Exp(self, '>=', __value)

    def between(self, __value1: Union[Exp, int, str], __value2: Union[Exp, int, str]) -> Exp:
        # construct a new Exp object manually: set the `_formula` attribute to `(sql, paras)`.
        res = Exp(self, 'BETWEEN', __value1)

        exp1 = res.formula()
        exp3 = BasicExp.convert(__value2)

        # set the `_formula` attribute.
        res._formula = f"({exp1[0]} AND {exp3[0]})", tuple(exp1[1] + exp3[1])

        return res

    def in_(self, __value: Union[list, tuple, set]) -> Exp:
        return Exp(self, 'IN', str(tuple(__value)))

    def like(self, __value: str) -> Exp:
        return Exp(self, 'LIKE', __value)

    def __and__(self, __value: Union[Exp, int, str]) -> Exp:
        return Exp(self, 'AND', __value)

    def __or__(self, __value: Union[Exp, int, str]) -> Exp:
        return Exp(self, 'OR', __value)

    def __invert__(self) -> Union[Exp, int, str]:
        return Exp('', 'NOT', self)

    def query(self, table=None, select='*') -> list:
        """
        Execute query.
        """
        self.table = table or self.table
        self.driver = self.table.db.driver

        if self.table is None:
            raise NotSpecifiedError("Table not specified.")
        if not isinstance(self.table, Table):
            raise NotExistsError(f"Table `{self.table.table_name}` not exists.")

        condition, paras = self.formula()

        cmd = self.driver.APIs.gensql.query(
            self.table.table_name, select, condition)
        res = self.table.db.do(cmd, paras=[paras])
        return res.fetchall()

    def __iter__(self):
        """
        use magic method `__iter__` to search.
        """
        return iter(self.query())

    def delete(self, table=None) -> None:
        """
        Execute delete.
        """
        self.table = table or self.table

        if self.table is None:
            raise NotSpecifiedError("Table not specified.")
        if not isinstance(self.table, Table):
            raise NotExistsError(f"Table `{self.table.table_name}` not exists.")

        condition, paras = self.formula()

        cmd = self.driver.APIs.gensql.delete(self.table.table_name, condition)
        self.table.db.do(cmd, paras=[paras])

    def __str__(self):
        return self._str

