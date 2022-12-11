import typing as tp

from assembler.recipes.base import Recipe


class MissingPlaceholder(tp.NamedTuple):
    reason: str
    fill_value: tp.Any


def process_recipe(
    recipe: Recipe, allow_missing_override: bool, args, kwargs
) -> tuple[Recipe, tp.Any]:
    """Called in a child process, this utility function returns both the recipe and the result of
    its `extract_from_dependencies` method."""

    try:
        result = recipe.extract_from_dependencies(*args, **kwargs)
    except recipe.missing_data_exceptions as e:
        if not allow_missing_override or not recipe.allow_missing:
            raise
        else:
            result = MissingPlaceholder(
                reason=str(e),
                fill_value=getattr(recipe, "missing_data_fill_value", None),
            )

    return recipe, result
