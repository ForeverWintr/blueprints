from __future__ import annotations

import dataclasses
import functools
import itertools
import typing as tp
from abc import ABC
from abc import abstractmethod

from frozendict import frozendict

from blueprints import util
from blueprints.constants import MissingDependencyBehavior


class Parameters(tp.NamedTuple):
    factory_allow_missing: bool


class DependencyRequest:
    def __init__(self, *args: Recipe | None, **kwargs: Recipe | None):
        """Returned from recipes' get_dependency_request method. Used to indicate which other
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
        args: tuple,
        kwargs: frozendict[Recipe, tp.Any],
        recipe_to_result: frozendict[Recipe, tp.Any],
        metadata: Parameters,
    ):
        """Holder for instantiated dependencies. Passed to recipes'
        extract_from_dependencies method."""
        self.recipe_to_result = recipe_to_result
        self.metadata = metadata
        self.args = args
        self.kwargs = kwargs

    @classmethod
    def from_request(
        cls,
        request: DependencyRequest,
        recipe_to_dependency: dict[Recipe | None, tp.Any],
        metadata: Parameters,
    ) -> Dependencies:
        recipe_to_result = frozendict(
            {r: recipe_to_dependency[r] for r in request.recipes()}
        )
        args = tuple(recipe_to_result[a] for a in request.args)
        kwargs = frozendict(
            (k, recipe_to_result[v]) for k, v in request.kwargs.items() if v is not None
        )

        return cls(
            args=args,
            kwargs=kwargs,
            recipe_to_result=recipe_to_result,
            metadata=metadata,
        )


class _RecipeTypeRegistry:
    def __init__(self):
        """Internal cache for tracking recipe subclasses. Intended to be instantiated
        once globally. Used for serialization and deserialization."""
        self._registry = {}

    @staticmethod
    def key(recipe: tp.Type[Recipe]) -> tuple[str, str]:
        return (recipe.__module__, recipe.__qualname__)

    def add(self, recipe: tp.Type[Recipe]) -> None:
        """Add a new recipe to the registry, asserting that it is not already there"""
        key = self.key(recipe)
        assert key not in self._registry, f"{recipe!r} was defined twice!"
        self._registry[key] = recipe

    def get(self, key: tuple[str, str]) -> tp.Type[Recipe]:
        return self._registry[key]


RECIPE_TYPE_REGISTRY = _RecipeTypeRegistry()


@dataclasses.dataclass(frozen=True, repr=False, kw_only=True)
class Recipe(ABC):
    """Base class for recipes"""

    allow_missing: bool = False
    missing_data_exceptions: tp.Type[Exception] | tp.Tuple[tp.Type[Exception], ...] = ()

    ## Class level configuration
    on_missing_dependency: tp.ClassVar[MissingDependencyBehavior] = (
        MissingDependencyBehavior.SKIP
    )

    def get_dependency_request(self) -> DependencyRequest:
        """Return a DependencyRequest specifiying recipes that this recipe depends on."""
        return DependencyRequest()

    @abstractmethod
    def extract_from_dependencies(
        self,
        dependencies: Dependencies,
        requested_by: frozenset[Recipe, ...],
        config: frozendict[str, tp.Any],
    ) -> tp.Any:
        """Extract the data this recipe describes.

        Args:
            dependencies: a Dependencies object corresponding to the DependencyRequest
            returned by `get_dependency_request` above. Dependent recipes have been
            requested_by: The recipes that requested this recipe.
            config: A dictionary containing user defined configuration.
        """

    @classmethod
    def from_serializable_dict(cls, data: dict, key_to_recipe: dict) -> tp.Self:
        """Return an instance of this class, given a serializable dict as produced by
        cls.to_serializable_dict. All references to other recipes in the `data` received
        here have been replaced with entries into the provided `key_to_recipe` mapping.
        This method should look up the corresponding recipes there.

        for example, if your recipe is:

        class MyRecipe(Recipe):
            depends_on=other_recipe

        this method will receive a dictionary similar to

        data={'depends_on': 'RR_123412341234'}

        and should return

        cls(depends_on=key_to_recipe[data['depends_on']])
        """
        is_match_action = (
            (
                functools.partial(util.item_in_dict_and_hashable, d=key_to_recipe),
                lambda r: key_to_recipe[r],
            ),
            (util.is_callable_key, util.callable_from_key),
        )
        type_replace = {list: tuple, dict: frozendict}

        result = {}
        for f in dataclasses.fields(cls):
            val = data[f.name]
            for is_match, action in is_match_action:
                val = util.replace(
                    val,
                    is_match=is_match,
                    get_replacement=action,
                    type_replace=type_replace,
                )
            result[f.name] = val

        return cls(**result)

    def to_serializable_dict(self, recipe_to_key: frozendict) -> dict:
        """Return a dictionary that can be serialized (e.g. with json). To do this,
        convert any complex types types that are json serializable (e.g.
        strings/ints/tuples), and replace any recipes with their keys in the provided
        `recipe_to_key` (which should already contain all recipes that this recipe depends
        on). This method handles known subclasses but can be overridden to enable
        serialization of custom attributes.

        For example, if your recipe is:

        class MyRecipe(Recipe):
            depends_on=other_recipe

        This method would return

        {'depends_on': recipe_to_key[self.depends_on]}
        """
        is_match_action = (
            (lambda item: isinstance(item, Recipe), lambda r: recipe_to_key[r]),
            (lambda item: isinstance(item, tp.Callable), util.get_callable_key),
        )

        result = {}
        for f in dataclasses.fields(self):
            val = getattr(self, f.name)
            for is_match, action in is_match_action:
                val = util.replace(
                    val,
                    is_match=is_match,
                    get_replacement=action,
                )
            result[f.name] = val

        return result

    def short_name(self) -> str:
        """Return a short string representing this recipe."""
        return type(self).__name__

    ### Below this line, methods are internal and not intended to be overriden.

    def __init_subclass__(cls, **kwargs) -> None:
        # Automatically make other recipes dataclasses.
        r = dataclasses.dataclass(cls, frozen=True, repr=False, kw_only=True)  # type: ignore

        # Assert that this only added attributes, rather than creating a new class.
        assert r is cls

        # Add to the global registry of recipe classes.
        RECIPE_TYPE_REGISTRY.add(r)

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
