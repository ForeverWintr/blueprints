class AssemblerError(Exception):
    """Base class for frame factory errors"""


class ConfigurationError(AssemblerError):
    """The specified configuration is invalid"""


class MissingDependencyError(AssemblerError):
    """An upstream dependency is missing and at least one dependency does not allow missing"""


class TimeoutError(AssemblerError):
    """A multiprocessed task timed out."""
