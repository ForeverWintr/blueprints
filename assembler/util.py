from __future__ import annotations

import typing as tp
import json
import frozendict

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


def flatten_recipe(recipe: Recipe) -> set[Recipe]:
    """Return a set containing this recipe and all of its dependencies"""
    result = {recipe}
    result.update(r for r in recipe.get_dependencies().recipes())
    return result


def flatten_recipes(recipes: tp.Iterable[Recipe]) -> set[Recipe]:
    return {r for root in recipes for r in flatten_recipe(root)}


def recipe_registry(recipes: tp.Iterable[Recipe]) -> dict[int, Recipe]:
    """Return a dictionary mapping recipe ids to recipes, for the provided recipes and
    all of their dependencies. For use in serialization"""
    return {id(r): r for r in flatten_recipes(recipes)}


def _wrap_parse(
    parse_method: tp.Callable, type_replacement: tp.Callable
) -> tuple | frozendict:
    def wrapper(*args, **kwargs):
        obj, end = parse_method(*args, **kwargs)
        return type_replacement(obj), end

    return wrapper


class ImmutableJson(json.JSONDecoder):
    """Subclass of JSONDecoder that replaces lists with tuples and dicts with
    frozendicts."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parse_array = _wrap_parse(json.decoder.JSONArray, tuple)
        self.parse_object = _wrap_parse(json.decoder.JSONObject, frozendict)

    def parse_array(self):
        asdf
