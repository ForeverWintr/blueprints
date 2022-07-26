from __future__ import annotations
import typing as tp
from abc import ABC, abstractmethod

class Recipe(ABC):
    '''Base class for recipes'''

    @abstractmethod
    def identity_key(self) -> tuple:
        '''Return a key from this recipe's parameters. This is used for hashing and equality, and it should be possible to re-create the recipe using Recipe(**dict(r.key()))'''

    def __hash__(self):
        return hash(self.identity_key())

    def __eq__(self, other: tp.Any) -> bool:
        if not isinstance(other, Recipe):
            return NotImplemented
        return self.identity_key() == other.identity_key()

    @classmethod
    def group_by_dependency(cls, recipes: tuple[Recipe]) -> dict[tuple[Recipe]|None, tuple[Recipe]]:
        '''Given an iterable of recipes of this type, group them by shared dependencies'''
        return {None: recipes}
