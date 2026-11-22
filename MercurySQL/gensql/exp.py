"""
MercurySQL.gensql.exp
=====================
This file offers the `Exp` class, which is used to construct complex query expressions for the MercurySQL package.

Classes
-------
- `BasicExp`: Base class for basic expressions.
- `Exp`: Class for constructing complex query expressions.

.. versionchanged:: 0.2.0
   Several expressions used to emit invalid SQL (and therefore hang the caller),
   or to silently drop a predicate:

   * ``column == None`` now generates ``IS NULL`` (and ``!= None`` generates
     ``IS NOT NULL``);
   * ``in_([...])`` generates ``IN (?, ?, ...)`` instead of binding the string
     ``"(1, 2)"``;
   * ``between(a, b)`` generates ``BETWEEN ? AND ?``;
   * ``~exp`` generates ``NOT (...)``;
   * ``exp1 & exp2`` / ``exp1 | exp2`` are the only way to combine conditions:
     using Python's ``and``/``or`` now raises instead of silently keeping one
     operand (an authorization filter written with ``and`` used to be dropped).
"""

from typing import Any, Iterable, Tuple, Union

from ..errors import NotSpecifiedError

#: Internal placeholder for a bound value. It is replaced with the driver's
#: parameter marker when the statement is built, never inside ``db.do()``, so a
#: user query that literally contains this text is no longer rewritten.
PAYLOAD = "___!!!PAYLOAD!!!___"


def _combine(value) -> Tuple[str, tuple]:
    """Convert a value into ``(sql_fragment, parameters)``."""
    if isinstance(value, BasicExp):
        return value.formula()
    if value is None:
        return "", ()
    return PAYLOAD, (value,)


class BasicExp:
    def __init__(self, exp1, oper="", exp2=None):
        self.exp1 = exp1
        self.oper = oper
        self.exp2 = exp2
        self._formula = ("", ())

        self.gen_formula()

    @staticmethod
    def convert(value: Any) -> Tuple[str, tuple]:
        """
        Convert value into a form that can be used in a SQL query.

        :param value: The value to convert.
        :type value: Any

        :return: The converted value in the form of `(sql_command, paras)`.
        :rtype: Tuple[str, tuple]

        Example Usage:

        .. code-block:: python

            BasicExp.convert(1)                 # ('___!!!PAYLOAD!!!___', (1,))
            BasicExp.convert('Bernie')          # ('___!!!PAYLOAD!!!___', ('Bernie',))
            BasicExp.convert(None)              # ('', ())
            BasicExp.convert(Exp('id') == 1)    # ('(id = ___!!!PAYLOAD!!!___)', (1,))
            ...

        """
        return _combine(value)

    def gen_formula(self) -> None:
        """
        [Helper] Generate the formula of the expression.

        .. note :: You can also construct a formula by yourself, just set the `_formula` attribute to a tuple in the form of `(sql_command, paras)`.
        """
        oper = self.oper

        if oper == "":
            self._formula = (self.exp1, ())
            return

        if oper == "NOT":
            inner, paras = _combine(self.exp1)
            self._formula = (f"(NOT {inner})", tuple(paras))
            return

        if oper in ("IN", "NOT IN"):
            left, paras = _combine(self.exp1)
            values = list(self.exp2) if self.exp2 is not None else []
            if not values:
                # `x IN ()` is a syntax error in SQLite and MySQL; an empty set
                # matches nothing (or everything, for NOT IN).
                self._formula = ("(1 = 0)" if oper == "IN" else "(1 = 1)", ())
                return
            marks = ", ".join([PAYLOAD] * len(values))
            self._formula = (
                f"({left} {oper} ({marks}))",
                tuple(paras) + tuple(values),
            )
            return

        if oper == "BETWEEN":
            low, high = self.exp2
            left, left_paras = _combine(self.exp1)
            low_sql, low_paras = _combine(low)
            high_sql, high_paras = _combine(high)
            self._formula = (
                f"({left} BETWEEN {low_sql} AND {high_sql})",
                tuple(left_paras) + tuple(low_paras) + tuple(high_paras),
            )
            return

        # `column == None` must be `IS NULL`; `(id = )` is a syntax error.
        if self.exp2 is None and oper in ("=", "<>"):
            left, left_paras = _combine(self.exp1)
            self._formula = (
                f"({left} {'IS NULL' if oper == '=' else 'IS NOT NULL'})",
                tuple(left_paras),
            )
            return

        if self.exp2 is None:
            raise ValueError(
                f"`{oper}` needs a right-hand value; use `== None` for a NULL check."
            )

        left, left_paras = _combine(self.exp1)
        right, right_paras = _combine(self.exp2)
        self._formula = (
            f"({left} {oper} {right})",
            tuple(left_paras) + tuple(right_paras),
        )

    def formula(self, payload: str = None) -> Tuple[str, tuple]:
        """
        Return the formula of the expression in the form of (sql_command, paras).

        :param payload: The parameter marker of the target driver
            (``?`` or ``%s``). Defaults to ``?``.
        """
        sql, paras = self._formula
        return sql.replace(PAYLOAD, "?" if payload is None else payload), paras

    # Using an expression as a boolean silently discarded one operand:
    # ``(a == 1) and (b == 2)`` evaluates to ``b == 2`` only, which turned an
    # authorization filter into "no filter". Fail loudly instead.
    def __bool__(self):
        raise TypeError(
            "MercurySQL expressions cannot be used as booleans. "
            "Use `&` for AND, `|` for OR and `~` for NOT instead of "
            "Python's `and`, `or` and `not`."
        )

    def __repr__(self):
        return f"<{type(self).__name__} {self._formula[0]!r}>"


class Exp(BasicExp):
    def __init__(self, o1, op="", o2="", **kwargs):
        """
        Acceptable addition attributes:
        - table: Table ...................... the table to search
        - _str: str ......................... the string to show when print the object
        """
        super().__init__(o1, op, o2)

        self.table = kwargs.get("table", None)
        self._str = kwargs.get("_str", "<MercurySQL.core.Exp object>")
        self.result = None
        self._result_generation = None

        if isinstance(o1, Exp):
            self.table = self.table or o1.table
        if isinstance(o2, Exp):
            self.table = self.table or o2.table

    # ---------- comparison ----------
    def __eq__(self, __value: Union["Exp", int, str]) -> "Exp":
        return Exp(self, "=", __value)

    def __ne__(self, __value: Union["Exp", int, str]) -> "Exp":
        return Exp(self, "<>", __value)

    def __lt__(self, __value: Union["Exp", int, str]) -> "Exp":
        return Exp(self, "<", __value)

    def __le__(self, __value: Union["Exp", int, str]) -> "Exp":
        return Exp(self, "<=", __value)

    def __gt__(self, __value: Union["Exp", int, str]) -> "Exp":
        return Exp(self, ">", __value)

    def __ge__(self, __value: Union["Exp", int, str]) -> "Exp":
        return Exp(self, ">=", __value)

    def between(self, __value1, __value2) -> "Exp":
        """
        ``column BETWEEN low AND high``.
        """
        return Exp(self, "BETWEEN", (__value1, __value2))

    def in_(self, __value: Iterable) -> "Exp":
        """
        ``column IN (v1, v2, ...)``.

        An empty iterable produces a condition that is always false.
        """
        if isinstance(__value, (str, bytes)):
            raise TypeError("`in_()` expects an iterable of values, not a string.")
        return Exp(self, "IN", tuple(__value))

    def not_in(self, __value: Iterable) -> "Exp":
        """``column NOT IN (v1, v2, ...)``."""
        if isinstance(__value, (str, bytes)):
            raise TypeError("`not_in()` expects an iterable of values, not a string.")
        return Exp(self, "NOT IN", tuple(__value))

    def like(self, __value: str) -> "Exp":
        return Exp(self, "LIKE", __value)

    def is_null(self) -> "Exp":
        """``column IS NULL`` (same as ``column == None``)."""
        return Exp(self, "=", None)

    def is_not_null(self) -> "Exp":
        """``column IS NOT NULL`` (same as ``column != None``)."""
        return Exp(self, "<>", None)

    # ---------- combination ----------
    def __and__(self, __value: Union["Exp", int, str]) -> "Exp":
        return Exp(self, "AND", __value)

    def __or__(self, __value: Union["Exp", int, str]) -> "Exp":
        return Exp(self, "OR", __value)

    def __invert__(self) -> "Exp":
        return Exp(self, "NOT", None)

    # ---------- execution ----------
    def _bound_table(self, table=None):
        table = table or self.table
        if table is None:
            raise NotSpecifiedError("Table not specified.")
        return table

    def build_query(self, table=None, selection: str = "*", limit=None, offset=None):
        """
        Return ``(sql, parameters)`` for this expression.

        :param table: The table to query (defaults to the bound table).
        :param selection: The **already quoted** projection built by `Table`.
        :param limit: Optional row limit.
        :param offset: Optional row offset.
        """
        table = self._bound_table(table)
        driver = table.db.driver
        condition, paras = self.formula(driver.payload)
        cmd = driver.APIs.gensql.query(
            table.table_name, selection, condition, limit=limit, offset=offset
        )
        return cmd, paras

    def query(self, table=None, select="*", limit=None, offset=None) -> list:
        """
        Execute query and return the raw rows.
        """
        table = self._bound_table(table)
        selection_sql, _ = table._build_selection(select)
        cmd, paras = self.build_query(table, selection_sql, limit=limit, offset=offset)
        return table.db.do(cmd, paras=[paras]).fetchall()

    def delete(self, table=None) -> None:
        """
        Execute delete.
        """
        table = self._bound_table(table)
        driver = table.db.driver

        condition, paras = self.formula(driver.payload)
        cmd = driver.APIs.gensql.delete(table.table_name, condition)
        table.db.do(cmd, paras=[paras])

    def update(self, data, /, table=None) -> None:
        """
        Execute update.
        """
        table = self._bound_table(table)
        table.update(self, data)

    # ---------- caching ----------
    def invalidate(self) -> None:
        """Forget the cached rows, so the next iteration queries again."""
        self.result = None
        self._result_generation = None

    def __iter__(self):
        """
        use magic method `__iter__` to search.

        The rows are cached, but the cache is dropped as soon as the database
        changes (`DataBase.generation`), so iterating again after a write does
        not return stale data.
        """
        table = self._bound_table()
        generation = table.db.generation

        if self.result is None or self._result_generation != generation:
            data = self.query()
            keys = table.columns
            self.result = [dict(zip(keys, row)) for row in data]
            self._result_generation = generation

        return iter(self.result)

    def __str__(self):
        return self._str
