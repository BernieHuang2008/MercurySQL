class DuplicateError(Exception):
    def __init__(self, msg: str):
        self.message = msg
        super().__init__(msg)


class NotExistsError(Exception):
    def __init__(self, msg: str):
        self.message = msg
        super().__init__(msg)


class NotSupportedError(Exception):
    def __init__(self, msg: str):
        self.message = msg
        super().__init__(msg)


class ConfilictError(Exception):
    def __init__(self, msg: str):
        self.message = msg
        super().__init__(msg)

class NotSpecifiedError(Exception):
    def __init__(self, msg: str):
        self.message = msg
        super().__init__(msg)
