MercurySQL.gensql
=================

Operate SQL in a more pythonic way.

This module contains the implementation of python to SQL.
It provides a high-level API for operating SQL databases, which allows you to create tables, insert rows, execute queries, etc. in a more pythonic way.

For each sql engine (e.g. sqlite, mysql, ...), a `Driver` is needed. For more details about the `Driver`, please refer to the :ref:`PG_INTRO_DRIVER` section.

.. warning::
   This module provides built-in support for anti-SQL-injection. That is, all the query values are replaced with safe queries ('`?`' or else). 
   
   However, the inspection of the table name & column name is implemented by `Driver` s. So becareful especially when using third-party drivers.
   
   It is recommended to hard-code the `DB name`, `table name` & `column name` in your code, instead of using user inputs directly.


Advanced APIs
-------------

.. autoclass:: MercurySQL.gensql.DataBase
   :members:
   :special-members:
   :exclude-members: __weakref__, __module__

.. autoclass:: MercurySQL.gensql.Table
   :members:
   :special-members: 
   :exclude-members: __weakref__, __module__

.. autoclass:: MercurySQL.gensql.Exp
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

.. autoclass:: MercurySQL.gensql.exp.BasicExp
   :members:
   :undoc-members:
   :special-members: 
   :exclude-members: __weakref__, __module__

   Basic class of Exp, representing a basic query expression that can be used to construct complex queries.
