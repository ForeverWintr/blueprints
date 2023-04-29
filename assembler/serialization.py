from __future__ import annotations
import typing as tp
import json

from frozendict import frozendict

from assembler import util

if tp.TYPE_CHECKING:
    from assembler.recipes.base import Recipe, Dependencies, DependencyRequest


def recipe_registry(recipes: tp.Iterable[Recipe]) -> dict[int, Recipe]:
    """Return a dictionary mapping recipe ids to recipes, for the provided recipes and
    all of their dependencies. For use in serialization"""
    return {id(r): r for r, _ in util.recipes_and_dependencies(recipes)}


class ImmutableJsonDecoder(json.JSONDecoder):
    """Subclass of JSONDecoder that replaces lists with tuples and dicts with
    frozendicts."""

    @classmethod
    def _make_immutable(cls, obj: list | dict) -> tuple | frozendict:
        """Recurse through an arbitrarily nested structure of dicts and lists, and replace
        them with frozendicts and tuples. Intended to be called on the result of
        json.decode, so assumes no cycles and immutable keys."""
        constructor = frozendict
        try:
            items = obj.items()
        except AttributeError:
            items = enumerate(obj)
            constructor = tuple

        for k, v in items:
            if isinstance(v, (list, dict)):
                obj[k] = cls._make_immutable(v)
        return constructor(obj)

    def decode(self, string: str):
        obj = super().decode(string)
        return self._make_immutable(obj)


def recipe_to_json(recipe: Recipe) -> str:
    asdf
