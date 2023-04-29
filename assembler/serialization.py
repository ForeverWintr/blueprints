from __future__ import annotations
import typing as tp
import json
import dataclasses

from frozendict import frozendict

from assembler import util
from assembler.constants import Sentinel

from assembler.recipes.base import Recipe


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

    def get_key(self, recipe: Recipe, default: tp.Any = Sentinel.NOT_SET) -> str:
        if default is Sentinel.NOT_SET:
            return self._recipe_to_key[recipe]
        return self._recipe_to_key.get(recipe, default)

    def iter_recipes(self) -> tp.Iterator[Recipe]:
        return iter(self._recipe_to_key)


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


def _flat(items: tp.ItemsView) -> tp.Iterator:
    return (x for item in items for x in item)


def recipe_to_json(recipe: Recipe) -> str:
    """Convert to a json representation that does not duplicate recipes. A recipe's
    dependencies are replaced with IDs into a registry mapping."""

    # registry that maps both ways
    registry = RecipeRegistry.from_recipes([recipe])
    # for each recipe in registry, replace any recipe fields with references to registry.
    # That doesn't work because I need to replace them.
    # No, it does. The upper level just has to refer into the registry.

    #:. We only need to look at each recipe's attributes and inside any iterables
    # attached to it. We do not need to recurse.

    # How to handle arbitrary iterables?
    # Skip string, check for mapping and iterable? Then need to know what type to use.
    # I think it's best to assume only tuples and frozendicts.
    gk = registry.get_key
    for r in registry.iter_recipes():
        to_replace = {}
        for f in dataclasses.fields(r):
            val = getattr(r, f.name)

            if isinstance(val, Recipe):
                to_replace[f.name] = gk(recipe)

            elif isinstance(val, tuple) and any(isinstance(x, Recipe) for x in val):
                to_replace[f.name] = tuple(gk(x, x) for x in val)

            elif isinstance(val, frozendict) and any(
                isinstance(x, Recipe) for x in _flat(val.items())
            ):
                to_replace[f.name] = frozendict(
                    (gk(k, k), gk(v, v)) for k, v in val.items()
                )
        to_serialize = dataclasses.asdict(r)
        to_serialize.update(to_replace)
        asdf
