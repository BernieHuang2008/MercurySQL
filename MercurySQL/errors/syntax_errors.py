from .basic_errors import MSQLSyntaxError


class DuplicateError(MSQLSyntaxError):
    """
    DuplicateError is raised when a duplicate entry is found in the database.

    E.g.:
    - Trying to create a table with the same name as an existing table.
    - Trying to add a column with the same name as an existing column.
    """
    def __init__(self, msg: str):
        self.message = msg
        super().__init__(msg)


class NotExistsError(MSQLSyntaxError):
    """
    NotExistsError is raised when an entry is not found in the database.

    E.g.:
    - Trying to use/delete a table which is not existing.
    - Trying to use/delete a column which is not existing.
    """
    def __init__(self, msg: str):
        self.message = msg
        super().__init__(msg)


class NotSupportedError(MSQLSyntaxError):
    """
    NotSupportedError is raised when an operation is not supported by the database.

    E.g.:
    - Asking a driver for a feature it does not implement.
    """
    def __init__(self, msg: str):
        self.message = msg
        super().__init__(msg)


class ConfilictError(MSQLSyntaxError):
    """
    ConfilictError is raised when an operation conflicts with the database.

    E.g.:
    - Trying to add a new column, but the column name is already used, and the two columns has different type.
    """
    def __init__(self, msg: str):
        self.message = msg
        super().__init__(msg)


class NotSpecifiedError(MSQLSyntaxError):
    """
    NotSpecifiedError is raised when a required parameter is not specified.

    E.g.:
    - Trying to create a DataBase object without specifying the driver.
    - Trying to execute a query without specifying the table.
    """
    def __init__(self, msg: str):
        self.message = msg
        super().__init__(msg)


class InvalidIdentifierError(MSQLSyntaxError):
    """
    InvalidIdentifierError is raised when a table/column name is not a usable SQL identifier.

    Identifiers are quoted, never bound as parameters, so they must be validated
    before they are pasted into a statement.

    E.g.:
    - An empty name, or a name containing a NUL byte.
    - A name that is not a ``str``.
    """
    def __init__(self, msg: str):
        self.message = msg
        super().__init__(msg)


class UnsafeTypeError(MSQLSyntaxError):
    """
    UnsafeTypeError is raised when a type string is not a plain SQL type.

    MercurySQL builds DDL by pasting the parsed type into ``CREATE TABLE`` /
    ``ALTER TABLE``. Only plain type names (optionally with a size, and with the
    few column modifiers MercurySQL itself understands) are accepted, so a type
    string cannot smuggle extra DDL into the statement.
    """
    def __init__(self, msg: str):
        self.message = msg
        super().__init__(msg)


class TransactionError(MSQLSyntaxError):
    """
    TransactionError is raised when a transaction cannot be committed.

    Examples:

    * committing a transaction in which a statement already failed (it has
      been rolled back, so committing would silently commit nothing);
    * starting a nested transaction.
    """
    def __init__(self, msg: str):
        self.message = msg
        super().__init__(msg)
