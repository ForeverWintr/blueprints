import typing as tp

from frozendict import frozendict

from assembler.recipes.base import Recipe, Dependencies


class FromFunction(Recipe):
    function: tp.Callable
    args: tuple
    kwargs: dict

    def __post_init__(self):
        # Make kwargs immutable.
        object.__setattr__(self, "kwargs", frozendict(self.kwargs))

    def extract_from_dependencies(self, dependencies: Dependencies) -> tp.Any:
        return self.function(*self.args, **self.kwargs)
