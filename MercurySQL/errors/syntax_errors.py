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

    Currently, this error is not used in MercurySQL.
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
