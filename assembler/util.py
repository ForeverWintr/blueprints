import typing as tp

from frame_factory.recipes import Recipe


def process_recipe(recipe: Recipe, dependencies: tuple[tp.Any, ...]) -> tp.Any:
    return recipe, recipe.extract_from_dependency(*dependencies)
