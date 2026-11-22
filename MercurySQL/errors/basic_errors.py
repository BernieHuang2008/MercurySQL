class MercurySQLError(Exception):
    """Base class for MercurySQL errors."""
    pass


class MSQLSyntaxError(MercurySQLError):
    """MSQLSyntaxError is raised when a syntax error is found in the query."""
    pass


class MSQLDriverError(MercurySQLError):
    """
    MSQLDriverError is raised when a driver error is found in the query.

    .. note::
       If the third-party drivers wants to create there own errors, it is recommended to inherit this class, for better error handling.
    """
    pass


class MSQLCommandError(MercurySQLError):
    """
    MSQLCommandError is raised when the command queue cannot execute a statement.

    This is different from a driver error: the statement may be perfectly valid
    SQL, but the execution machinery failed (timeout, closed database, ...).
    """
    pass
