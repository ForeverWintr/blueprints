from __future__ import annotations
import typing as tp
import json
import dataclasses

from frozendict import frozendict

from assembler import util

if tp.TYPE_CHECKING:
    from assembler.recipes.base import Recipe, Dependencies, DependencyRequest


class RecipeRegistry:
    KEY_PREFIX = "RR"

    def __init__(
        self,
        key_to_recipe: dict[str, Recipe] | None = None,
    ):
        """Maps recipes to process-unique ids. For use in serializing."""
        self._recipe_to_key = {}
        self._key_to_recipe = {}
        if key_to_recipe:
            self._key_to_recipe = key_to_recipe
            self._recipe_to_key = {r: k for k, r in key_to_recipe.items()}

    @classmethod
    def from_recipes(cls, recipes: tp.Iterable[Recipe]) -> tp.Self:
        return cls(
            {
                f"{cls.KEY_PREFIX}_{id(r)}": r
                for r, _ in util.recipes_and_dependencies(recipes)
            }
        )

    def add(self, recipe: Recipe) -> None:
        if recipe not in self._recipe_to_key:
            key = f"{self.KEY_PREFIX}_{id(recipe)}"
            self._key_to_recipe[key] = recipe
            self._recipe_to_key[recipe] = key


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
    """Convert to a json representation that does not duplicate recipes. A recipe's
    dependencies are replaced with IDs into a registry mapping."""

    # registry that maps both ways
    # for each recipe in registry, replace any recipe fields with references to registry.
    r = RecipeRegistry.from_recipes([recipe])
    asdf
