from __future__ import annotations
from enum import Enum, auto


class BuildState(Enum):
    NOT_STARTED = auto()
    BUILDABLE = auto()
    BUILDING = auto()
    BUILT = auto()
    MISSING = auto()


class MissingDependencyBehavior(Enum):
    """Setting to determine how a recipe behaves when one of its dependencies are
    missing. The options are:

    SKIP: If an upstream dependency is missing, treat this recipe as missing as well.
    This will result in a failure if the recipe has allow_missing=False.

    BIND: The recipe receives a missing placeholder for any of its dependencies that are
    missing.
    """

    SKIP = auto()
    BIND = auto()


class Sentinel(Enum):
    NOT_SET = auto()


BUILD_STATE_TO_COLOR = {
    BuildState.NOT_STARTED: "#eaecee",
    BuildState.BUILDING: "#f4d03f",
    BuildState.BUILT: "#2ecc71",
    BuildState.MISSING: "#e74c3c",
    BuildState.BUILDABLE: "#e70000",
}
