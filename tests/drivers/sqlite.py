# <--- Test Head --->
import io
import sys
sys.path.insert(0, './')

SCREEN_OUTPUT = sys.stdout
TEST_OUTPUT = io.StringIO()
sys.stdout = TEST_OUTPUT

# <--- Test Head End --->


from MercurySQL import DataBase, set_driver
from MercurySQL.drivers.sqlite import Driver_SQLite
import re

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
    test_table.insert(id=1, name='test', __auto=True)

    # Query data
    e = (test_table['id'] == 1) & \
        (test_table['name'] == 'test')
    print("Query result:", list(test_table.select(e)))

    # Delete data
    e.delete()
    print("After deleting the query result:", list(test_table.select(e)))

# <--- Check Test --->
def process_output(s):
    s = s.strip()

    pattern = r' object at 0x[0-9A-Fa-f]+>'
    s = re.sub(pattern, ' object at 0xPYTHON_ADDRESS>', s)

    return s

EXPECTED_OUTPUT = """
Database Information: {'name': 'test.db'}
Tables in the database: {'test': <MercurySQL.core.Table object at 0x000001B056422760>}
[(0, 'id', 'INTEGER', 0, None, 1), (1, 'name', 'TEXT', 0, None, 0), (2, 'score', 'REAL', 0, None, 0)]
Columns in the 'test' table: ['id', 'name', 'score']
Definition of 'id' column: INTEGER
Definition of 'name' column: TEXT
[(0, 'id', 'INTEGER', 0, None, 1), (1, 'name', 'TEXT', 0, None, 0), (2, 'score', 'REAL', 0, None, 0)]
Query result: [{'id': 1, 'name': 'test', 'score': None}]
After deleting the query result: []
"""

print(process_output(TEST_OUTPUT.getvalue()) == process_output(EXPECTED_OUTPUT), file=SCREEN_OUTPUT)
