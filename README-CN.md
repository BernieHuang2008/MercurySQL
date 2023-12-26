Also read in [English](README.md)

阅读完整文档 [Read the Docs](https://mercurysql.readthedocs.io/en/latest/)

# MercurySQL
Operate SQL in a more pythonic way.

# 是个啥
用更Python的方式操作SQL数据库。

- 被复杂无比的SQL语句弄懵？
- 因没有commit而导致数据丢失？
- 在终端里调试了几个小时的SQL？

别怕，我也是。所以MercurySQL诞生了。

MercurySQL有以下优点 ....

- **更Pythonic的操作方式**：更符合Python风格的API，使得操作SQL数据库更加简洁易懂。
- **避免复杂的SQL语句**：避免编写复杂的SQL语句，从而减少了学习和理解SQL语法的负担。
- **数据库更安全**：使用安全查询、自动处理事务提交，保护数据库安全，防止数据丢失。
- **直接使用Python进行调试**：可以在Python代码中直接调试和查看数据库操作，无需在终端中进行SQL调试。

比如说，它可以做这些事....
### 创建数据库
SQL
```sql
CREATE DATABASE IF NOT EXISTS test;
```
MercurySQL
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
MercurySQL
```py
tb = db['test']  # 如果没有，会自动创建
tn.newColumn('id', int, primaryKey=True)
tb['id'] = int, 'Primary Key  # 大小写不敏感
```

### 删除数据表
SQL
```sql
DROP TABLE IF EXISTS test;
```
MercurySQL
```py
del db['test']
```

### 添加列
SQL
```sql
ALTER TABLE test
ADD COLUMN name TEXT;
```
MercurySQL
```py
table['name'] = str
```

### 添加主键列
SQL
```sql
ALTER TABLE test
ADD COLUMN id INTEGER PRIMARY KEY;
```
MercurySQL
```py
table['id'] = int, 'Primary Key'  # 'Primary Key' 这类参数对大小写不敏感
```

### 删除列
SQL
```sql
ALTER TABLE table
DROP COLUMN name;
```
MercurySQL
```py
del table['name']
```

### 添加记录
SQL
```sql
INSERT INTO test (id, name) VALUES (1, 'Bernie Huang');
```
MercurySQL
```py
table.insert(id=1, name='Bernie Huang')
```

### 查找记录
SQL
```sql
SELECT * FROM test WHERE id=1 AND name='Bernie Huang';
```
MercurySQL
```py
res = (table['id'] == 1) & (table['name'] == 'test')

print(list(res))
```

### 删除记录
SQL
```sql
DELETE * FROM test WHERE id=1 AND name='Bernie Huang';
```
MercurySQL
```py
((table['id'] == 1) & (table['name'] == 'test')).delete()
```

# 驱动（drivers）
MercurySQL 理论上可以兼容任何使用sql语言的数据库。
这是因为我们的 drivers 思想。

MercurySQL 的核心代码是通用的，但是，针对每一个数据库，都需要一个专门的驱动程序来做适配。
这个驱动程序的功能很简单，可以参考read the docs上的“Drivers”部分进行开发。
驱动程序将以一个类的形式提供服务，可以在DataBase中传入一个参数，或者使用内置api `set_driver()`一劳永逸地设置全局默认驱动。
比如说：
```python
from MercurySQL.drivers.sqlite import Driver_SQlite   # 导入sqlite驱动
from MercurySQL import set_driver  # 导入set_driver

set_driver(Driver_SQLite)
```
或者是，在DataBase中传入驱动器：
```python
Database(... driver=Driver_SQLite)
```

# 依赖项：
MercurySQL可以使用不同的驱动器（driver），每个驱动器都有自己的依赖。
自带驱动器的依赖项如下：
* Sqlite Driver
  - sqlite3（Python自带）
* MySQL Driver
  - mysql-connector

---

## 为什么叫做MercurySQL

*（===== 以下是ChatGPT瞎吹的，别管他 =====）*

**速度与敏捷性**： 水银（Mercury）是古罗马神话中的信使神，也是快速、灵活的代名词。通过
将"Mercury"放在库的名称中，你可能想传达这个库在处理SQL数据库时的速度和敏捷性。

**轻量级**： 水银是一种相对较轻的金属，这也可能表示你的库设计为轻量级，适用于对资源敏感的环境，如嵌入式系统或移动设备。

**流动性**： 水银在常温下是液态金属，具有良好的流动性。这可能象征着你的库提供了流畅的API，使得对SQL数据库的操作更加灵活和容易。

**精确性**： 在温度变化下，水银表现出稳定的体积，这使得它在温度计中得到广泛应用。这可能表明你的库在处理数据时是准确和稳定的，具有良好的可靠性。

**化学稳定性**： 水银是一种化学稳定的元素，不容易与其他元素发生反应。这可能意味着你的库在与其他Python 库或框架集成时是稳定且不易产生冲突的。