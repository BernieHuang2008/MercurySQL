"""
Use built-in sqlite3 library to operate sql in a more pythonic way.
"""

import sqlite3
from typing import Any, Union

class Exp: pass
class Table: pass
class DataBase: pass


class DataBase:
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
        [Helper] Gather all infomations of the database, including:
          - all tables
        """
        def get_all_tables():
            self.cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table';")
            return list(map(lambda x: x[0], self.cursor.fetchall()))

        self.tables = get_all_tables()
        self.tables = {tname: Table(self, tname) for tname in self.tables}

    def do(self, *sql: str) -> sqlite3.Cursor:
        """
        Execute a sql command on the database.

        Paras:
            sql: str
                The sql command(s).
        """
        for command in sql:
            self.cursor.execute(command)

        self.conn.commit()

        return self.cursor

    def createTable(self, *table_names: str, forceNew: bool=False) -> Table:
        """
        create a table in the database.

        Paras:
            table_names: str
                The name of the table.
            forceNew: bool
                Force to create a new table.
                An exception will be raised if the table already exists.
        """
        tables = []

        for table_name in table_names:
            if table_name in self.tables and forceNew:
                raise Exception("Table already exists.")

            table = Table(self, table_name)
            # must be executed after Table.__init__()
            self.tables[table_name] = table

            tables.append(table)

        return tables if len(tables) > 1 else tables[0]


class Table:
    def __init__(self, db: DataBase, table_name: str):
        self.name = table_name

        self.db = db
        self.table_name = table_name

        if table_name in self.db.tables:
            # table exists
            self.isEmpty = False
        else:
            # table not exists
            # can't create a table with no columns, so it's a hackish way to create a table when adding a column.
            self.isEmpty = True

        self._gather_info()

    def __getitem__(self, key: str) -> Exp:
        """
        get a column from the table, mainly used to construct query.
        """
        if key not in self.columns:
            raise Exception("Column not exists.")
        return Exp(key)
    
    def __call__(self, exp: Exp, select: str='*') -> Any:
        """
        Select data from the table.
        
        Paras:
            exp: Exp
                The query expression.
            select: str
                The columns to select, default is '*'(all columns).
        """
        sql = f"SELECT {select} FROM {self.table_name} WHERE {str(exp)}"
        self.db.do(sql)
        return self.db.cursor.fetchall()

    def _gather_info(self):
        """
        [Helper] Gather all infomations of the table, including:
            - all columns
        """
        def get_columns():
            cursor = self.db.do(f"PRAGMA table_info({self.table_name})")
            return list(map(lambda x: x[1], cursor.fetchall()))

        if not self.isEmpty:
            self.columns = get_columns()
        else:
            self.columns = []

    def newColumn(self, name, type, primaryKey=False):
        """
        Add a new column to the table.

        Paras:
            name: str
                The name of the column.
            type: str
                The type of the column.
            primaryKey: bool
                The column will be a primary key if set to `True`.
        """
        if name in self.columns:
            raise Exception("Column already exists.")

        if self.isEmpty:
            # create it first
            self.db.do(f"""
                CREATE TABLE IF NOT EXISTS {self.name} ({name} {type} {'PRIMARY KEY' if primaryKey else ''})
            """)
        else:
            self.db.do(
                f"ALTER TABLE {self.table_name} ADD COLUMN {name} {type}")

            if primaryKey:
                self.setPrimaryKey(name)

        self.columns.append(name)

    def setPrimaryKey(self, keyname):
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

    def insert(self, **kwargs):
        """
        Insert a row into the table.

        Paras:
            kwargs: dict
                The data to insert.
        """
        columns = ', '.join(kwargs.keys())
        values = ', '.join(map(lambda x: f"'{x}'", kwargs.values()))

        self.db.do(f"INSERT INTO {self.table_name} ({columns}) VALUES ({values})")


class Exp:
    def __init__(self, o1, op='', o2=''):
        self.o1 = o1
        self.op = op
        self.o2 = o2
    
    def __str__(self):
        if self.op == '':
            return str(self.o1)
        return f"({str(self.o1)} {str(self.op)} {str(self.o2)})"
    
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
        return Exp(self, 'BETWEEN', str(__value1) + ' AND ' + str(__value2))
    
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

if __name__ == '__main__':
    db = DataBase("test.db")
    print(db.info)

    test_table = db['test']
    print(db.tables)

    print((db['test']['id'] == 1) & (db['test']['name']=='test'))
    print(db['test'].columns)

    # db['test'].insert(id=1, name='b huang')
    print(db['test'](db['test']['id'] == 1))
