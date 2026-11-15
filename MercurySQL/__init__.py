"""
MercurySQL (M.SQL)
==================

Operate SQL in a more pythonic way.

This package provides classes for interacting with a SQL database, including:

- DataBase: Represents a SQL database and provides methods for creating tables, executing SQL commands, and retrieving table objects.

- Table: Represents a table in the database and provides methods for adding columns, deleting columns, inserting rows, and executing queries.

- Exp: Represents a query expression that can be used to construct complex queries.

Please refer to the individual class documentation for more details.
"""

import os

from .gensql import DataBase, Table, set_driver
from . import drivers

_real_path = os.path.dirname(os.path.realpath(__file__))

with open(os.path.join(_real_path, "VERSION"), encoding="utf-8") as _f:
    __version__ = _f.read().strip()

__all__ = ["DataBase", "Table", "set_driver", "drivers", "__version__"]
