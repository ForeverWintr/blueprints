from __future__ import annotations

import typing as tp
import json
from frozendict import frozendict

from assembler.constants import BuildStatus

if tp.TYPE_CHECKING:
    from assembler.recipes.base import Recipe, Dependencies


class MissingPlaceholder(tp.NamedTuple):
    reason: str
    fill_value: tp.Any


class ProcessResult(tp.NamedTuple):
    recipe: Recipe
    status: BuildStatus
    output: tp.Any


def process_recipe(recipe: Recipe, dependencies: Dependencies) -> ProcessResult:
    """Called in a child process, this utility function returns both the recipe and the result of
    its `extract_from_dependencies` method."""

    try:
        result = recipe.extract_from_dependencies(dependencies)
    except recipe.missing_data_exceptions as e:
        if not dependencies.metadata.factory_allow_missing or not recipe.allow_missing:
            raise
        else:
            result = MissingPlaceholder(
                reason=repr(e),
                fill_value=getattr(recipe, "missing_data_fill_value", None),
            )
            status = BuildStatus.MISSING
    else:
        status = BuildStatus.BUILT

    return ProcessResult(recipe=recipe, status=status, output=result)


def recipes_and_dependencies(
    recipes: tp.Iterable[Recipe],
) -> tp.Iterator[tuple[Recipe, Dependencies]]:
    """Yield pairs of Recipe, Dependencies for the given recipe and all recipes they
    depend on."""
    to_process: list[Recipe] = list(recipes)
    seen = set()
    while to_process:
        r = to_process.pop()
        depends_on = r.get_dependencies()

        yield r, depends_on

        for d in depends_on.recipes():
            if d not in seen:
                to_process.append(d)
                seen.add(d)
        seen.add(r)


def recipe_registry(recipes: tp.Iterable[Recipe]) -> dict[int, Recipe]:
    """Return a dictionary mapping recipe ids to recipes, for the provided recipes and
    all of their dependencies. For use in serialization"""
    return {id(r): r for r in flatten_recipes(recipes)}


def make_immutable(obj: list | dict) -> tuple | frozendict:
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
            obj[k] = make_immutable(v)
    return constructor(obj)


class ImmutableJsonDecoder(json.JSONDecoder):
    """Subclass of JSONDecoder that replaces lists with tuples and dicts with
    frozendicts."""

    def decode(self, string: str):
        obj = super().decode(string)
        return make_immutable(obj)
