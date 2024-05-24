class ConnPoolErrors(Exception):
    """
    The super class of all errors related to the connection pool
    """
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class ConnPoolConnectionAlreadyExistsError(ConnPoolErrors):
    """
    A connection for the target thread already exists in the conn-pool
    """
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class ConnPoolNotClosedError(ConnPoolErrors):
    """
    A connection pool is not fully closed
    """
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)