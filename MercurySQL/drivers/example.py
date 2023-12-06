from typing import List, Union


class BaseDriver:
    class Cursor:
        pass

    class Conn:
        pass

    class APIs:
        pass


class BaseDriver:
    payload = '?'

    class Cursor:
        def execute(self, sql: str, paras: List[tuple] = []) -> BaseDriver.Cursor:
            pass

        def fetchone(self) -> tuple:
            pass

        def fetchall(self) -> List[tuple]:
            pass

    class Conn:
        def cursor(self) -> BaseDriver.Cursor:
            pass

        def commit(self) -> None:
            pass

        def close(self) -> None:
            pass

    class APIs:
        class gensql:
            @staticmethod
            def drop_table(table_name: str) -> Union[str, List[str]]:
                pass
                # return f"DROP TABLE {table_name}"

            @staticmethod
            def get_all_tables() -> Union[str, List[str]]:
                pass
                # return "SELECT name FROM sqlite_master WHERE type='table';"

            @staticmethod
            def get_all_columns(table_name: str) -> Union[str, List[str]]:
                pass
                # return f"PRAGMA table_info({table_name});"

            @staticmethod
            def create_table_if_not_exists(table_name: str, column_name: str, column_type: str, primaryKey=False) -> Union[str, List[str]]:
                pass
                # return f"""
                #     CREATE TABLE IF NOT EXISTS {table_name} ({column_name} {column_type} {'PRIMARY KEY' if primaryKey else ''})
                # """

            @staticmethod
            def add_column(table_name: str, column_name: str, column_type: str) -> Union[str, List[str]]:
                pass
                # return f"""
                #     ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}
                # """

            @staticmethod
            def drop_column(table_name: str, column_name: str) -> Union[str, List[str]]:
                pass
                # return f"""
                #     ALTER TABLE {table_name} DROP COLUMN {column_name}
                # """

            @staticmethod
            def set_primary_key(table, keyname: str, keytype: str) -> Union[str, List[str]]:
                pass
                # return [
                #     f"CREATE TABLE new_table ({keyname} {keytype} PRIMARY KEY, {', '.join([f'{name} {type_}' for name, type_ in table.columns.items() if name != keyname])})",
                #     f"INSERT INTO new_table SELECT * FROM {table.table_name}",
                #     f"DROP TABLE {table.table_name}",
                #     f"ALTER TABLE new_table RENAME TO {table.table_name}"
                # ]

            @staticmethod
            def insert(table_name: str, columns: str, values: str) -> Union[str, List[str]]:
                pass
                # return f"INSERT INTO {table_name} ({columns}) VALUES ({values})"

            @staticmethod
            def insert_or_update(table_name: str, columns: str, values: str) -> Union[str, List[str]]:
                pass
                # return f"INSERT OR REPLACE INTO {table_name} ({columns}) VALUES ({values})"

            @staticmethod
            def update(table_name: str, columns: str, condition: str) -> Union[str, List[str]]:
                pass
                # return f"UPDATE {table_name} SET {columns} WHERE {condition}"

            @staticmethod
            def query(table_name: str, selection: str, condition: str) -> Union[str, List[str]]:
                pass
                # return f"SELECT {selection} FROM {table_name} WHERE {condition}"

            @staticmethod
            def delete(table_name: str, condition: str) -> Union[str, List[str]]:
                pass
                # return f"DELETE FROM {table_name} WHERE {condition}"

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
    def connect(db_name: str, **kwargs) -> BaseDriver.Conn:
        pass
