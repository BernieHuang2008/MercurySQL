MercurySQLite.gensql
====================

Use built-in sqlite3 library to operate sql in a more pythonic way.

This file contains the implementation of a SQLite database wrapper class and related classes for table and query expressions.

.. note:: This code is a simplified implementation and may not cover all possible use cases. Please refer to the official documentation for more information.

.. warning::
   This module will not perform any inspection on DB names, Table names or Column names etc.
   However, all the query values are replaced with safe queries ('`?`'). Therefore, it is recommended to hardcode Column names to prevent SQL injection.


Advanced APIs
-------------

.. autoclass:: MercurySQLite.gensql.DataBase
   :members:
   :special-members:
   :exclude-members: __weakref__, __module__

   Represents a SQLite database and provides methods for creating tables, executing SQL commands, and retrieving table objects.

.. autoclass:: MercurySQLite.gensql.Table
   :members:
   :special-members: 
   :exclude-members: __weakref__, __module__

   Represents a table in the SQLite database and provides methods for adding columns, deleting columns, inserting rows, and executing queries.

.. autoclass:: MercurySQLite.gensql.Exp
   :members:
   :special-members: 
   :exclude-members: __weakref__, __module__
   :inherited-members:

   Subclass of BasicExp, representing a query expression that can be used to construct complex queries.

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

   .. note:: you should mind the priority of operations when using `&` and `|`.


Low-level (Helper) APIs
-----------------------

.. autoclass:: MercurySQLite.gensql.BasicExp
   :members:
   :undoc-members:
   :special-members: 
   :exclude-members: __weakref__, __module__

   Basic class of Exp, representing a basic query expression that can be used to construct complex queries.

.. autoclass:: MercurySQLite.gensql.TypeParser
   :members:
   :undoc-members:
   :special-members: 
   :exclude-members: __weakref__, __module__

    Class for parsing Python standard types to SQLite types.

