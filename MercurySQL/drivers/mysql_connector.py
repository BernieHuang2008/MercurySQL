"""
Requirements: 
  - sqlite3
"""
from .base import BaseDriver

import mysql.connector
from typing import Any, List


class Driver_MySQLConnector(BaseDriver):
    pass


class Driver_MySQLConnector(BaseDriver):
    version = '0.1.0'
    payload = '%s'

    Conn = mysql.connector.MySQLConnection
    Cursor = mysql.connector.cursor_cext.CMySQLCursor

    class APIs:
        class gensql:
            @staticmethod
            def drop_table(table_name: str) -> str:
                return f"DROP TABLE {table_name};"

            @staticmethod
            def get_all_tables() -> str:
                return "SHOW TABLES;"

            @staticmethod
            def get_all_columns(table_name: str) -> str:
                return f"DESCRIBE {table_name};"

            @staticmethod
            def create_table_if_not_exists(table_name: str, column_name: str, column_type: str, primaryKey=False, autoIncrement=False, engine='', charset='') -> str:
                return f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        {column_name} {column_type} {'PRIMARY KEY' if primaryKey else ''} {'AUTO_INCREMENT' if autoIncrement else ''}
                    ) {engine} {f'DEFAULT CHARSET={charset}' if charset else ''};
                """

            @staticmethod
            def add_column(table_name: str, column_name: str, column_type: str) -> str:
                return f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type};"

            @staticmethod
            def drop_column(table_name: str, column_name: str) -> str:
                return f"ALTER TABLE {table_name} DROP COLUMN {column_name};"

            @staticmethod
            def set_primary_key(table, keyname: str, keytype: str) -> list:
                return [
                    f"ALTER TABLE DROP PRIMARY KEY;",
                    f"ALTER TABLE {table.table_name} ADD PRIMARY KEY ({keyname});"
                ]

            @staticmethod
            def insert(table_name: str, columns: str, values: str) -> str:
                return f"INSERT INTO {table_name} ({columns}) VALUES ({values});"
            
            @staticmethod
            def insert_or_update(table_name: str, columns: str, values: str) -> str:
                update_columns = ', '.join(f'{col}=VALUES({col})' for col in columns.split(', '))
                return f"INSERT INTO {table_name} ({columns}) VALUES ({values}) ON DUPLICATE KEY UPDATE {update_columns};"

            @staticmethod
            def update(table_name: str, columns: str, condition: str) -> str:
                return f"UPDATE {table_name} SET {columns} WHERE {condition};"

            @staticmethod
            def query(table_name: str, selection: str, condition: str) -> str:
                return f"SELECT {selection} FROM {table_name} WHERE {condition};"

            @staticmethod
            def delete(table_name: str, condition: str) -> str:
                return f"DELETE FROM {table_name} WHERE {condition};"

        @classmethod
        def get_all_tables(cls, conn) -> List[str]:
            cursor = conn.cursor()
            cursor.execute(cls.gensql.get_all_tables())
            return list(map(lambda x: x[0], cursor.fetchall()))

        @classmethod
        def get_all_columns(cls, conn, table_name: str) -> List[str]:
            cursor = conn.cursor()
            cursor.execute(cls.gensql.get_all_columns(table_name))
            return list(map(lambda x: [x[0], x[1]], cursor.fetchall()))

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

            +-------------------+-------------+
            | Supported Types   | SQLite Type |
            +===================+=============+
            | bool              | BOOLEAN     |
            +-------------------+-------------+
            | int               | INTEGER     |
            +-------------------+-------------+
            | int(1)            | TINYINT     |
            +-------------------+-------------+
            | int(2)            | SMALLINT    |
            +-------------------+-------------+
            | int(3)            | MEDIUMINT   |
            +-------------------+-------------+
            | int(4)            | INT         |
            +-------------------+-------------+
            | int(8)            | BIGINT      |
            +-------------------+-------------+
            | float             | FLOAT       |
            +-------------------+-------------+
            | float(4)          | FLOAT       |
            +-------------------+-------------+
            | float(8)          | DOUBLE      |
            +-------------------+-------------+
            | str               | VARCHAR(225)|
            +-------------------+-------------+
            | str('char')       | CHAR        |
            +-------------------+-------------+
            | str('tiny')       | TINYTEXT    |
            +-------------------+-------------+
            | str('medium')     | MEDIUMTEXT  |
            +-------------------+-------------+
            | str('long')       | LONGTEXT    |
            +-------------------+-------------+
            | bytes             | BLOB        |
            +-------------------+-------------+
            | bytes(b'tiny')    | TINYBLOB    |
            +-------------------+-------------+
            | bytes(b'medium')  | MEDIUMBLOB  |
            +-------------------+-------------+
            | bytes(b'long')    | LONGBLOB    |
            +-------------------+-------------+
            | datetime.datetime | DATETIME    |
            +-------------------+-------------+
            | datetime.date     | DATE        |
            +-------------------+-------------+
            | datetime.time     | TIME        |
            +-------------------+-------------+
            

            Example Usage:

            .. code-block:: python

                TypeParser.parse(int(8))       # BIGINT
                TypeParser.parse(str)         # VARCHAR
                TypeParser.parse(float)       # FLOAT
                ...

            """
            import datetime

            supported_types = {
                bool: 'BOOLEAN',

                int: 'INT',
                int(1): 'TINYINT',
                int(2): 'SMALLINT',
                int(3): 'MEDIUMINT',
                int(4): 'INT',
                int(8): 'BIGINT',

                float: 'FLOAT',
                float(4): 'FLOAT',
                float(8): 'DOUBLE',

                str: 'VARCHAR(225)',
                str('char'): 'CHAR',
                str('tiny'): 'TINYTEXT',
                str('medium'): 'MEDIUMTEXT',
                str('long'): 'LONGTEXT',
                
                bytes: 'BLOB',
                bytes(b'tiny'): 'TINYBLOB',
                bytes(b'medium'): 'MEDIUMBLOB',
                bytes(b'long'): 'LONGBLOB',

                datetime.datetime: 'DATETIME',
                datetime.date: 'DATE',
                datetime.time: 'TIME',
            }

            if not isinstance(type_, tuple):
                type_ = (type_,)

            res = ""

            # round 1: Built-in Types
            if type_[0] in supported_types:
                res = supported_types[type_[0]]

            # round 2: Custom Types
            if res == "" and isinstance(type_[0], str):    # custom type
                return type_[0]

            # round 3: Not Null
            for i in range(1, len(type_)):
                if i == (not None):
                    res += ' NOT NULL'

            # Not Supported
            if res == "":
                raise TypeError(f"Type `{str(type_)}` is not supported.")
            
            return res

    @staticmethod
    def connect(db_name: str, host: str, user: str, passwd: str = '', force=False) -> Conn:
        """
        Connect to a 
        """
        if force:
            return mysql.connector.connect(
                host=host,
                user=user,
                passwd=passwd,
                database=db_name
            )
        else:
            conn = mysql.connector.connect(
                host=host,
                user=user,
                passwd=passwd
            )
            conn.backup_cursor = conn.cursor

            def cursor():
                """ Create Database if not exists. """
                conn.cursor = conn.backup_cursor

                c = conn.cursor()

                try:
                    c.execute(f'USE {db_name};')
                except mysql.connector.errors.ProgrammingError:
                    c.execute(f'CREATE DATABASE {db_name};')

                return c

            conn.cursor = cursor
            return conn
