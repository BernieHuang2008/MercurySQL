# [Abandoned]
import testlib

from MercurySQL.drivers.mysql import Driver_MySQL
from MercurySQL import DataBase, set_driver


# Set the driver to Driver_MySQL
set_driver(Driver_MySQL)

if __name__ == '__main__':
    import sys
    if len(sys.argv) == 3:
        user = sys.argv[1]
        passwd = sys.argv[2]
    else:
        user = 'test'
        passwd = 'test'

    # Create db
    db = DataBase("test", host='localhost', user=user, passwd=passwd)
    print("Database Information:", db.info)

    # Create table
    test_table = db['test']
    print("Tables in the database:", db.tables)

    # Set structure
    print("Columns in the 'test' table:", test_table.columns)
    test_table.struct({
        'id': int,
        'name': str
    }, primaryKey='id')
    test_table['score'] = float
    test_table['index_'] = int(1), 'primary key', 'auto increment'
    print("Columns in the 'test' table:", test_table.columns)

    # Access column definition
    print("Definition of 'id' column:", test_table['id'])
    print("Definition of 'name' column:", test_table['name'])
    print(Driver_MySQL.APIs.get_all_columns(db.conn, 'test'))

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



testlib.check(EXPECTED_OUTPUT = """
Database Information: {'name': 'test'}
Tables in the database: {'test': <MercurySQL.core.Table object at 0x000002549D2F8550>}
Columns in the 'test' table: []
Columns in the 'test' table: ['id', 'name', 'score', 'index_']
Definition of 'id' column: INT
Definition of 'name' column: VARCHAR(225)
[['id', 'int', 'NO', '', None, ''], ['name', 'varchar(225)', 'YES', '', None, ''], ['score', 'float', 'YES', '', None, ''], ['index_', 'int', 'NO', 'PRI', '1', '']]
Data [id=1]: [{'id': 1, 'name': 'test', 'score': None, 'index_': 1}]
Data [id=1]: [{'id': 1, 'name': 'test2', 'score': None, 'index_': 1}]
Query result: []
After deleting the query result: []
Tables in the database: {}
""")
