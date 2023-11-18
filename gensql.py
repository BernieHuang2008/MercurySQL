"""
Use built-in sqlite3 library to operate sql in a more pythonic way.
"""

import sqlite3
from typing import Any, Union, List, Tuple


class DataBase: pass
class Table: pass
class BasicExp: pass
class Exp: pass


class DataBase:
    """
    select/create a SQLite database using python's built-in library `sqlite3`.
    """

    def __init__(self, db_name: str):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()

        self.info = {
            "name": db_name
        }

        self._gather_info()

    def __getitem__(self, key: str) -> Table:
        """
        get a table from the database.

        Paras:
            key: str
                The name of the table.
        """
        return self.tables[key]

    def _gather_info(self):
        """
        [Helper]
        Gather all infomations of the database, including:
          - all tables
        """
        def get_all_tables():
            self.cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table';")
            return list(map(lambda x: x[0], self.cursor.fetchall()))

        self.tables = get_all_tables()
        self.tables = {tname: Table(self, tname) for tname in self.tables}

    def do(self, *sql: str, paras: List[tuple] = []) -> sqlite3.Cursor:
        """
        Execute a sql command on the database.

        Paras:
            sql: str
                The sql command(s).
            paras: tuple
                The parameters for the sql command(s).
        """
        if len(paras) < len(sql):
            paras += [()] * (len(sql) - len(paras))

        # for each sql command
        for i in range(len(sql)):
            self.cursor.execute(sql[i], paras[i])

        self.conn.commit()

        return self.cursor

    def createTable(self, *table_names: str, allowExist: bool = True) -> Table:
        """
        create a table in the database.

        Paras:
            table_names: str
                The name of the table.
            allowExist: bool
                Allow to return a existing table.
        """
        tables = []

        for table_name in table_names:
            if table_name in self.tables:
                if not allowExist:
                    raise Exception("Table already exists.")

            table = Table(self, table_name)
            # must be executed after Table.__init__()
            self.tables[table_name] = table

            tables.append(table)

        return tables if len(tables) > 1 else tables[0]


class Table:
    """
    A table in the SQLite database.
    """

    def __init__(self, db: DataBase, table_name: str):
        self.db = db
        self.table_name = table_name

        if table_name in self.db.tables:
            # table exists
            self.isEmpty = False
        else:
            # table not exists
            # can't create a table with no columns, so a hackish way is to create the table when adding a column.
            self.isEmpty = True

        self._gather_info()

    def _gather_info(self):
        """
        [Helper] Gather all infomations of the table, including:
            - all columns
        """
        def get_columns():
            cursor = self.db.do(f"PRAGMA table_info({self.table_name})")
            return list(cursor.fetchall())

        if not self.isEmpty:
            self.column_info = get_columns()
        else:
            self.column_info = []
        
        self.columns = list(map(lambda x: x[1], self.column_info))
        self.columnsType = {self.column_info[i][1]: self.column_info[i][2] for i in range(len(self.column_info))}

    def __getitem__(self, key: str) -> Exp:
        """
        get a column from the table, mainly used to construct query.
        """
        if key not in self.columns:
            raise Exception("Column not exists.")

        return Exp(key, table=self, _str=self.columnsType[key])

    def __setitem__(self, key: str, value: Any) -> None:
        """ 
        Create a new column in the table.
        """
        self.newColumn(key, value)

    def __delitem__(self, key: str) -> None:
        """ 
        Delete an existing column in this table. 
        An Exception will be raised if column not exist.
        """
        self.delColumn(key)

    def __call__(self, exp: Exp, select: str = '*') -> list:
        """
        Select data from the table.

        Paras:
            exp: Exp
                The query expression.
            select: str
                The columns to select, default is '*'(all columns).
        """
        return exp.execute(table=self, select=select)

    def newColumn(self, name: str, type, primaryKey=False, allowExist=True) -> None:
        """
        Add a new column to the table.

        Paras:
            name: str
                The name of the column.
            type: str
                The type of the column.
            primaryKey: bool
                The column will be a primary key if set to `True`.
            allowExist: bool
                Allow to return a existing column.
        """
        if name in self.columns:
            if not allowExist:
                raise Exception("Column already exists.")
            else:
                return

        if self.isEmpty:
            # create it first
            self.db.do(f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} ({name} {type} {'PRIMARY KEY' if primaryKey else ''})
            """)
        else:
            self.db.do(
                f"ALTER TABLE {self.table_name} ADD COLUMN {name} {type}")

            if primaryKey:
                self.setPrimaryKey(name)

        self.columns.append(name)

    def delColumn(self, name: str) -> None:
        if name not in self.columns:
            raise Exception("Column not exist!")
        else:
            self.columns.remove(name)
            self.db.do(f"ALTER TABLE {self.table_name} DROP COLUMN {name}")

    def setPrimaryKey(self, keyname: str) -> None:
        """
        Set a column as the primary key of the table.

        Paras:
            keyname: str
                The name of the column.
        """
        self.db.do(
            f"CREATE TABLE new_table ({keyname} INTEGER PRIMARY KEY, {', '.join([f'{name} {type}' for name, type in self.columns.items() if name != keyname])})",
            f"INSERT INTO new_table SELECT * FROM {self.table_name}",
            f"DROP TABLE {self.table_name}",
            f"ALTER TABLE new_table RENAME TO {self.table_name}"
        )

    def insert(self, **kwargs) -> None:
        """
        Insert a row into the table.

        Paras:
            kwargs: dict
                The data to insert.
        """
        columns = ', '.join(kwargs.keys())
        values = ', '.join(map(lambda x: f"'{x}'", kwargs.values()))

        self.db.do(f"INSERT INTO {self.table_name} ({columns}) VALUES ({values})")


class BasicExp:
    def __init__(self, exp1, oper='', exp2=None):
        self.exp1 = exp1
        self.oper = oper
        self.exp2 = exp2

    def formula(self) -> Tuple[str, tuple]:
        if self.oper == '':
            return self.exp1, ()
        else:
            # process `exp1`
            if isinstance(self.exp1, BasicExp):
                exp1_formula, exp1_paras = self.exp1.formula()
            elif self.exp1 is None:
                exp1_formula, exp1_paras = '', ()
            else:
                exp1_formula, exp1_paras = '?', (self.exp1,)

            # process `exp2`
            if isinstance(self.exp2, BasicExp):
                exp2_formula, exp2_paras = self.exp2.formula()
            elif self.exp2 is None:
                exp2_formula, exp2_paras = '', ()
            else:
                exp2_formula, exp2_paras = '?', (self.exp2,)

            return f"({exp1_formula} {self.oper} {exp2_formula})", tuple(exp1_paras + exp2_paras)


class Exp(BasicExp):
    def __init__(self, o1, op='', o2='', **kwargs):
        """
        Acceptable addition attributes:
        - table: Table ...................... the table to search
        - _str: str ......................... the string to show when print the object
        """
        super().__init__(o1, op, o2)

        self.table = kwargs.get('table', None)
        self._str = kwargs.get('_str', '<Exp object>')

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

    # def between(self, __value1: Union[Exp, int, str], __value2: Union[Exp, int, str]) -> Exp:
    #     return Exp(self, 'BETWEEN', str(__value1) + ' AND ' + str(__value2))

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

    def execute(self, table=None, select='*') -> list:
        """
        Execute the query.
        """
        self.table = table or self.table

        if self.table is None:
            raise Exception("Table not specified.")
        if not isinstance(self.table, Table):
            raise Exception("Table not exists.")

        sql, paras = self.formula()
        sql = f"SELECT {select} FROM {self.table.table_name} WHERE {sql}"

        res = self.table.db.do(sql, paras=[paras])
        return res.fetchall()

    def __iter__(self):
        """
        use magic method `__iter__` to search.
        """
        return iter(self.execute())
    
    def __str__(self):
        return self._str


if __name__ == '__main__':
    print((Exp('id').in_([1, 2, 3]) & (Exp('name') == 'hello, world')).table)

    db = DataBase("test.db")
    print(db.info)

    test_table = db.createTable('test')
    print(db.tables)

    # test_table.newColumn('id', 'INTEGER', primaryKey=True)
    # test_table.newColumn('name', 'TEXT')
    print(test_table.columns)

    print(test_table['id'])

    # test_table.insert(id=1, name='test')
    print(list((db['test']['id'] == 1) & (db['test']['name'] == 'test')))

    # # db['test'].insert(id=1, name='b huang')
    # print(db['test'](db['test']['id'] == 1))
