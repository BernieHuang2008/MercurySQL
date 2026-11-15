"""
MercurySQL.orm.command_queue
============================

Serialize every statement of one database onto a single worker thread.

Why a thread at all? Because a :mod:`sqlite3` connection may only be used from
the thread that created it, while MercurySQL lets *any* thread call
``db.do(...)``. The worker owns the connection; every caller hands it a job and
waits on a :class:`concurrent.futures.Future`.

The rules below are what make the execution layer trustworthy:

* **every job always completes its future** -- with a result, or with the
  original exception. A failed statement raises in the caller; it can never
  block the caller forever.
* **a batch is a transaction** -- ``db.do(sql1, sql2)`` submits one batch, which
  is committed only if *every* statement succeeded, and rolled back otherwise.
* **the connection is opened inside the worker**, and a connection failure is
  reported back to the constructor, so ``DataBase(...)`` raises immediately
  instead of hanging on the first statement.
* **``close()`` exists** -- the worker is stopped with a sentinel and joined,
  and the connection is really closed.
"""

import queue
import threading
from concurrent.futures import Future
from concurrent.futures import TimeoutError as FutureTimeoutError

from ..errors import orm as orm_errors
from ..errors import TransactionError

FETCHALL = -1

__all__ = ["CommandQueue", "CQResult"]

_OP_EXEC = "exec"
_OP_BEGIN = "begin"
_OP_COMMIT = "commit"
_OP_ROLLBACK = "rollback"

_STOP = object()

DEFAULT_CLOSE_TIMEOUT = 10.0


class _Transaction:
    """Bookkeeping for an open transaction."""

    __slots__ = ("failed",)

    def __init__(self):
        self.failed = None


class CQResult:
    """
    The rows returned by one batch of statements.

    A batch holds the rows of its **last** statement, which is what a plain
    ``db.do("SELECT ...")`` should return. A statement without a result set
    (``INSERT``, ``UPDATE``, DDL) yields an empty result instead of an error.
    """

    __slots__ = ("result", "columns")

    def __init__(self, rows=None, columns=None):
        self.result = list(rows) if rows else []
        self.columns = list(columns) if columns else []

    def fetchall(self):
        """Return all rows of the last statement."""
        return list(self.result)

    def fetchone(self):
        """Return the first row, or ``None`` when the result is empty."""
        if not self.result:
            return None
        return self.result[0]

    def fetchmany(self, size: int = 1):
        """Return at most ``size`` rows of the last statement."""
        return list(self.result[:size])

    def __iter__(self):
        return iter(self.result)

    def __len__(self):
        return len(self.result)

    def __getitem__(self, index):
        return self.result[index]

    def __bool__(self):
        return bool(self.result)

    def __repr__(self):
        return f"<CQResult rows={len(self.result)}>"


class CommandQueue:
    """
    Owns one worker thread, one connection and one cursor for a database.

    :param driver: The driver class (``Driver_SQLite``, ``Driver_MySQL``, ...).
    :param db_name: The database name / path.
    :param timeout: Default timeout (seconds) for waiting on a job. ``None``
        means "wait until the statement finishes".
    :param conn_ops: Keyword arguments forwarded to ``driver.connect()``.
    """

    def __init__(self, driver, db_name: str, timeout=None, **conn_ops):
        self.driver = driver
        self.db_name = db_name
        self.conn_ops = conn_ops
        self.timeout = timeout
        self.queue = queue.Queue()

        self._closed = False
        self._connected = threading.Event()
        self._connect_error = None
        self._conn = None
        self._cursor = None
        self._tx = None

        self._thread = threading.Thread(
            target=self._loop,
            name=f"MercurySQL[{db_name}]",
            daemon=True,
        )
        self._thread.start()

        # Wait for the worker to either open the connection or fail. The worker
        # always sets this flag, so this wait cannot hang (apart from a driver
        # whose connect() never returns, which no wrapper can fix).
        self._connected.wait()

        if self._connect_error is not None:
            self._closed = True
            try:
                self.queue.put(_STOP)
            except Exception:
                pass
            raise self._connect_error

    # ------------------------------------------------------------------ #
    # Worker
    # ------------------------------------------------------------------ #
    def _loop(self):
        try:
            conn = self.driver.connect(self.db_name, **self.conn_ops)
            cursor = conn.cursor()
        except BaseException as exc:  # noqa: BLE001 - reported to the caller
            self._connect_error = exc
            self._connected.set()
            return

        self._conn = conn
        self._cursor = cursor
        self._connected.set()

        try:
            while True:
                job = self.queue.get()
                try:
                    if job is _STOP:
                        break
                    op, payload, future = job
                    self._handle(op, payload, future)
                finally:
                    self.queue.task_done()
        finally:
            self._shutdown(conn, cursor)

    def _handle(self, op, payload, future):
        try:
            if op == _OP_EXEC:
                future.set_result(self._exec_batch(payload))
            elif op == _OP_BEGIN:
                self._begin_tx()
                future.set_result(None)
            elif op == _OP_COMMIT:
                self._commit_tx()
                future.set_result(None)
            elif op == _OP_ROLLBACK:
                self._rollback_tx()
                future.set_result(None)
            else:  # pragma: no cover - programming error
                raise orm_errors.queue.QueueError(f"Unknown job type: {op!r}")
        except BaseException as exc:  # noqa: BLE001 - always answer the caller
            if not future.done():
                future.set_exception(exc)

    def _exec_batch(self, statements):
        cursor = self._cursor
        rows, columns = [], []

        # A multi-statement batch is *one* transaction: without an explicit
        # BEGIN, every statement would be committed on its own (SQLite runs in
        # autocommit mode, MySQL commits on conn.commit()), and a failure in the
        # middle would leave the earlier statements persisted -- the F-03 bug.
        own_transaction = self._tx is None and len(statements) > 1
        if own_transaction:
            self.driver.APIs.begin(self._conn)

        try:
            for sql, params in statements:
                cursor.execute(sql, params)
                rows, columns = self._drain(cursor)
        except BaseException:
            if own_transaction:
                try:
                    self._conn.rollback()
                except Exception:
                    pass
            else:
                self._abort_tx()
            raise

        if own_transaction or self._tx is None:
            self._conn.commit()
        return CQResult(rows, columns)

    @staticmethod
    def _drain(cursor):
        """Fetch the current statement's rows, without failing on DML/DDL."""
        description = getattr(cursor, "description", None)
        if description is None:
            return [], []
        return list(cursor.fetchall()), [column[0] for column in description]

    # ------------------------------------------------------------------ #
    # Transactions
    # ------------------------------------------------------------------ #
    def _begin_tx(self):
        if self._tx is not None:
            raise TransactionError("Nested transactions are not supported.")
        self.driver.APIs.begin(self._conn)
        self._tx = _Transaction()

    def _commit_tx(self):
        if self._tx is None:
            raise TransactionError("No transaction is active.")
        failed = self._tx.failed
        self._tx = None
        if failed:
            raise TransactionError(
                "The transaction was rolled back because a statement inside it "
                f"failed ({failed!r})."
            ) from failed
        self._conn.commit()

    def _rollback_tx(self):
        try:
            self._conn.rollback()
        finally:
            self._tx = None

    def _abort_tx(self):
        """Roll back after a failed statement."""
        try:
            self._conn.rollback()
        except Exception:
            pass
        if self._tx is not None:
            self._tx.failed = True

    # ------------------------------------------------------------------ #
    # Caller side
    # ------------------------------------------------------------------ #
    def _submit(self, op, payload):
        if self._closed:
            raise orm_errors.queue.QueueClosedError(
                "This database is closed; no further statement can be executed."
            )
        if not self._thread.is_alive():
            raise orm_errors.queue.QueueCrashedError(
                "The command-queue worker thread is not running."
            )
        future = Future()
        self.queue.put((op, payload, future))
        return future

    def _wait(self, future, timeout=None):
        if timeout is None:
            timeout = self.timeout
        if timeout is None:
            return future.result()
        try:
            return future.result(timeout=timeout)
        except (TimeoutError, FutureTimeoutError):
            # `concurrent.futures.TimeoutError` is a distinct class before
            # Python 3.11, and the driver itself may raise a TimeoutError.
            if future.done():
                raise
            raise orm_errors.queue.QueueTimeoutError(
                f"Statement did not finish within {timeout} seconds. It may "
                "still be running; check the statement or raise the timeout."
            ) from None

    def execute_batch(self, statements, timeout=None):
        """
        Execute ``[(sql, params), ...]`` as one transaction and return a
        :class:`CQResult` holding the last statement's rows.
        """
        future = self._submit(_OP_EXEC, list(statements))
        return self._wait(future, timeout)

    def execute(self, sql, params=(), timeout=None):
        """Execute a single statement (convenience wrapper around a batch)."""
        return self.execute_batch([(sql, params)], timeout=timeout)

    def begin(self, timeout=None):
        """Start an explicit transaction."""
        return self._wait(self._submit(_OP_BEGIN, None), timeout)

    def commit(self, timeout=None):
        """Commit the explicit transaction."""
        return self._wait(self._submit(_OP_COMMIT, None), timeout)

    def rollback(self, timeout=None):
        """Roll back the explicit transaction."""
        return self._wait(self._submit(_OP_ROLLBACK, None), timeout)

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #
    @property
    def closed(self) -> bool:
        return self._closed

    def close(self, timeout: float = DEFAULT_CLOSE_TIMEOUT):
        """
        Stop the worker thread and close the connection.

        Safe to call more than once. If the worker is stuck inside a long
        statement, it is left behind (it is a daemon thread) after ``timeout``.
        """
        if self._closed:
            return
        self._closed = True

        if self._thread.is_alive():
            try:
                self.queue.put(_STOP)
            except Exception:
                pass
            self._thread.join(timeout=timeout)

        # Whatever could not be executed any more is answered with an error, so
        # no caller is left waiting.
        self._reject_pending()

    def _reject_pending(self):
        while True:
            try:
                job = self.queue.get_nowait()
            except queue.Empty:
                return
            try:
                if job is not _STOP:
                    _, _, future = job
                    if not future.done():
                        future.set_exception(
                            orm_errors.queue.QueueClosedError(
                                "This database has been closed."
                            )
                        )
            finally:
                self.queue.task_done()

    def _shutdown(self, conn, cursor):
        """Release the driver resources (runs on the worker thread)."""
        try:
            if cursor is not None:
                cursor.close()
        except Exception:
            pass
        try:
            if conn is not None:
                conn.close()
        except Exception:
            pass
        self._reject_pending()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
