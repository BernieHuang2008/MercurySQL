import sys
import os

# Add the parent directory of 'tests' to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from MercurySQLite import DataBase

if __name__ == '__main__':
    # Create a new database object for a database named "test.db"
    db = DataBase("test.db")

    # Print the information about the database
    print("Database Information:", db.info)

    # Choose / Create a table named 'test' in the database
    test_table = db['test']
    print("Tables in the database:", db.tables)

    # Set the structure of 'test' table
    test_table.struct({
        'id': int,
        'name': str
    }, primaryKey='id')

    # add a single new column named 'score' with type 'float'
    test_table['score'] = float

    print("Columns in the 'test' table:", test_table.columns)

    # Access the column definition of 'id' in 'test' table
    print("Accessing 'id' column :", test_table['id'])

    # Uncomment the following line to insert a new row into the 'test' table
    # test_table.insert(id=1, name='test')

    # Query the 'test' table for rows where 'id==1 AND name==test'
    e = (db['test']['id'] == 1) & \
        (db['test']['name'] == 'test')

    print("Query result:", list(e))

    # Delete the data
    del e

    print("After deleting the query result:", list(
        (db['test']['id'] == 1) &
        (db['test']['name'] == 'test'))
    )
