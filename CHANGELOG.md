# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/), and the
project uses [Semantic Versioning](https://semver.org/).

## [0.2.0]

This release fixes the findings of the project review (issue #1, upstream
`BernieHuang2008/MercurySQL#38`). Several fixes change behaviour on purpose;
they are listed as **Breaking** below.

### Fixed

- **F-01 — a failed statement no longer hangs the caller.** All SQL runs in a
  worker thread that now always completes a `Future`: a failing statement
  re-raises the driver's exception instead of printing it to stderr and blocking
  `Event.wait()` forever. A connection failure is raised by the `DataBase`
  constructor instead of hanging every later call.
- **F-02 — `setPrimaryKey()` no longer swaps column values.** The SQLite rebuild
  names every column explicitly in both `CREATE` and `INSERT ... SELECT`, and
  runs in one transaction, so values keep their column and an interrupted
  rebuild cannot leave the data in a temporary table.
- **F-03 — `db.do(sql1, sql2)` is one transaction.** All statements are
  committed together, rolled back together, and the failure is raised. The
  stale-result bug (a reused `Event` returning the first statement's rows) is
  gone.
- **F-04 — identifiers are quoted, `selection` is validated.** Table and column
  names are quoted per dialect; `selection` only accepts the table's own
  columns; a type string must be a plain SQL type. `selection="id, (SELECT
  secret FROM users) AS leak"` and `table['x'] = "TEXT DEFAULT 'pwn'"` are now
  errors.
- **F-05 — `insert(..., __auto=True)` is a real UPSERT.** Unspecified columns
  keep their value on both backends (`ON CONFLICT ... DO UPDATE` /
  `ON DUPLICATE KEY UPDATE`). It requires a primary key.
- **F-06 — the expression API emits valid SQL.** `== None` → `IS NULL`,
  `in_()` → `IN (?, ?, ...)`, `between()` → `BETWEEN ? AND ?`, `~exp` →
  `NOT (...)`. `del table['col']` passes the table name, `update()` with no data
  raises, and deleting the last column raises instead of dropping the table.
- **F-07 — thread and connection lifecycle.** `DataBase.close()` / `dispose()`
  / context-manager support stop the worker and close the connection; nothing
  leaks per instance any more.
- **F-08 — MySQL driver.** `int` → `BIGINT`, `str` → `VARCHAR(255)`, the
  `DFAULT` typo is gone, defaults are quoted, `USE`/`CREATE DATABASE` quote the
  database name, the `VALUES()` UPSERT is replaced by the row-alias form, the
  cursor monkey-patch is removed, and `MercurySQL[mysql]` declares the
  dependency.
- **F-09 — CI and release.** Test workflows run on `pull_request` (they used
  `pull_request_target` and therefore tested the base branch), actions are
  pinned to commit SHAs, `dependabot.yml` is valid, publishing is gated on the
  test job and uses PyPI Trusted Publishing, and the broken weekly "release"
  workflow was replaced by a manual version-bump workflow.
- **F-10 — documentation.** The security claim now says exactly what is
  parameterised and what is quoted; the README no longer promises "prevent data
  loss"; `main` is released as 0.2.0, so the documented `Exp.update()` exists in
  the published artifact.
- **F-11 — packaging.** `pyproject.toml` with `requires-python = ">=3.8"`, wheel
  and sdist through `python -m build`, `MercurySQL[mysql]` / `[dev]` extras,
  pinned dev requirements. `setup.py` and its cwd-dependent file reads are gone.
- **F-12 — identifier casing.** Table and column names are resolved
  case-insensitively where the backend is, so `db["users"]` finds
  `createTable("Users")` instead of creating a phantom table. Internal
  `sqlite_%` tables no longer show up in `db.tables`.
- **F-13 — performance / resources.** `select(limit=, offset=)`,
  `select_iter()` (paged), `count()`, `insert_many()` (one statement, one
  commit), `db.transaction()`, and cached `Exp` results are invalidated when the
  database changes.
- Low-severity items: `check_version()` accepts two-part versions,
  `DataBase()` without a driver raises `NotSpecifiedError`, `fetchone()` returns
  `None` on an empty result, `paras` is no longer mutated, the
  `___!!!PAYLOAD!!!___` sentinel no longer rewrites literal SQL, and the
  duplicated class definitions were removed.

### Breaking

- Driver API 0.2.0: `insert`/`update` take a column-name list,
  `insert_or_update` takes `primary_keys`, `query` takes `limit`/`offset`, and
  `values` is the complete `VALUES` tail. A driver written for 0.1.x must be
  updated (see the driver guide) and will otherwise raise
  `DriverIncompatibleError`.
- `Exp` raises `TypeError` when used as a boolean. Use `&`, `|`, `~` instead of
  `and`, `or`, `not`.
- `selection` rejects unknown columns unless `raw=True` is passed.
- `insert(__auto=True)` requires a primary key and updates instead of replacing
  the row.
- Deleting the last column raises `NotSupportedError`; use `db.deleteTable()`.

### Added

- `DataBase.close()`, `dispose()`, context-manager support and
  `DataBase.transaction()`.
- `Table.select_iter()`, `count()`, `insert_many()`, `resolveColumn()`,
  `primaryKeys`; `Exp.invalidate()`, `is_null()`, `is_not_null()`, `not_in()`.
- `MercurySQL.errors`: `InvalidIdentifierError`, `UnsafeTypeError`,
  `TransactionError`, `QueueError`, `QueueTimeoutError`, `QueueClosedError`,
  `QueueCrashedError`.
- A `pytest` suite (`tests/test_regressions.py`) covering every finding.
- `SECURITY.md`, `CHANGELOG.md`, `pyproject.toml`.

### Removed

- `docs/build/` (93 generated files, ~6 MB) from version control.
- The unfinished `orm/connection_pool.py` experiments are no longer imported by
  the package entry points.
