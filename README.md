Also read in [中文](README-CN.md)

# MercurySQLite
Operate SQLite in a more pythonic way.

# What is it
Operate SQLite database in a more Pythonic way.

For example....
### Create Database
SQL
```sql
CREATE DATABASE IF NOT EXISTS test;
```
MercurySQLite
```py
db = DataBase('test')
```

### Create Table
SQL
```sql
CREATE TABLE IF NOT EXISTS test (
    id INTEGER PRIMARY KEY
);
```
MercurySQLite
```py
table = db['test']
table.newColumn('id', int, primaryKey=True)
```

### Delete Table
SQL
```sql
DROP TABLE IF EXISTS test;
```
MercurySQLite
```py
del db['test']
```

### Add Column
SQL
```sql
ALTER TABLE test
ADD COLUMN name TEXT;
```
MercurySQLite
```py
table['name'] = str
```

### Add Primary Key Column
SQL
```sql
ALTER TABLE test
ADD COLUMN id INTEGER PRIMARY KEY;
```
MercurySQLite
```py
table['id'] = int, 'Primary Key'  # 'Primary Key' is case-insensitive
```

### Delete Column
SQL
```sql
ALTER TABLE table
DROP COLUMN name;
```
MercurySQLite
```py
del table['name']
```

### Add Record
SQL
```sql
INSERT INTO test (id, name) VALUES (1, 'Bernie Huang');
```
MercurySQLite
```py
table.insert(id=1, name='Bernie Huang')
```

## Query
SQL
```sql
SELECT * FROM test WHERE id=1 AND name='Bernie Huang';
```
MercurySQLite
```py
rec = table.select(
      (table['id'] == 1) & \
      (table['name'] == 'test')
)   # rec = [{'id': 1, 'name': 'Bernie Huang'}]
```

### Delete Record
SQL
```sql
DELETE * FROM test WHERE id=1 AND name='Bernie Huang';
```
MercurySQLite
```py
((table['id'] == 1) & (table['name'] == 'test')).delete()
```

# Dependencies:
- sqlite3 (comes with Python)

  So ... no dependencies!

---

## Why is it called MercurySQLite

*(===== The following is just some fun speculation by ChatGPT, don't mind it =====)*

**Speed and Agility**: Mercury is the messenger god in ancient Roman mythology, and is synonymous with speed and flexibility. By putting "Mercury" in the name of the library, you might want to convey the speed and agility of this library when handling SQLite databases.

**Lightweight**: Mercury is a relatively light metal, which may indicate that your library is designed to be lightweight, suitable for resource-sensitive environments such as embedded systems or mobile devices.

**Fluidity**: Mercury is a liquid metal at room temperature, with good fluidity. This may symbolize that your library provides a smooth API, making operations on SQLite databases more flexible and easy.

**Accuracy**: Under temperature changes, mercury shows a stable volume, which makes it widely used in thermometers. This may indicate that your library is accurate and stable when handling data, with good reliability.

**Chemical Stability**: Mercury is a chemically stable element and does not easily react with other elements. This may mean that your library is stable and not prone to conflicts when integrated with other Python libraries or frameworks.