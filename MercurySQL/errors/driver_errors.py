from .basic_errors import MSQLDriverError

class DriverIncompatibleError(MSQLDriverError):
    """
    DriverIncompatibleError is raised when the driver version is not supported by MercurySQL.

    For details of MercurySQL Versioning System, please see the `Drivers.Versioning` Chapter. 
    """
    def __init__(self, driver: str, dv: str, cv: str):
        """
        :param driver: Driver Name.
        :param dv: Driver Version.
        :param cv: Current Version.
        """
        self.message = f"Driver `{driver}`(v{dv}) is not supported by MercurySQL(v{cv}). Please update your Driver/MercurySQL to the latest version."
        super().__init__(self.message)
