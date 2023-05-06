from __future__ import annotations
import typing as tp
import json

from frozendict import frozendict
import networkx as nx

from assembler import util

from assembler.recipes.base import Recipe, RECIPE_TYPE_REGISTRY


class RecipeRegistry:
    KEY_PREFIX = "RR"

    def __init__(
        self,
        key_to_recipe: frozendict[str, Recipe],
        dependency_graph: nx.DiGraph,
    ):
        """Maps recipes to process-unique ids. For use in serializing."""
        self.dependency_graph = dependency_graph
        self.key_to_recipe = key_to_recipe
        self.recipe_to_key = frozendict((r, k) for k, r in key_to_recipe.items())

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
        recipe_data = data["recipe_data"]

        instantiation_order = nx.dag.topological_sort(dependency_graph)
        key_to_recipe = {}
        for recipe_id in instantiation_order:
            d = recipe_data[recipe_id]
            recipe_cls = RECIPE_TYPE_REGISTRY.get(tuple(d["type"]))
            recipe = recipe_cls.from_serializable_dict(
                d["attributes"],
                key_to_recipe=key_to_recipe,
            )
            key_to_recipe[recipe_id] = recipe

        return cls(
            key_to_recipe=frozendict(key_to_recipe),
            dependency_graph=dependency_graph,
        )

    def recipes(self) -> tp.Iterator[Recipe]:
        yield from self.recipe_to_key

    def get(self, item: Recipe, default=None):
        return self.recipe_to_key.get(item, default)

    def replace_dependencies(self, graph: nx.DiGraph) -> nx.DiGraph:
        """Swap all nodes in the given graph of recipes for their keys in the registry"""
        r2k = self.recipe_to_key
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
                "attributes": r.to_serializable_dict(self.recipe_to_key),
                "type": RECIPE_TYPE_REGISTRY.key(type(r)),
            }
            recipes[self.recipe_to_key[r]] = recipe_data

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


def recipes_to_json(recipes: tp.Iterable[Recipe]) -> str:
    """Convert to a json representation that does not duplicate recipes. A recipe's
    dependencies are replaced with IDs into a registry mapping."""
    registry = RecipeRegistry.from_recipes(recipes)
    data = registry.to_serializable_dict()
    data["outputs"] = tuple(registry.recipe_to_key[r] for r in recipes)
    return json.dumps(data)


def recipes_from_json(json_str: str) -> tuple[Recipe]:
    """Deserialize Json-ified recipes"""
    data = json.loads(json_str)  # , cls=ImmutableJsonDecoder)

    # Loaded dict needs to replace dependencies with recipes. It does not know what
    # fields contain recipes though. That means calling Recipe.from_serializable_dict
    # and passing a registry. How to build the registry? Can't call until all a
    # recipes dependencies are in the registry. Need to process in order. But don't know
    # what fields indicate deps.

    # Regristry contains a dependency graph.
    registry = RecipeRegistry.from_serializable_dict(data)
    return tuple(registry.key_to_recipe[k] for k in data["outputs"])
