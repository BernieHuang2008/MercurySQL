# <--- Test Head --->
if 'set path':
    import sys
    sys.path.insert(0, '../../')
    sys.path.insert(0, './')
if 'set io':
    import io
    SCREEN_OUTPUT = sys.stdout
    TEST_OUTPUT = io.StringIO()
    sys.stdout = TEST_OUTPUT
if 'import':
    import re
    from MercurySQL.drivers.mysql import Driver_MySQL
    from MercurySQL import DataBase, set_driver
# <--- Test Head End --->


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
    test_table.insert(id=1, name='test', __auto=True)

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


def process_output(s):
    s = s.strip()

    pattern = r' object at 0x[0-9A-Fa-f]+>'
    s = re.sub(pattern, ' object at 0xPYTHON_ADDRESS>', s)

    return s


EXPECTED_OUTPUT = """
Database Information: {'name': 'test'}
Tables in the database: {'test': <MercurySQL.core.Table object at 0x000002BC3B3024C0>}
Columns in the 'test' table: []
Columns in the 'test' table: ['id', 'name', 'score', 'index_']
Definition of 'id' column: INT
Definition of 'name' column: VARCHAR(225)
[['id', 'int', 'NO', '', None, ''], ['name', 'varchar(225)', 'YES', '', None, ''], ['score', 'float', 'YES', '', None, ''], ['index_', 'int', 'NO', 'PRI', '1', '']]
Query result: [{'id': 1, 'name': 'test', 'score': None, 'index_': 1}]
After deleting the query result: []
Tables in the database: {}
"""

TEST_OUTPUT = process_output(TEST_OUTPUT.getvalue())
EXPECTED_OUTPUT = process_output(EXPECTED_OUTPUT)

if TEST_OUTPUT == EXPECTED_OUTPUT:
    print("\033[32mTest Passed!\033[0m", file=SCREEN_OUTPUT)
else:
    print("\033[31mTest Failed!\033[0m", file=SCREEN_OUTPUT)
    print("Expected Output:", file=SCREEN_OUTPUT)
    print(EXPECTED_OUTPUT, file=SCREEN_OUTPUT)
    print('='*30+'\n', file=SCREEN_OUTPUT)
    print("Test Output:", file=SCREEN_OUTPUT)
    print(TEST_OUTPUT, file=SCREEN_OUTPUT)
    print('='*30+'\n', file=SCREEN_OUTPUT)
    print("Differences:", file=SCREEN_OUTPUT)

    import difflib

    def color_diff(expected, actual):
        diff = difflib.unified_diff(
            expected.splitlines(), actual.splitlines(), lineterm='')
        diff_str = '\n'.join(diff)

        for line in diff_str.splitlines():
            if line.startswith('+'):
                # Green for added lines
                print('\033[32m' + line + '\033[0m', file=SCREEN_OUTPUT)
            elif line.startswith('-'):
                # Red for removed lines
                print('\033[31m' + line + '\033[0m', file=SCREEN_OUTPUT)
            else:
                print(line, file=SCREEN_OUTPUT)

    color_diff(EXPECTED_OUTPUT, TEST_OUTPUT)

    raise Exception("Test Failed!")
