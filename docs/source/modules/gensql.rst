MercurySQL.gensql
=================

Operate SQL in a more pythonic way.

This module contains the implementation of python to SQL.
It provides a high-level API for operating SQL databases, which allows you to create tables, insert rows, execute queries, etc. in a more pythonic way.

For each sql engine (e.g. sqlite, mysql, ...), a `Driver` is needed. For more details about the `Driver`, please refer to the :ref:`PG_INTRO_DRIVER` section.

Security: what is protected, and what is not
---------------------------------------------

.. warning::
   **Values are bound, identifiers are quoted -- they are not the same thing.**

   - **Values** (the right-hand side of a comparison, the data of `insert()` /
     `update()` / `delete()`) are always passed as parameters
     (``?`` or ``%s``) to the DB-API driver. They are never concatenated into
     the statement, so value-based SQL injection is not possible.
   - **Identifiers** (table names, column names) and **column types** cannot be
     parameters in SQL. They are handled as follows:

     * table and column names are quoted by the driver (``"name"`` for SQLite,
       `````name``` `` for MySQL), and a name containing a NUL byte is
       rejected;
     * ``selection=`` only accepts the table's own column names (or an iterable
       of them), and raises :class:`MercurySQL.errors.NotExistsError` for
       anything else. Passing arbitrary SQL requires the explicit
       ``raw=True`` opt-out -- only do that with trusted input;
     * a custom SQL type must be a plain type name with an optional size and the
       supported modifiers; a string such as ``"TEXT DEFAULT 'x'"`` raises
       :class:`MercurySQL.errors.UnsafeTypeError`.

   Quoting stops injection, but it cannot tell a secret column from a public
   one. Do not build table or column names from untrusted input without your own
   allow-list.

Transactions
------------

- ``db.do(sql1, sql2, ...)`` runs **all** its statements in one transaction:
  they are committed only if every statement succeeded, and rolled back (with
  the driver exception re-raised) otherwise.
- ``with db.transaction():`` groups several ORM calls into one transaction.
- Databases should be closed: ``with DataBase(...) as db:`` or ``db.close()``.


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
     * `==`: equality (`column == None` becomes ``IS NULL``)
     * `!=`: inequality (`column != None` becomes ``IS NOT NULL``)
     * `<`: less than
     * `<=`: less than or equal to
     * `>`: greater than
     * `>=`: greater than or equal to
     * `.in_()`: in (generates ``IN (?, ?, ...)``)
     * `.not_in()`: not in
     * `.between(a, b)`: between (generates ``BETWEEN ? AND ?``)
     * `.like()`: like
     * `.is_null()` / `.is_not_null()`: NULL checks
     * `&`: and
     * `|`: or
     * `~`: not

   .. note:: you should mind the priority of operations when using some of the operators, especially `&` and `|`.

   .. warning::
      Use ``&``, ``|`` and ``~``, **not** Python's ``and``, ``or`` and ``not``.
      Python's boolean operators return one of their operands, which used to
      silently drop a predicate (``(a == 1) and (b == 2)`` returned ``b == 2``).
      Expressions now raise :class:`TypeError` when they are used as a boolean,
      so that mistake fails loudly.


Low-level APIs
--------------

.. autoclass:: MercurySQL.gensql.exp.BasicExp
   :members:
   :undoc-members:
   :special-members: 
   :exclude-members: __weakref__, __module__

   Basic class of Exp, representing a basic query expression that can be used to construct complex queries.

