Introduction to MercurySQL Drivers
==================================

.. warning::
   All Drivers **MUST** be defined as subclasses of the `BaseDriver <base.html>`_ class.

.. _driver-api-0_2_0:

Driver API 0.2.0 (breaking changes)
-----------------------------------

Version 0.2.0 changed the driver contract so that identifiers can be quoted and
upserts can be built per dialect. A driver written for 0.1.x must be updated:

- ``BaseDriver.APIs`` now provides :func:`quote_ident` (``"name"`` by default;
  MySQL uses backticks). Subclass it -- do **not** redefine ``class APIs:`` from
  scratch, or you lose the helper.
- ``gensql.insert(table_name, columns, values)``: ``columns`` is now a
  **list of column names** (quote each one), and ``values`` is the **complete
  VALUES tail**, e.g. ``"(?, ?)"`` or ``"(?, ?), (?, ?)"``.
- ``gensql.insert_or_update(table_name, columns, values, primary_keys)``:
  build a real UPSERT. ``primary_keys`` are the primary-key column names.
- ``gensql.update(table_name, columns, condition)``: ``columns`` is a **list of
  column names**.
- ``gensql.query(table_name, selection, condition, limit=None, offset=None)``:
  ``selection`` arrives **already quoted**; ``limit``/``offset`` must be
  honoured (``LIMIT n OFFSET m``).
- ``APIs.get_primary_keys(session, table_name)`` should return the primary-key
  column names in key order (``[]`` means "unknown"; ``__auto`` then refuses to
  guess). ``APIs.begin(conn)`` starts an explicit transaction.
- ``TypeParser.parse()`` must reject non-plain type strings, using
  :func:`MercurySQL.drivers.base.check_type_sql`.
- Set ``table_name_case_insensitive`` / ``column_name_case_insensitive`` to
  describe the dialect (SQLite: both true; MySQL: table names depend on
  ``lower_case_table_names``, columns are always case-insensitive).


Versioning
----------
**About Versioning**:

Every version name is composed of 3 numbers separated by dots (e.g. `1.0.0`).

- The first number is the **major** version. Major versions are incompatible.
- The second number is the **minor** version. Minor versions are **Backwards Compatible**. This means that the driver **MUST** be compatible with the previous minor version of MercurySQL, only adding some new features.
- The third number is the **patch** version. Patch versions are compatible.

**In short**, if the following conditions are met, the driver will be judged as `incompatible` with the current version of MercurySQL:

- `driver.major != mercury.major`
- `driver.minor < mercury.minor`

Drivers which are not compatible with the current version of MercurySQL will raise an `DriverIncompatibleError` exception.
