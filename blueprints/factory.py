import multiprocessing
import os
import typing as tp
from concurrent.futures import FIRST_COMPLETED
from concurrent.futures import Future
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import wait

from frozendict import frozendict

from blueprints import exceptions
from blueprints import util
from blueprints.blueprint import Blueprint
from blueprints.recipes.base import Parameters
from blueprints.recipes.base import Recipe


class Factory:
    def __init__(
        self,
        allow_missing: bool = True,
        config: dict = frozendict(),
    ):
        """A factory controls the construction of recipes.

        Args:

            allow_missing: If False, individual recipes' allow_missing settings are ignored, and any missing data errors are raised. If both the factory and recipe have allow_missing set to true, missing data sentinels are returned instead.
            config: A dictionary that you can use for arbitrary configuration values.
            Recipes receive this in Recipe.extract_from_dependencies
        """
        self.allow_missing = allow_missing
        self.config = frozendict(config)

    @staticmethod
    def recipes_to_build(
        blueprint: Blueprint, building: tp.Optional[set[Recipe]] = None
    ) -> frozenset[Recipe]:
        buildable = blueprint.buildable_recipes()
        if not buildable and not blueprint.is_built():
            # This should not happen. If it does, it indicates an internal error in
            # the factory.
            raise exceptions.blueprintsError(
                "Blueprint is not built but returned no buildable recipes."
            )
        if building:
            buildable = buildable - building

        return buildable

    def process_blueprint(self, blueprint: Blueprint) -> dict[Recipe, tp.Any]:
        instantiated: dict[Recipe, tp.Any] = {}
        metadata = Parameters(factory_allow_missing=self.allow_missing)

        while len(instantiated) < len(blueprint):
            for recipe in self.recipes_to_build(blueprint):
                dependencies = blueprint.prepare_to_build(
                    recipe, instantiated, metadata=metadata
                )
                result = util.process_recipe(
                    recipe,
                    dependencies=dependencies,
                    config=self.config,
                    requesting_recipes=blueprint.successors(recipe),
                )

                unbuildable = blueprint.update_result(result, instantiated)
                if unbuildable:
                    raise exceptions.MissingDependencyError(
                        f"Unable to build {len(unbuildable)} recipes because {result.output.reason} from {recipe}"
                    )

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
    def __init__(
        self, allow_missing=True, max_workers=None, timeout=60 * 5, mp_context=None
    ):
        """Basic multiprocessing of recipes using concurrent futures."""
        super().__init__(allow_missing=allow_missing)

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
        metadata = Parameters(factory_allow_missing=self.allow_missing)

        with ProcessPoolExecutor(
            max_workers=min(self.max_workers, len(blueprint)),
            mp_context=self.mp_context,
        ) as executor:
            while len(instantiated) < len(blueprint):
                for recipe in self.recipes_to_build(blueprint, building=building):
                    dependencies = blueprint.prepare_to_build(
                        recipe, instantiated, metadata=metadata
                    )
                    future = executor.submit(
                        util.process_recipe,
                        recipe=recipe,
                        dependencies=dependencies,
                        config=self.config,
                    )
                    running_futures.add(future)
                    building.add(recipe)

                completed, running_futures = wait(
                    running_futures, timeout=self.timeout, return_when=FIRST_COMPLETED
                )

                # At least one recipe has completed. Add the results.
                for task in completed:
                    # If task failed, an exception is raised here.
                    result = task.result()
                    unbuildable = blueprint.update_result(result, instantiated)
                    if unbuildable:
                        # Cancel pending futures (those that haven't actually started
                        # running yet). This does not stop futures that are already
                        # running.
                        for f in running_futures:
                            f.cancel()
                        raise exceptions.MissingDependencyError(
                            f"Unable to build {len(unbuildable)} recipes because {result.output.reason} from {recipe}"
                        )
                    building.remove(result.recipe)

        return instantiated
