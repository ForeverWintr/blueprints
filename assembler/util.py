from __future__ import annotations

import typing as tp
import json
from frozendict import frozendict

from assembler.constants import BuildStatus

if tp.TYPE_CHECKING:
    from assembler.recipes.base import Recipe, Dependencies, DependencyRequest


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
) -> tp.Iterator[tuple[Recipe, DependencyRequest]]:
    """Yield pairs of Recipe, Dependencies for the given recipe and all recipes they
    depend on."""
    to_process: list[Recipe] = list(recipes)
    seen = set()
    while to_process:
        r = to_process.pop()
        depends_on = r.get_dependency_request()

        yield r, depends_on

        for d in depends_on.recipes():
            if d not in seen:
                to_process.append(d)
                seen.add(d)
        seen.add(r)
