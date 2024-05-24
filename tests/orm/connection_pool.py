
from MercurySQL import DataBase, set_driver
from MercurySQL.drivers.sqlite import Driver_SQLite

import threading

# Set the driver to Driver_SQLite
set_driver(Driver_SQLite)

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

def thread1():
    # insert one data piece into the table
    test_table.insert(id=1, name='test')

def thread2():
    # insert another data piece into the table
    test_table.insert(id=2, name='test2')

# insert data
threading.Thread(target=thread1).start()
threading.Thread(target=thread2).start()

# wait for the threads to finish
thread1.join()
thread2.join()
