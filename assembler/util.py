import typing as tp

from assembler.recipes.base import Recipe, Dependencies
from assembler.constants import BuildStatus


class MissingPlaceholder(tp.NamedTuple):
    reason: str
    fill_value: tp.Any


class ProcessResult(tp.NamedTuple):
    recipe: Recipe
    status: BuildStatus
    result: tp.Any


def process_recipe(
    recipe: Recipe, allow_missing: bool, dependencies: Dependencies
) -> ProcessResult:
    """Called in a child process, this utility function returns both the recipe and the result of
    its `extract_from_dependencies` method."""

    try:
        result = recipe.extract_from_dependencies(dependencies)
    except recipe.missing_data_exceptions as e:
        if not allow_missing or not recipe.allow_missing:
            raise
        else:
            result = MissingPlaceholder(
                reason=str(e),
                fill_value=getattr(recipe, "missing_data_fill_value", None),
            )

    return ProcessResult(recipe=recipe, status=BuildStatus.BUILT, result=result)
