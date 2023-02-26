from __future__ import annotations
import typing as tp
from abc import ABC, abstractmethod
import dataclasses
import itertools

from frozendict import frozendict

from assembler.constants import MissingDependencyBehavior


class Parameters(tp.NamedTuple):
    factory_allow_missing: bool


class DependencyRequest:
    def __init__(self, *args: Recipe | None, **kwargs: Recipe | None):
        """Returned from recipes' get_dependencies method. Used to indicate which other
        recipes a recipe depends on."""
        self.args: tuple = args
        self.kwargs: dict = kwargs

    def recipes(self) -> tp.Iterator[Recipe]:
        """Return an iterator over all recipes. If an arg or kwarg was specifically
        passed as None, it is skipped here."""
        for item in itertools.chain(self.args, self.kwargs.values()):
            if item is not None:
                yield item


class Dependencies:
    def __init__(
        self,
        request: DependencyRequest,
        recipe_to_result: dict[Recipe, tp.Any],
        metadata: Parameters,
    ):
        """Holder for instantiated dependencies. Passed to recipes'
        extract_from_dependencies method."""
        self.request = request
        self.recipe_to_result = recipe_to_result
        self.metadata = metadata

    @classmethod
    def from_request(
        cls,
        dependency_request: DependencyRequest,
        recipe_to_dependency: dict[Recipe | None, tp.Any],
        metadata: Parameters,
    ) -> Dependencies:

        relevant_deps = frozendict(
            {r: recipe_to_dependency[r] for r in dependency_request.recipes()}
        )

        return cls(
            request=dependency_request,
            recipe_to_result=relevant_deps,
            metadata=metadata,
        )

    def arg(self, arg: int) -> tp.Any:
        """Return the result for the requested positional arg."""
        return self.recipe_to_result[self.request.args[arg]]

    def kwarg(self, kwarg: str) -> tp.Any:
        """Return the result for the requested kwarg."""
        return self.recipe_to_result[self.request.kwargs[kwarg]]


@dataclasses.dataclass(frozen=True, repr=False, kw_only=True)
class Recipe(ABC):
    """Base class for recipes"""

    allow_missing: bool = False
    missing_data_exceptions: tp.Type[Exception] | tp.Tuple[tp.Type[Exception], ...] = ()

    ## Class level configuration
    on_missing_dependency: tp.ClassVar[
        MissingDependencyBehavior
    ] = MissingDependencyBehavior.SKIP

    def get_dependencies(self) -> DependencyRequest:
        """Return a DependencyRequest specifiying recipes that this recipe depends on."""
        return DependencyRequest()

    @abstractmethod
    def extract_from_dependencies(self, *args: tp.Any) -> tp.Any:
        """Given positional dependencies, extract the data that this recipe describes. args will be
        the results of instantiating the recipes returned by `get_dependencies` above"""

    ### Below this line, methods are internal and not intended to be overriden.

    def __init_subclass__(cls, **kwargs) -> None:
        # Automatically make other recipes dataclasses.
        r = dataclasses.dataclass(cls, frozen=True, repr=False, kw_only=True)  # type: ignore
        assert r is cls

    def _is_not_default(
        self, attribute: str, fields: tp.Dict[str, dataclasses.Field]
    ) -> bool:
        """
        Return true if the specified attribute is not its default
        """
        return (
            attribute in fields
            and getattr(self, attribute) is not fields[attribute].default
        )

    def pformat(self, indent="", indent_increase="    "):
        """Generate a multiline representation of this recipe, for easier visual inspection."""
        fields = {f.name: f for f in dataclasses.fields(self)}
        non_default = (
            (k, v) for k, v in fields.items() if self._is_not_default(k, fields)
        )
        to_display = {k: getattr(self, k) for k, _ in non_default}

        lines = [f"{indent}{self.__class__.__name__}("]
        next_indent = indent + indent_increase
        for name, value in to_display.items():
            # For now I assume the only iterable we need to worry about is tuples. This should be
            # enforced somewhere else in the recipe framework,
            if name != "label" and isinstance(value, tuple):
                lines.append(f"{next_indent}{name}=(")
                inner = next_indent + indent_increase
                for sub in value:
                    if isinstance(sub, Recipe):
                        lines.append(
                            f"{sub.pformat(indent=inner, indent_increase=indent_increase)},"
                        )
                    else:
                        lines.append(f"{inner}{sub!r},")
                lines.append(f"{next_indent}),")

            else:
                lines.append(f"{next_indent}{name}={value!r},")

        lines.append(f"{indent})")
        return "\n".join(lines)

    def __repr__(self):
        """Customize repr to only include fields that aren't the default value"""
        return self.pformat()
