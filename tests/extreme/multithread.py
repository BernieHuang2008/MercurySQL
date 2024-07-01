import testlib

from MercurySQL import DataBase, set_driver
from MercurySQL.drivers.sqlite import Driver_SQLite

import threading
import time

set_driver(Driver_SQLite)

db = DataBase("test.db")
tb = db['test']
tb.struct({
    'id': int,
    'name': str
}, primaryKey='id')

# before inserting
print(1, list(tb.select()))

def t1():
    # insert one data piece into the table
    time.sleep(0.5)
    tb.insert(id=1, name='test')
    print(3, list(tb.select()))

def t2():
    # insert another data piece into the table
    tb.insert(id=2, name='test2')
    print(2, list(tb.select()))

# thread start
threading.Thread(target=t1).start()
threading.Thread(target=t2).start()
time.sleep(0.7)

# after inserting
print(4, list(tb.select()))

# <--- Check Test --->


testlib.check(EXPECTED_OUTPUT = """
1 []
2 [{'id': 2, 'name': 'test2'}]
3 [{'id': 1, 'name': 'test'}, {'id': 2, 'name': 'test2'}]
4 [{'id': 1, 'name': 'test'}, {'id': 2, 'name': 'test2'}]
""")
