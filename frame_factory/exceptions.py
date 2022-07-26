class FrameFactoryError(Exception):
    """Base class for frame factory errors"""


class ConfigurationError(FrameFactoryError):
    """The specified configuration is invalid"""
