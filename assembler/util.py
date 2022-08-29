import typing as tp

from assembler.recipes import Recipe


def process_recipe(recipe: Recipe, dependencies: tuple[tp.Any, ...]) -> tp.Any:
    return recipe, recipe.extract_from_dependencies(*dependencies)
