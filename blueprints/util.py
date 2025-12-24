from __future__ import annotations

import importlib
import sys
import typing as tp

import networkx as nx

from blueprints import constants
from blueprints import exceptions
from blueprints.constants import BuildState

if tp.TYPE_CHECKING:
    from frozendict import frozendict

    from blueprints.recipes.base import Dependencies
    from blueprints.recipes.base import DependencyRequest
    from blueprints.recipes.base import Recipe


class MissingPlaceholder(tp.NamedTuple):
    reason: str
    fill_value: tp.Any


class ProcessResult(tp.NamedTuple):
    recipe: Recipe
    status: BuildState
    output: tp.Any


def process_recipe(
    recipe: Recipe, dependencies: Dependencies, shared_state: frozendict
) -> ProcessResult:
    """Called in a child process, this utility function returns both the recipe and the result of
    its `extract_from_dependencies` method."""
    kw = {}
    if recipe.bind_shared_state:
        kw["shared_state"] = shared_state

    try:
        result = recipe.extract_from_dependencies(dependencies, **kw)
    except recipe.missing_data_exceptions as e:
        if not dependencies.metadata.factory_allow_missing or not recipe.allow_missing:
            raise
        else:
            result = MissingPlaceholder(
                reason=repr(e),
                fill_value=getattr(recipe, "missing_data_fill_value", None),
            )
            status = BuildState.MISSING
    else:
        status = BuildState.BUILT

    return ProcessResult(recipe=recipe, status=status, output=result)


def recipes_and_dependencies(
    recipes: tp.Iterable[Recipe],
) -> tp.Iterator[tuple[Recipe, DependencyRequest]]:
    """Yield pairs of Recipe, Dependencies for the given recipe and all recipes they
    depend on."""
    to_process: list[Recipe] = list(recipes)
    seen = set()
    while to_process:
        r = to_process.pop()
        depends_on = r.get_dependency_request()

        yield r, depends_on

        for d in depends_on.recipes():
            if d not in seen:
                to_process.append(d)
                seen.add(d)
        seen.add(r)


def flatten(items: tp.ItemsView) -> tp.Iterator:
    return (x for item in items for x in item)


def make_dependency_graph(recipes: tp.Iterable[Recipe]) -> nx.DiGraph:
    g = nx.DiGraph()
    outputs = set(recipes)
    for r, depends_on in recipes_and_dependencies(outputs):
        g.add_node(r)
        for d in depends_on.recipes():
            g.add_edge(d, r)

    if nx.dag.has_cycle(g):
        cycles = nx.find_cycle(g)
        raise exceptions.ConfigurationError(
            f"The given recipe produced dependency cycles: {cycles}"
        )
    return g


def replace(
    item: tp.Any,
    is_match: tp.Callable[[tp.Any], bool],
    get_replacement: tp.Callable[[tp.Any], tp.Any],
    type_replace: dict[tp.Type, tp.Type] | None = None,
) -> tp.Any:
    """Look for entries where `is_match` returns true, and replace them with the output
    of `get_replacement`.

    - If item is a match, the result of `get_replacement` is returned.

    - If item is an iterable or mapping and contains entries for which `is_match`
    returns true, a copy is returned with all matches replaced by the result of
    `get_replacement`.

    - If neither of the above are true, the original item is returned"""
    type_replace = type_replace or {}
    if is_match(item):
        return get_replacement(item)
    if isinstance(item, (str, bytes)):
        # Assume we don't want to search within strings.
        return item

    original_type = type(item)
    constructor = type_replace.get(original_type, original_type)
    new_items = item
    changes = constructor is not original_type

    def recurse(x):
        nonlocal changes
        new = replace(
            x,
            is_match=is_match,
            get_replacement=get_replacement,
            type_replace=type_replace,
        )
        if new is not x:
            changes = True
        return new

    if items := getattr(item, "items", None):
        new_items = tuple((recurse(k), recurse(v)) for k, v in items())

    else:
        try:
            iterator = iter(item)
        except TypeError:
            pass
        else:
            new_items = tuple(recurse(x) for x in iterator)

    if changes:
        return constructor(new_items)
    return item


def item_in_dict_and_hashable(item: tp.Any, d: dict) -> bool:
    try:
        return item in d
    except TypeError:
        # e.g., unhashable item.
        return False


def get_callable_key(callable_: tp.Callable) -> tuple[str, str]:
    """Get a key used to represent the given callable. Used for serialization in conjunction with `callable_from_key`"""
    return (
        constants.CALLABLE_KEY_IDENTIFIER,
        callable_.__module__,
        callable_.__qualname__,
    )


def is_callable_key(item: tp.Any) -> bool:
    try:
        return item[0] == constants.CALLABLE_KEY_IDENTIFIER
    except (TypeError, IndexError, KeyError):
        return False


def callable_from_key(key: tuple[str, str]) -> tp.Callable:
    """Given a key identifying a callable, as returned by `get_callable_key`, locate and
    return the corresponding callable. This imports modules if they aren't already
    loaded."""
    _, module_name, function_qualname = key
    try:
        obj = sys.modules[module_name]
    except KeyError:
        # If this module isn't imported, try to import it. This adds it to sys.modules.
        obj = importlib.import_module(module_name)

    for name in function_qualname.split("."):
        obj = getattr(obj, name)
    return obj
