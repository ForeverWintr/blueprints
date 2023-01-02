from __future__ import annotations
import typing as tp

import networkx as nx

from assembler.recipes.base import Recipe, DependencyRequest, Dependencies, Parameters
from assembler import exceptions
from assembler.constants import (
    NodeAttrs,
    BuildStatus,
    BUILD_STATUS_TO_COLOR,
    MissingDependencyBehavior,
)
from assembler import util

if tp.TYPE_CHECKING:
    from matplotlib import pyplot as plt


def get_blueprint_layout(
    g: nx.DiGraph, vertical_increment: float = 0.2, horizontal_increment: float = 0.1
) -> dict[Recipe, tuple[float, float]]:
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


def make_dependency_graph(recipes: tp.Iterable[Recipe]) -> nx.DiGraph:
    g = nx.DiGraph()
    outputs = set(recipes)
    to_process: list[Recipe] = list(outputs)
    processed = set()
    while to_process:
        r = to_process.pop()
        depends_on = r.get_dependencies()
        g.add_node(
            r,
            **{
                NodeAttrs.output: r in outputs,
                NodeAttrs.build_status: BuildStatus.NOT_STARTED,
                NodeAttrs.dependency_request: depends_on,
            },
        )
        for d in depends_on.recipes():
            g.add_edge(d, r)

            if d not in processed:
                to_process.append(d)

        processed.add(r)

    if nx.dag.has_cycle(g):
        cycles = nx.find_cycle(g)
        raise exceptions.ConfigurationError(
            f"The given recipe produced dependency cycles: {cycles}"
        )
    return g


class Blueprint:
    def __init__(self, dependency_graph: nx.DiGraph, outputs: frozenset[Recipe]):
        """A Blueprint describes how to construct recipes and their depenencies.

        Args:
            dependency_graph: A directed graph, where edges point from dependencies to
            the recipes that depend on them.
        """
        self._dependency_graph = dependency_graph
        self.outputs = outputs

        # Recipes that are currently buildable.
        self._buildable: set = set()
        for r in {v for v, d in dependency_graph.in_degree() if d == 0}:
            self.mark_buildable(r)

        # Map of current number of unbuilt dependencies per recipe
        self._dependency_count = {
            v: d for v, d in dependency_graph.in_degree() if d > 0
        }

    @classmethod
    def from_recipes(cls, recipes: tp.Iterable[Recipe]) -> Blueprint:
        """Create a blueprint from the given recipe."""
        outputs = frozenset(recipes)
        g = make_dependency_graph(recipes)
        return cls(g, outputs=outputs)

    def get_build_state(self, recipe: Recipe) -> BuildStatus:
        """Return the build state of the given recipe"""
        return self._dependency_graph.nodes(data=True)[recipe][NodeAttrs.build_status]

    def get_dependency_request(self, recipe: Recipe) -> DependencyRequest:
        """Return the `DependencyRequest` object associated with the given recipe"""
        return self._dependency_graph.nodes(data=True)[recipe][
            NodeAttrs.dependency_request
        ]

    def prepare_to_build(
        self, recipe: Recipe, instantiated: dict[Recipe, tp.Any], metadata: Parameters
    ) -> Dependencies:
        """Prepare to build the given recipe. Find its dependencies in the given
        `instantiated` dict and return a `Dependencies` object that can be passed to the
        recipe. Mark the recipe as `BUILDING`."""
        request = self.get_dependency_request(recipe)
        dependencies = Dependencies.from_request(
            request,
            instantiated,
            metadata=metadata,
        )
        self._set_build_state(recipe, BuildStatus.BUILDING)
        return dependencies

    def _set_build_state(self, recipe: Recipe, state: BuildStatus) -> None:
        self._dependency_graph.nodes(data=True)[recipe][NodeAttrs.build_status] = state

    def mark_buildable(self, recipe: Recipe) -> None:
        self._buildable.add(recipe)
        self._set_build_state(recipe, BuildStatus.BUILDABLE)

    def mark_built(self, recipe: Recipe) -> None:
        """Update the blueprint to reflect that the given node was built successfully"""
        self._set_build_state(recipe, BuildStatus.BUILT)
        self._buildable.remove(recipe)

        # What new recipes are now buildable?
        for successor in self._dependency_graph.successors(recipe):
            if self.get_build_state(successor) is BuildStatus.NOT_STARTED:

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
        self._set_build_state(recipe, BuildStatus.MISSING)
        self._buildable.remove(recipe)

        unbuildable = set()
        for successor in self._dependency_graph.successors(recipe):
            if successor.allow_missing:
                if successor.on_missing_dependency is MissingDependencyBehavior.SKIP:
                    self._set_build_state(successor, BuildStatus.MISSING)
                    instantiated[successor] = instantiated[recipe]
                elif successor.on_missing_dependency is MissingDependencyBehavior.BIND:
                    breakpoint()
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
        if result.status is BuildStatus.BUILT:
            self.mark_built(result.recipe)
            unbuildable = set()
        elif result.status is BuildStatus.MISSING:
            # Mark all downstream recipes that skip missing as missing too. Return any that cannot be built.
            unbuildable = self.mark_missing(result.recipe, instantiated)
        return unbuildable

    def buildable_recipes(self) -> frozenset[Recipe]:
        """Return recipes can be built (i.e., all of their dependencies were already built)"""
        return frozenset(self._buildable)

    def draw(self, ax: plt.Axes) -> None:
        """Draw the blueprint on the given matplotlib ax object"""
        positions = get_blueprint_layout(self._dependency_graph)

        node_data = self._dependency_graph.nodes(data=True)
        nodes = sorted(self._dependency_graph, key=str)
        labels = {n: str(n) for n in nodes}
        colors = [
            BUILD_STATUS_TO_COLOR[node_data[n][NodeAttrs.build_status]] for n in nodes
        ]

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
