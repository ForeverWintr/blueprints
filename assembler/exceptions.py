class AssemblerError(Exception):
    """Base class for frame factory errors"""


class ConfigurationError(AssemblerError):
    """The specified configuration is invalid"""
