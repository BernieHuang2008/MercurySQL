import testlib

from MercurySQL import DataBase, set_driver
from MercurySQL.drivers.sqlite import Driver_SQLite

import os
import threading
import time

set_driver(Driver_SQLite)

# Start from a clean database, otherwise rows left by the previous run collide.
if os.path.exists('test.db'):
    os.remove('test.db')

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
# `join()` instead of `sleep()`: the main thread must not print "4" before the
# workers printed "2" and "3", otherwise the golden output fails at random
# (which the old `time.sleep(0.7)` version did).
workers = [threading.Thread(target=t1), threading.Thread(target=t2)]
for worker in workers:
    worker.start()
for worker in workers:
    worker.join()

# after inserting
print(4, list(tb.select()))

# <--- Check Test --->


testlib.check(EXPECTED_OUTPUT = """
1 []
2 [{'id': 2, 'name': 'test2'}]
3 [{'id': 1, 'name': 'test'}, {'id': 2, 'name': 'test2'}]
4 [{'id': 1, 'name': 'test'}, {'id': 2, 'name': 'test2'}]
""")
