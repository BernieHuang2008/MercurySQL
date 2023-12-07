MercurySQL.core
===============

Operate SQL in a more pythonic way.

This file contains the implementation of a common SQL database wrapper class, and for each sql (e.g. sqlite, mysql), a `Driver` is needed.

.. note:: This code is a simplified implementation and may not cover all possible use cases. Please refer to the official documentation for more information.

.. warning::
   This module will not perform any inspection on DB names, Table names or Column names etc.
   However, all the query values are replaced with safe queries ('`?`' or else). Therefore, it is recommended to hardcode Column names to prevent SQL injection.


Advanced APIs
-------------

.. autoclass:: MercurySQL.core.DataBase
   :members:
   :special-members:
   :exclude-members: __weakref__, __module__

   Represents a SQL database. It provides methods for creating tables, executing SQL commands, and retrieving table objects, etc.

.. autoclass:: MercurySQL.core.Table
   :members:
   :special-members: 
   :exclude-members: __weakref__, __module__

   Represents a table in a SQL database. Can be created by `db.createTable()`. It provides methods for adding columns, deleting columns, inserting rows, and executing queries, etc.

.. autoclass:: MercurySQL.core.Exp
   :members:
   :special-members: 
   :exclude-members: __weakref__, __module__
   :inherited-members:

   Subclass of BasicExp, representing a query expression, which can be used to construct complex queries.

   - Supported Operations:
     * `==`: equality
     * `!=`: inequality
     * `<`: less than
     * `<=`: less than or equal to
     * `>`: greater than
     * `>=`: greater than or equal to
     * `.in_()`: in
     * `.like()`: like
     * `&`: and
     * `|`: or
     * `not`: not

   .. note:: you should mind the priority of operations when using some of the operators, especially `&` and `|`.


Low-level APIs
--------------

.. autoclass:: MercurySQL.core.BasicExp
   :members:
   :undoc-members:
   :special-members: 
   :exclude-members: __weakref__, __module__

   Basic class of Exp, representing a basic query expression that can be used to construct complex queries.
