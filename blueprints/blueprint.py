from __future__ import annotations

import json
import typing as tp

import networkx as nx

from blueprints import serialization, util
from blueprints.constants import (
    BUILD_STATE_TO_COLOR,
    BuildState,
    MissingDependencyBehavior,
)
from blueprints.recipes.base import Dependencies, Parameters, Recipe

if tp.TYPE_CHECKING:
    from matplotlib import pyplot as plt


def get_blueprint_layout(
    g: nx.DiGraph, vertical_increment: float = 0.2, horizontal_increment: float = 0.5
) -> dict[Recipe, tuple[float, float]]:
    """Return a dictionary from each recipe in the graph to it's x,y position"""
    bottom_layer = {n for n, d in g.out_degree() if d == 0}
    x = 0.0
    positions = {}

    while bottom_layer:
        next_layer = set()
        y = 0.0
        for node in sorted(bottom_layer, key=str):
            positions[node] = (y, x)
            y += horizontal_increment
            for p in g.predecessors(node):
                next_layer.add(p)
        bottom_layer = next_layer
        x += vertical_increment
    return positions


class Blueprint:
    def __init__(
        self,
        *,
        dependency_graph: nx.DiGraph,
        outputs: frozenset[Recipe],
        build_state: dict[Recipe, BuildState],
    ):
        """A Blueprint describes how to construct recipes and their depenencies.

        Args:
            dependency_graph: A directed graph, where edges point from dependencies to
            the recipes that depend on them.
        """
        self._dependency_graph = dependency_graph
        self.outputs = outputs
        self._build_state = build_state
        self._node_view: nx.reportviews.NodeDataView = dependency_graph.nodes(data=True)

        # Recipes that are not yet finished processing.
        self._unbuilt = {
            r
            for r in self._dependency_graph.nodes
            if self._build_state[r] not in {BuildState.BUILT, BuildState.MISSING}
        }

        # Recipes that are currently buildable.
        self._buildable: set = set()
        for r in {v for v, d in dependency_graph.in_degree() if d == 0}:
            self.mark_buildable(r)

        # Map of current number of unbuilt dependencies per recipe
        self._dependency_count = {
            v: d for v, d in dependency_graph.in_degree() if d > 0
        }

    @classmethod
    def from_recipes(cls, recipes: tp.Iterable[Recipe]) -> tp.Self:
        """Create a blueprint from the given recipe."""
        outputs = frozenset(recipes)
        g = util.make_dependency_graph(recipes)
        build_state = {}
        for recipe, data in g.nodes(data=True):
            build_state[recipe] = BuildState.NOT_STARTED
        return cls(
            dependency_graph=g,
            outputs=outputs,
            build_state=build_state,
        )

    @classmethod
    def from_serializable_dict(cls, data: dict) -> tp.Self:
        """Instantiate a blueprint from a serializable dict, as is returned by `to_serializable_dict`"""
        registry = serialization.RecipeRegistry.from_serializable_dict(
            data["recipe_registry"]
        )
        build_state = {
            registry.key_to_recipe[k]: BuildState(v)
            for k, v in data["build_state"].items()
        }
        return cls(
            dependency_graph=registry.dependency_graph,
            outputs=frozenset(registry.outputs),
            build_state=build_state,
        )

    @classmethod
    def from_json(cls, json_str: str) -> tp.Self:
        """Instantiate a blueprint from json. See `to_json`"""
        return cls.from_serializable_dict(json.loads(json_str))

    def get_build_state(self, recipe: Recipe) -> BuildState:
        """Return the build state of the given recipe"""
        return self._build_state[recipe]

    def prepare_to_build(
        self, recipe: Recipe, instantiated: dict[Recipe, tp.Any], metadata: Parameters
    ) -> Dependencies:
        """Prepare to build the given recipe. Find its dependencies in the given
        `instantiated` dict and return a `Dependencies` object that can be passed to the
        recipe. Mark the recipe as `BUILDING`."""
        dependencies = Dependencies.from_request(
            recipe.get_dependency_request(),
            instantiated,
            metadata=metadata,
        )
        self._build_state[recipe] = BuildState.BUILDING
        return dependencies

    def mark_buildable(self, recipe: Recipe) -> None:
        self._buildable.add(recipe)
        self._build_state[recipe] = BuildState.BUILDABLE

        # In practice the recipe should already be in this set, but for conceptual
        # consistency and testing, we add it again.
        self._unbuilt.add(recipe)

    def mark_built(self, recipe: Recipe) -> None:
        """Update the blueprint to reflect that the given node was built successfully"""
        self._build_state[recipe] = BuildState.BUILT
        self._buildable.discard(recipe)
        self._unbuilt.discard(recipe)

        # What new recipes are now buildable?
        for successor in self._dependency_graph.successors(recipe):
            if self.get_build_state(successor) is BuildState.NOT_STARTED:
                self._dependency_count[successor] -= 1
                if self._dependency_count[successor] == 0:
                    # This successor is now buildable.
                    self.mark_buildable(successor)

    def mark_missing(
        self, recipe: Recipe, instantiated: dict[Recipe, tp.Any]
    ) -> set[Recipe]:
        """If a recipe is missing, all its successors with
        MissingDependencyBehavior.SKIP and allow_missing=True are set to missing as
        well. Those same successors have their results set to missing in the
        `instantiated` dict.

        Return any recipes that cannot be built (i.e. they do not allow_missing) as a
        result of this.
        """
        self._build_state[recipe] = BuildState.MISSING
        self._buildable.discard(recipe)
        self._unbuilt.discard(recipe)

        # Update successors of this recipe depending on how they handle a missing
        # dependency.
        to_update = list(self._dependency_graph.successors(recipe))
        unbuildable = set()

        for successor in to_update:
            # It's possible this successor was already marked missing.
            if successor not in self._unbuilt:
                continue

            if successor.allow_missing:
                if successor.on_missing_dependency is MissingDependencyBehavior.SKIP:
                    # Mark this child recipe missing as well.
                    instantiated[successor] = instantiated[recipe]
                    # We must now update its successors too.
                    self.mark_missing(successor, instantiated)
                elif successor.on_missing_dependency is MissingDependencyBehavior.BIND:
                    # The successor is buildable. It will receive a missing placeholder.
                    self.mark_buildable(successor)
            else:
                unbuildable.add(successor)
        return unbuildable

    def update_result(
        self,
        result: util.ProcessResult,
        instantiated: dict[Recipe, tp.Any],
    ) -> set[Recipe]:
        """Update internal state based on the result of building a recipe."""
        instantiated[result.recipe] = result.output
        if result.status is BuildState.MISSING or isinstance(
            result.output, util.MissingPlaceholder
        ):
            # Mark all downstream recipes that skip missing as missing too. Return any that cannot be built.
            unbuildable = self.mark_missing(result.recipe, instantiated)
        elif result.status is BuildState.BUILT:
            self.mark_built(result.recipe)
            unbuildable = set()
        return unbuildable

    def buildable_recipes(self) -> frozenset[Recipe]:
        """Return recipes can be built (i.e., all of their dependencies were already built)"""
        return frozenset(self._buildable)

    def is_built(self) -> bool:
        """Return True if every recipe in the blueprint is built (or marked missing)."""
        return not self._unbuilt

    def draw(self, ax: plt.Axes) -> None:
        """Draw the blueprint on the given matplotlib ax object"""
        positions = get_blueprint_layout(self._dependency_graph)

        nodes = sorted(self._dependency_graph, key=str)
        labels = {n: n.short_name() for n in nodes}
        colors = [BUILD_STATE_TO_COLOR[self._build_state[n]] for n in nodes]

        nx.draw_networkx(
            self._dependency_graph,
            pos=positions,
            ax=ax,
            nodelist=nodes,
            labels=labels,
            node_color=colors,
        )

        # Preserve relative edge length
        ax.set_aspect("equal")

    def __len__(self):
        return len(self._dependency_graph)

    def to_serializable_dict(self) -> dict:
        """Return a dict represention of this object that can be json serialized"""
        registry = serialization.RecipeRegistry.from_depencency_graph(
            self._dependency_graph, outputs=tuple(self.outputs)
        )
        data = {
            "recipe_registry": registry.to_serializable_dict(),
            "build_state": {
                registry.recipe_to_key[r]: s.value for r, s in self._build_state.items()
            },
        }
        return data

    def to_json(self) -> str:
        """Serialize the blueprint to json"""
        return json.dumps(self.to_serializable_dict())
