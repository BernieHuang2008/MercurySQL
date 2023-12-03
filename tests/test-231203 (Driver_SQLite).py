# <--- Test Head --->
import sys
sys.path.insert(0, 'g:\git\BernieHuang2008\MercurySQLite')
# <--- Test Head End --->


from MercurySQLite import DataBase, Driver_SQLite

if __name__ == '__main__':
    # Create a new database object for a database named "test.db"
    db = DataBase(Driver_SQLite, "test.db")

    # Print the information about the database
    print("Database Information:", db.info)

    # Choose / Create a table named 'test' in the database
    test_table = db['test']
    print("Tables in the database:", db.tables)

    # Set the structure of 'test' table
    print(Driver_SQLite.APIs.get_all_columns(db.conn, 'test'))
    test_table.struct({
        'id': int,
        'name': str
    }, primaryKey='id')

    # add a single new column named 'score' with type 'float'
    test_table['score'] = float

    print("Columns in the 'test' table:", test_table.columns)

    # Access the column definition of 'id' in 'test' table
    print("Definition of 'id' column :", test_table['id'])
    print("Definition of 'name' column :", test_table['name'])

    print(Driver_SQLite.APIs.get_all_columns(db.conn, 'test'))
    # Uncomment the following line to insert a new row into the 'test' table
    test_table.insert(id=1, name='test', __auto=True)

    # Query the 'test' table for rows where 'id==1 AND name==test'
    e = (test_table['id'] == 1) & \
        (test_table['name'] == 'test')

    print("Query result:", list(test_table.select(e)))

    # Delete the data
    e.delete()

    print("After deleting the query result:", list(test_table.select(e)))
