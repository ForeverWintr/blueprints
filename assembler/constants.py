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
    ERROR = auto()


BUILD_STATUS_TO_COLOR = {
    BuildStatus.NOT_STARTED: "#eaecee",
    BuildStatus.BUILDING: "#f4d03f",
    BuildStatus.BUILT: "#2ecc71",
    BuildStatus.ERROR: "#e74c3c",
}
