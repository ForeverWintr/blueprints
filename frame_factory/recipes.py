from __future__ import annotations
import typing as tp
from abc import ABC, abstractmethod
import dataclasses


class Recipe(ABC):
    """Base class for recipes"""

    def get_dependency_recipes(self) -> tuple[Recipe, ...]:
        """Return a tuple of recipes that this recipe depends on"""
        return ()

    @abstractmethod
    def extract_from_dependency(self, *args) -> tp.Any:
        """Given positional dependencies, extract the data that this recipe describes. args will be
        the results of instantiating the recipes returned by `get_dependency_recipes` above"""

    ### Below this line, methods are internal and not intended to be overriden.

    def __init_subclass__(cls, **kwargs) -> None:
        r = dataclasses.dataclass(cls, frozen=True, repr=False, kw_only=True)
        assert r is cls
