from __future__ import annotations
import typing as tp
import json
import dataclasses

from frozendict import frozendict

from assembler import util
from assembler.constants import Sentinel

from assembler.recipes.base import Recipe, RECIPE_TYPE_REGISTRY


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

    def recipes(self) -> tp.Iterator[Recipe]:
        yield from self._recipe_to_key

    def get(self, item: Recipe, default=None):
        return self._recipe_to_key.get(item, default)


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

    registry = RecipeRegistry.from_recipes([recipe])

    result = {}
    for r in registry.recipes():
        recipe_data = {
            "attributes": r.to_serializable_dict(registry),
            "type": RECIPE_TYPE_REGISTRY.key(type(r)),
        }
        result[registry.get(r)] = recipe_data
    return json.dumps(result)


def recipe_from_json(json_str: str) -> Recipe:
    """Deserialize Json-ified recipes"""
    loaded = json.loads(json_str)
    asdf
