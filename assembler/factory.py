import typing as tp
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED, Future
import os
import multiprocessing

import networkx as nx

from assembler.recipes.base import Recipe
from assembler import util
from assembler.blueprint import Blueprint
from assembler import exceptions


class Factory:
    def process_blueprint(self, blueprint: Blueprint) -> dict[Recipe, tp.Any]:
        instantiated: dict[Recipe, tp.Any] = {}

        while len(instantiated) < len(blueprint):
            buildable = blueprint.buildable_recipes()
            if not buildable:
                raise exceptions.AssemblerError(
                    "Blueprint is not built but returned no buildable recipes."
                )
            for b in buildable:
                args, kwargs = blueprint.get_args_kwargs(b, instantiated)
                result = b.extract_from_dependencies(*args, **kwargs)
                instantiated[b] = result
                blueprint.mark_built(b)

        return {r: instantiated[r] for r in blueprint.outputs}

    def process_recipes(self, recipes: tp.Iterable[Recipe]) -> dict[Recipe, tp.Any]:
        """Process the given recipes, returning a dictionary mapping each recipe to the data it
        specifies."""
        recipes = tuple(recipes)
        blueprint = Blueprint.from_recipes(recipes)
        all_data = self.process_blueprint(blueprint)
        return {r: all_data[r] for r in recipes}

    def process_recipe(self, recipe: Recipe) -> tp.Any:
        """Construct the given recipe, and return whatever it returns."""
        return self.process_recipes((recipe,))[recipe]


class FactoryMP(Factory):
    def __init__(self, max_workers=None, timeout=60 * 5, mp_context=None):
        """Basic multiprocessing of recipes using concurrent futures."""
        if max_workers is None:
            max_workers = os.cpu_count()
        self.max_workers = max_workers

        if mp_context is None:
            mp_context = multiprocessing.get_context("spawn")
        self.mp_context = mp_context

        self.timeout = timeout

    def process_blueprint(self, blueprint: Blueprint) -> dict[Recipe, tp.Any]:
        instantiated: dict[Recipe, tp.Any] = {}
        running_futures: set[Future] = set()
        building: set[Recipe] = set()

        with ProcessPoolExecutor(
            max_workers=min(self.max_workers, len(blueprint)),
            mp_context=self.mp_context,
        ) as executor:
            while len(instantiated) < len(blueprint):

                buildable = blueprint.buildable_recipes()
                if not buildable:
                    raise exceptions.AssemblerError(
                        "Blueprint is not built but returned no buildable recipes."
                    )

                # Remove recipes that are currently in progress from buildable.
                for b in buildable - building:
                    args, kwargs = blueprint.get_args_kwargs(b, instantiated)
                    future = executor.submit(util.process_recipe, b, *args, **kwargs)
                    running_futures.add(future)
                    building.add(b)

                completed, running_futures = wait(
                    running_futures, timeout=self.timeout, return_when=FIRST_COMPLETED
                )

                # At least one recipe has completed. Add the results.
                for task in completed:
                    # If task failed, an exception is raised here.
                    recipe, data = task.result()
                    blueprint.mark_built(recipe)
                    instantiated[recipe] = data
                    building.remove(recipe)

        return instantiated
