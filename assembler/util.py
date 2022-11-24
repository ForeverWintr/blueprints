import typing as tp

from assembler.recipes.base import Recipe


def process_recipe(recipe: Recipe, *args, **kwargs) -> tuple[Recipe, tp.Any]:
    """Called in a child process, this utility function returns both the recipe and the result of
    its `extract_from_dependencies` method."""
    return recipe, recipe.extract_from_dependencies(*args, **kwargs)
