import testlib

from MercurySQL import DataBase, set_driver
from MercurySQL.drivers.sqlite import Driver_SQLite


# Set the driver to Driver_SQLite
set_driver(Driver_SQLite)

if __name__ == '__main__':
    # Create db
    db = DataBase("test.db")
    print("Database Information:", db.info)

    # Create table
    test_table = db['test']
    print("Tables in the database:", db.tables)

    # Set structure
    print(Driver_SQLite.APIs.get_all_columns(db.conn, 'test'))
    test_table.struct({
        'id': int,
        'name': str
    }, primaryKey='id')
    test_table['score'] = float
    print("Columns in the 'test' table:", test_table.columns)

    # Access column definition
    print("Definition of 'id' column:", test_table['id'])
    print("Definition of 'name' column:", test_table['name'])
    print(Driver_SQLite.APIs.get_all_columns(db.conn, 'test'))

    # Insert data
    test_table.insert(id=1, name='test')
    print("Data [id=1]:", list(test_table.select(test_table['id'] == 1)))
    test_table.insert(id=1, name='test2', __auto=True)
    print("Data [id=1]:", list(test_table.select(test_table['id'] == 1)))

    # Query data
    e = (test_table['id'] == 1) & \
        (test_table['name'] == 'test')
    print("Query result:", list(test_table.select(e)))

    # Delete data
    e.delete()
    print("After deleting the query result:", list(test_table.select(e)))

    # Delete table
    del db['test']
    print("Tables in the database:", db.tables)


# <--- Check Test --->


testlib.check(EXPECTED_OUTPUT = """
Database Information: {'name': 'test.db'}
Tables in the database: {'test': <MercurySQL.gensql.table.Table object at 0xPYTHON_ADDRESS>}
[]
Columns in the 'test' table: ['id', 'name', 'score']
Definition of 'id' column: INTEGER
Definition of 'name' column: TEXT
[['id', 'INTEGER'], ['name', 'TEXT'], ['score', 'REAL']]
Data [id=1]: [{'id': 1, 'name': 'test', 'score': None}]
Data [id=1]: [{'id': 1, 'name': 'test2', 'score': None}]
Query result: []
After deleting the query result: []
Tables in the database: {}
""")
