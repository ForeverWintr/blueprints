from __future__ import annotations
import typing as tp
import json
import dataclasses

from frozendict import frozendict
import networkx as nx

from assembler import util

from assembler.recipes.base import Recipe, RECIPE_TYPE_REGISTRY


class RecipeRegistry:
    KEY_PREFIX = "RR"

    def __init__(
        self,
        key_to_recipe: dict[str, Recipe],
        dependency_graph: nx.DiGraph,
    ):
        """Maps recipes to process-unique ids. For use in serializing."""
        self.dependency_graph = dependency_graph
        self._recipe_to_key = {}
        self._key_to_recipe = {}
        if key_to_recipe:
            self._key_to_recipe = key_to_recipe
            self._recipe_to_key = {r: k for k, r in key_to_recipe.items()}

    @classmethod
    def from_depencency_graph(cls, dependency_graph: nx.DiGraph) -> tp.Self:
        return cls(
            key_to_recipe={f"{cls.KEY_PREFIX}_{id(r)}": r for r in dependency_graph},
            dependency_graph=dependency_graph,
        )

    @classmethod
    def from_recipes(cls, recipes: tp.Iterable[Recipe]) -> tp.Self:
        dependency_graph = util.make_dependency_graph(recipes)
        return cls.from_depencency_graph(dependency_graph)

    @classmethod
    def from_serializable_dict(cls, data: dict) -> tp.Self:
        """Given a dict in the format produced by `to_serializable_dict`, create an
        instance of this class."""
        dependency_graph = nx.json_graph.adjacency_graph(data["dependency_graph"])
        instantiation_order = nx.dag.topological_sort(dependency_graph)
        asdf

    def recipes(self) -> tp.Iterator[Recipe]:
        yield from self._recipe_to_key

    def get(self, item: Recipe, default=None):
        return self._recipe_to_key.get(item, default)

    def replace_dependencies(self, graph: nx.DiGraph) -> nx.DiGraph:
        """Swap all nodes in the given graph of recipes for their keys in the registry"""
        r2k = self._recipe_to_key
        new = type(graph)()
        for n in graph.nodes():
            new.add_node(r2k[n])
        for a, b in graph.edges():
            new.add_edge(r2k[a], r2k[b])
        return new

    def to_serializable_dict(self) -> dict:
        """Convert the registry to a dict that can be serialized (e.g., with json)"""
        # Make recipes serializable.
        recipes = {}
        for r in self.recipes():
            recipe_data = {
                "attributes": r.to_serializable_dict(self),
                "type": RECIPE_TYPE_REGISTRY.key(type(r)),
            }
            recipes[self.get(r)] = recipe_data

        # Make the dependency graph serializable.
        result = {
            "dependency_graph": nx.json_graph.adjacency_data(
                self.replace_dependencies(self.dependency_graph)
            ),
            "recipe_data": recipes,
        }
        return result


class ImmutableJsonDecoder(json.JSONDecoder):
    """Subclass of JSONDecoder that replaces lists with tuples and dicts with
    frozendicts."""

    @classmethod
    def _make_immutable(cls, obj: list | dict) -> tuple | frozendict:
        """Recurse through an arbitrarily nested structure of dicts and lists, and replace
        them with frozendicts and tuples. Intended to be called on the result of
        json.decode, so assumes no cycles and immutable keys."""
        constructor = frozendict
        try:
            items = obj.items()
        except AttributeError:
            items = enumerate(obj)
            constructor = tuple

        for k, v in items:
            if isinstance(v, (list, dict)):
                obj[k] = cls._make_immutable(v)
        return constructor(obj)

    def decode(self, string: str):
        obj = super().decode(string)
        return self._make_immutable(obj)


def recipe_to_json(recipe: Recipe) -> str:
    """Convert to a json representation that does not duplicate recipes. A recipe's
    dependencies are replaced with IDs into a registry mapping."""
    registry = RecipeRegistry.from_recipes([recipe])
    data = registry.to_serializable_dict()
    return json.dumps(data)


def recipe_from_json(json_str: str) -> Recipe:
    """Deserialize Json-ified recipes"""
    data = json.loads(json_str)  # , cls=ImmutableJsonDecoder)

    # Loaded dict needs to replace dependencies with recipes. It does not know what
    # fields contain recipes though. That means calling Recipe.from_serializable_dict
    # and passing a registry. How to build the registry? Can't call until all a
    # recipes dependencies are in the registry. Need to process in order. But don't know
    # what fields indicate deps.

    # Regristry contains a dependency graph.
    registry = RecipeRegistry.from_serializable_dict(data)
    asdf
