from enum import Enum, auto


class NodeAttrs:
    """Constants for attributes defined on nodes."""

    output = "output"
    build_status = "build_status"


class BuildStatus(Enum):
    NOT_STARTED = auto()
    BUILDING = auto()
    BUILT = auto()
    ERROR = auto()
