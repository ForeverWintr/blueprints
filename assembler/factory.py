import typing as tp
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
import os

import networkx as nx

from assembler.recipes import Recipe
from assembler import util
from assembler.blueprint import Blueprint


class Factory:
    def _process_graph(self, recipe_graph: nx.DiGraph) -> dict[Recipe, tp.Any]:
        """Return a dictionary mapping recipe for data for all recipes in `recipe_graph`"""
        instantiated: dict[Recipe, tp.Any] = {}
        for intermediate_recipe in nx.topological_sort(recipe_graph):

            # The topological_sort guarantees that the dependencies of this intermediate_recipe
            # were seen first.
            dependencies = [
                instantiated[d] for d in intermediate_recipe.get_dependency_recipes()
            ]
            data = intermediate_recipe.extract_from_dependency(*dependencies)
            instantiated[intermediate_recipe] = data
        return instantiated

    def process_recipes(self, recipes: tp.Iterable[Recipe]) -> dict[Recipe, tp.Any]:
        """Process the given recipes, returning a dictionary mapping each recipe to the data it
        specifies."""
        recipes = tuple(recipes)
        blueprint = Blueprint.from_recipes(recipes)
        all_data = self._process_graph(blueprint._dependency_graph)
        return {r: all_data[r] for r in recipes}

    def process_recipe(self, recipe: Recipe) -> tp.Any:
        """Construct the given recipe, and return whatever it returns."""
        return self.process_recipes([recipe])[recipe]


class FrameFactoryMP(Factory):
    def __init__(self, max_workers=None, timeout=60 * 5):
        self.max_workers = max_workers
        if max_workers is None:
            self.max_workers = os.cpu_count()
        self.timeout = timeout

    @staticmethod
    def _get_buildable_recipes(
        instantiated: dict[Recipe, tp.Any], recipe_graph: nx.DiGraph
    ) -> list[Recipe]:
        """Based on what is currently built, return recipes for which all dependencies are
        built."""
        buildable = []
        for built in instantiated:
            for successor in recipe_graph.successors(built):
                if successor not in instantiated and all(
                    dep in instantiated for dep in recipe_graph.predecessors(successor)
                ):
                    buildable.append(successor)
        return buildable

    def _process_graph(self, recipe_graph: nx.DiGraph) -> dict[Recipe, tp.Any]:

        # Initially, recipes with no ancestors are buildable.
        buildable = next(nx.topological_generations(recipe_graph))
        building = set()
        instantiated: dict[Recipe, tp.Any] = {}

        with ProcessPoolExecutor(
            max_workers=min(self.max_workers, len(recipe_graph))
        ) as executor:
            while True:
                building |= {
                    executor.submit(
                        util.process_recipe,
                        r,
                        tuple(instantiated[d] for d in r.get_dependency_recipes()),
                    )
                    for r in buildable
                }
                completed, building = wait(
                    building, timeout=self.timeout, return_when=FIRST_COMPLETED
                )

                # At least one recipe has completed. Add the results.
                for task in completed:
                    # If task failed, an exception is raised here.
                    recipe, data = task.result()
                    instantiated[recipe] = data

                if len(instantiated) == len(recipe_graph):
                    # Done
                    break

                # Check to see what else is now buildable.
                buildable = self._get_buildable_recipes(instantiated, recipe_graph)

        return instantiated
