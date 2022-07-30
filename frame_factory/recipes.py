from __future__ import annotations
import typing as tp
from abc import ABC, abstractmethod


class Recipe(ABC):
    """Base class for recipes"""

    @abstractmethod
    def identity_key(self) -> tuple:
        """Return a key from this recipe's parameters. This is used for hashing and equality, and it should be possible to re-create the recipe using Recipe(**dict(r.key()))"""

    def get_dependency_recipes(self) -> tuple[Recipe, ...]:
        """Return a tuple of recipes that this recipe depends on"""
        return ()

    @abstractmethod
    def extract_from_dependency(self, *args) -> tp.Any:
        """Given positional dependencies, extract the data that this recipe describes. args will be
        the results of instantiating the recipes returned by `get_dependency_recipes` above"""

    def __hash__(self):
        return hash(self.identity_key())

    def __eq__(self, other: tp.Any) -> bool:
        if not isinstance(other, Recipe):
            return NotImplemented
        return self.identity_key() == other.identity_key()
