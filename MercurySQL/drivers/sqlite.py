"""
Requirements: 
  - sqlite3
"""

# # <--- Test Head --->
# import sys
# sys.path.insert(0, 'g:\git\BernieHuang2008\MercurySQLite')
# # <--- Test Head End --->

import sqlite3
from typing import Any, Union, List, Tuple


class Driver_SQLite:
    class Cursor:
        pass

    class Conn:
        pass


class Driver_SQLite:
    Conn = sqlite3.Connection
    Cursor = sqlite3.Cursor

    class APIs:
        class gensql:
            @staticmethod
            def drop_table(table_name: str) -> str:
                return f"DROP TABLE {table_name}"

            @staticmethod
            def get_all_tables() -> str:
                return "SELECT name FROM sqlite_master WHERE type='table';"

            @staticmethod
            def get_all_columns(table_name: str) -> str:
                return f"PRAGMA table_info({table_name});"

            @staticmethod
            def create_table_if_not_exists(table_name: str, column_name: str, column_type: str, primaryKey=False) -> str:
                return f"""
                    CREATE TABLE IF NOT EXISTS {table_name} ({column_name} {column_type} {'PRIMARY KEY' if primaryKey else ''})
                """

            @staticmethod
            def add_column(table_name: str, column_name: str, column_type: str) -> str:
                return f"""
                    ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}
                """

            @staticmethod
            def drop_column(table_name: str, column_name: str) -> str:
                return f"""
                    ALTER TABLE {table_name} DROP COLUMN {column_name}
                """

            @staticmethod
            def set_primary_key(table, keyname: str, keytype: str) -> list:
                return [
                    f"CREATE TABLE ___temp_table ({keyname} {keytype} PRIMARY KEY, {', '.join([f'{name} {type_}' for name, type_ in table.columnsType.items() if name != keyname])})",
                    f"INSERT INTO ___temp_table SELECT * FROM {table.table_name}",
                    f"DROP TABLE {table.table_name}",
                    f"ALTER TABLE ___temp_table RENAME TO {table.table_name}"
                ]

            @staticmethod
            def insert(table_name: str, columns: str, values: str) -> str:
                return f"INSERT INTO {table_name} ({columns}) VALUES ({values})"

            @staticmethod
            def insert_or_update(table_name: str, columns: str, values: str) -> str:
                return f"INSERT OR REPLACE INTO {table_name} ({columns}) VALUES ({values})"

            @staticmethod
            def update(table_name: str, columns: str, condition: str) -> str:
                return f"UPDATE {table_name} SET {columns} WHERE {condition}"

            @staticmethod
            def query(table_name: str, selection: str, condition: str) -> str:
                return f"SELECT {selection} FROM {table_name} WHERE {condition}"

            @staticmethod
            def delete(table_name: str, condition: str) -> str:
                return f"DELETE FROM {table_name} WHERE {condition}"
        

        @classmethod
        def get_all_tables(cls, conn) -> List[str]:
            cursor = conn.cursor()
            cursor.execute(cls.gensql.get_all_tables())
            return list(map(lambda x: x[0], cursor.fetchall()))

        @classmethod
        def get_all_columns(cls, conn, table_name: str) -> List[str]:
            cursor = conn.cursor()
            cursor.execute(cls.gensql.get_all_columns(table_name))
            return cursor.fetchall()


    @staticmethod
    def connect(db_name: str, **kwargs) -> Driver_SQLite.Conn:
        return sqlite3.connect(db_name, **kwargs)
