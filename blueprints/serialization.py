from __future__ import annotations

import json
import typing as tp

import networkx as nx
from frozendict import frozendict

from blueprints import util
from blueprints.recipes.base import RECIPE_TYPE_REGISTRY, Recipe


class RecipeRegistry:
    KEY_PREFIX = "RR"

    def __init__(
        self,
        outputs: tuple[Recipe],
        key_to_recipe: frozendict[str, Recipe],
        dependency_graph: nx.DiGraph,
    ):
        """Maps recipes to process-unique ids. For use in serializing."""
        self.outputs = outputs
        self.dependency_graph = dependency_graph
        self.key_to_recipe = key_to_recipe
        self.recipe_to_key = frozendict((r, k) for k, r in key_to_recipe.items())

    @classmethod
    def from_depencency_graph(
        cls, dependency_graph: nx.DiGraph, outputs: tuple[Recipe]
    ) -> tp.Self:
        return cls(
            outputs=outputs,
            key_to_recipe={f"{cls.KEY_PREFIX}_{id(r)}": r for r in dependency_graph},
            dependency_graph=dependency_graph,
        )

    @classmethod
    def from_recipes(cls, recipes: tp.Iterable[Recipe]) -> tp.Self:
        recipes = tuple(recipes)
        dependency_graph = util.make_dependency_graph(recipes)
        return cls.from_depencency_graph(dependency_graph, outputs=recipes)

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
            outputs=tuple(key_to_recipe[k] for k in data["output_keys"]),
            key_to_recipe=frozendict(key_to_recipe),
            dependency_graph=cls._remap_nodes(dependency_graph, mapping=key_to_recipe),
        )

    @staticmethod
    def _remap_nodes(graph: nx.DiGraph, mapping: dict[tp.Any, tp.Any]) -> nx.DiGraph:
        """replace all nodes in the given graph with values from the given mapping."""
        new = type(graph)()
        for n in graph.nodes():
            new.add_node(mapping[n])
        for a, b in graph.edges():
            new.add_edge(mapping[a], mapping[b])
        return new

    def to_serializable_dict(self) -> dict:
        """Convert the registry to a dict that can be serialized (e.g., with json)"""
        # Make recipes serializable.
        recipes = {}
        for r in self.recipe_to_key:
            recipe_data = {
                "attributes": r.to_serializable_dict(self.recipe_to_key),
                "type": RECIPE_TYPE_REGISTRY.key(type(r)),
            }
            recipes[self.recipe_to_key[r]] = recipe_data

        # Make the dependency graph serializable.
        result = {
            "dependency_graph": nx.json_graph.adjacency_data(
                self._remap_nodes(self.dependency_graph, self.recipe_to_key)
            ),
            "recipe_data": recipes,
            "output_keys": tuple(self.recipe_to_key[o] for o in self.outputs),
        }
        return result


def recipes_to_json(recipes: tp.Iterable[Recipe]) -> str:
    """Convert to a json representation that does not duplicate recipes. A recipe's
    dependencies are replaced with IDs into a registry mapping."""
    registry = RecipeRegistry.from_recipes(recipes)
    return json.dumps(registry.to_serializable_dict())


def recipes_from_json(json_str: str) -> tuple[Recipe]:
    """Deserialize Json-ified recipes"""
    data = json.loads(json_str)
    registry = RecipeRegistry.from_serializable_dict(data)
    return registry.outputs
