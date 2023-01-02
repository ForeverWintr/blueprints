from __future__ import annotations
from enum import Enum, auto
import typing as tp
import dataclasses


class NodeAttrs:
    """Constants for attributes defined on nodes."""

    output = "output"
    build_status = "build_status"
    dependency_request = "dependency_request"


class BuildStatus(Enum):
    NOT_STARTED = auto()
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
}
