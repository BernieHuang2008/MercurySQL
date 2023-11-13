# PySQLite
Operate SQLite in a more pythonic way.

# 是个啥
用更Python的方式操作sqlite数据库。

比如说....
### 创建数据库
SQL
```sql
CREATE DATABASE IF NOT EXISTS test;
```
PySQLite
```py
db = DataBase('test')
```

### 创建数据表
SQL
```sql
CREATE TABLE IF NOT EXISTS test (
    id INTEGER PRIMARY KEY
);
```
PySQLite
```py
table = db.createTable('test')
table.newColumn('id', 'INTEGER', primaryKey=True)
```

### 添加列
SQL
```sql
ALTER TABLE test
ADD COLUMN name TEXT;
```
PySQLite
```py
table.newColumn('name', 'TEXT')
```

### 删除列
SQL
```sql
ALTER TABLE table
DROP COLUMN name;
```
PySQLite
```py
delete table['name']
```

### 添加记录
SQL
```sql
INSERT INTO test (id, name) VALUES (1, 'Bernie Huang');
```
PySQLite
```py
table.insert(id=1, name='Bernie Huang')
```

### 查找记录
SQL
```sql
SELECT * FROM test WHERE id=1 AND name='Bernie Huang';
```
PySQLite
```py
rec = table(
      (table['id'] == 1) \
    & (table['name'] == 'test')
)
```


# 依赖项：
sqlite3（Python自带）


