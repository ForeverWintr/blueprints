class blueprintsError(Exception):
    """Base class for frame factory errors"""


class ConfigurationError(blueprintsError):
    """The specified configuration is invalid"""


class MissingDependencyError(blueprintsError):
    """An upstream dependency is missing and at least one dependency does not allow missing"""
