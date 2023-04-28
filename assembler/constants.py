from __future__ import annotations
from enum import Enum, auto


class NodeAttrs:
    """Constants for attributes defined on blueprint nodes.

    Meanings:

    is_output: This recipe is an output (rather than an internal dependency).

    build_status: The current state of the recipe. See BuildStatus enum.

    dependency_request: The DependencyRequest returned by the recipe's get_dependency_request
    method.
    """

    is_output = "is_output"
    build_status = "build_status"
    dependency_request = "dependency_request"


class BuildStatus(Enum):
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


BUILD_STATUS_TO_COLOR = {
    BuildStatus.NOT_STARTED: "#eaecee",
    BuildStatus.BUILDING: "#f4d03f",
    BuildStatus.BUILT: "#2ecc71",
    BuildStatus.MISSING: "#e74c3c",
    BuildStatus.BUILDABLE: "#e70000",
}
