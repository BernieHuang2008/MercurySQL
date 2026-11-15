from ..basic_errors import MSQLCommandError


class QueueError(MSQLCommandError):
    """Base class for errors raised by the command queue."""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class QueueTimeoutError(QueueError):
    """
    A statement did not finish before the configured timeout.

    .. warning::
       The statement may still be running inside the worker thread when this is
       raised. Do not assume it did not happen; use a longer timeout, or fix the
       statement, instead of retrying blindly.
    """
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class QueueClosedError(QueueError):
    """The command queue (and therefore the database) has been closed."""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class QueueCrashedError(QueueError):
    """The worker thread died, so no further statement can be executed."""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
