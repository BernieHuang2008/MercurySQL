# <--- Test Head --->
import sys
sys.path.insert(0, '../../')
sys.path.insert(0, './')

import io
SCREEN_OUTPUT = sys.stdout
TEST_OUTPUT = io.StringIO()
sys.stdout = TEST_OUTPUT

import re
from MercurySQL.drivers.mysql import Driver_MySQLConnector
from MercurySQL import DataBase, set_driver
# <--- Test Head End --->

# Set the driver to Driver_MySQLConnector
set_driver(Driver_MySQLConnector)

if __name__ == '__main__':
    # conn = Driver_MySQLConnector.connect('test', 'localhost', 'test', 'test')
    # print(Driver_MySQLConnector.APIs.get_all_tables(conn), file=SCREEN_OUTPUT)
    db = DataBase('test', Driver_MySQLConnector, host='localhost', user='test', passwd='test')
    # print("1", db.driver.APIs.get_all_tables(db.conn), file=SCREEN_OUTPUT)
    # print("2", list(db.driver.APIs.get_all_columns(db.conn, 'test')), file=SCREEN_OUTPUT)
    tb = db['test']
    # tb['id'] = int, 'primarykey'
    # tb['name'] = str
    tb.insert(id=1, name='test', __auto=True)
    print("1", list(tb.select(tb['id'] == 1)), file=SCREEN_OUTPUT)
