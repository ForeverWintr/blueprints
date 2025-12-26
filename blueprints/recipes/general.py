import typing as tp

from frozendict import frozendict

from blueprints.recipes.base import Dependencies
from blueprints.recipes.base import Recipe


class Object(Recipe):
    """A simple recipe that returns its payload. Useful for getting simple objects into
    a blueprint. Note that the payload must be hashable. For unhashable items, see
    FromFunction.
    """

    payload: tp.Hashable

    def extract_from_dependencies(
        self,
        dependencies: Dependencies,
        requesting_recipes: tuple[Recipe, ...],
        config: frozendict[str, tp.Any],
    ) -> tp.Hashable:
        """Extract the data this recipe describes.

        Args:
            dependencies: a Dependencies object corresponding to the DependencyRequest
            returned by `get_dependency_request` above. Dependent recipes have been
            requesting_recipes: The recipes that requested this recipe.
            config: A dictionary containing user defined configuration.
        """
        return self.payload


class FromFunction(Recipe):
    """A recipe that calls the given function with the given arguments."""

    function: tp.Callable
    args: tuple = ()
    kwargs: dict = frozendict()

    def __post_init__(self):
        # Make kwargs immutable.
        object.__setattr__(self, "kwargs", frozendict(self.kwargs))

    def extract_from_dependencies(
        self,
        dependencies: Dependencies,
        requesting_recipes: tuple[Recipe, ...],
        config: frozendict[str, tp.Any],
    ) -> tp.Any:
        """Extract the data this recipe describes.

        Args:
            dependencies: a Dependencies object corresponding to the DependencyRequest
            returned by `get_dependency_request` above. Dependent recipes have been
            requesting_recipes: The recipes that requested this recipe.
            config: A dictionary containing user defined configuration.
        """
        return self.function(*self.args, **self.kwargs)
