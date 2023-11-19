Also read in [English](README.md)

# MercurySQLite
Operate SQLite in a more pythonic way.

# 是个啥
用更Python的方式操作sqlite数据库。

比如说....
### 创建数据库
SQL
```sql
CREATE DATABASE IF NOT EXISTS test;
```
MercurySQLite
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
MercurySQLite
```py
table = db['test']
table.newColumn('id', int, primaryKey=True)
```

### 添加列
SQL
```sql
ALTER TABLE test
ADD COLUMN name TEXT;
```
MercurySQLite
```py
table['name'] = str
```

### 删除列
SQL
```sql
ALTER TABLE table
DROP COLUMN name;
```
PySQLite
```py
del table['name']
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
rec = list(
      (table['id'] == 1) & \
      (table['name'] == 'test')
)
```


# 依赖项：
- sqlite3（Python自带）

  所以……没有依赖项！

---

## 为什么叫做MercurySQLite

*（===== 以下是ChatGPT瞎吹的，别管他 =====）*

**速度与敏捷性**： 水银（Mercury）是古罗马神话中的信使神，也是快速、灵活的代名词。通过
将"Mercury"放在库的名称中，你可能想传达这个库在处理SQLite数据库时的速度和敏捷性。

**轻量级**： 水银是一种相对较轻的金属，这也可能表示你的库设计为轻量级，适用于对资源敏感的环境，如嵌入式系统或移动设备。

**流动性**： 水银在常温下是液态金属，具有良好的流动性。这可能象征着你的库提供了流畅的API，使得对SQLite数据库的操作更加灵活和容易。

**精确性**： 在温度变化下，水银表现出稳定的体积，这使得它在温度计中得到广泛应用。这可能表明你的库在处理数据时是准确和稳定的，具有良好的可靠性。

**化学稳定性**： 水银是一种化学稳定的元素，不容易与其他元素发生反应。这可能意味着你的库在与其他Python 库或框架集成时是稳定且不易产生冲突的。