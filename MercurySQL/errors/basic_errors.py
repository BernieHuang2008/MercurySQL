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

