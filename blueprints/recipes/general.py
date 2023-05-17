import typing as tp

from frozendict import frozendict

from assembler.recipes.base import Recipe, Dependencies


class Object(Recipe):
    """A simple recipe that returns its payload. Useful for getting simple objects into
    a blueprint. Note that the payload must be hashable. For unhashable items, see
    FromFunction.
    """

    payload: tp.Hashable

    def extract_from_dependencies(self, dependencies: Dependencies) -> tp.Hashable:
        return self.payload


class FromFunction(Recipe):
    """A recipe that calls the given function with the given arguments."""

    function: tp.Callable
    args: tuple = ()
    kwargs: dict = frozendict()

    def __post_init__(self):
        # Make kwargs immutable.
        object.__setattr__(self, "kwargs", frozendict(self.kwargs))

    def extract_from_dependencies(self, dependencies: Dependencies) -> tp.Any:
        return self.function(*self.args, **self.kwargs)
