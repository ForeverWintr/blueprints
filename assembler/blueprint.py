from __future__ import annotations
import typing as tp

import networkx as nx

from assembler.recipes import Recipe
from assembler import exceptions
from assembler.constants import NodeAttrs, BuildStatus, BUILD_STATUS_TO_COLOR

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
        g.add_node(
            r,
            **{
                NodeAttrs.output: r in outputs,
                NodeAttrs.build_status: BuildStatus.NOT_STARTED,
                # NodeAttrs.call: ,
            },
        )
        for d in r.get_dependency_recipes():
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
    def __init__(self, dependency_graph: nx.DiGraph):
        """A Blueprint describes how to construct recipes and their depenencies.

        Args:
            dependency_graph: A directed graph, where edges point from dependencies to
            the recipes that depend on them.
        """
        self._dependency_graph = dependency_graph

        # Recipes that are currently buildable.
        self._buildable = {v for v, d in dependency_graph.in_degree() if d == 0}

        # Map of current number of unbuilt dependencies per recipe
        self._dependency_count = {v: d for v, d in dependency_graph.in_degree() if d > 0}

    @classmethod
    def from_recipes(cls, recipes: tp.Iterable[Recipe]) -> Blueprint:
        """Create a blueprint from the given recipe."""
        g = make_dependency_graph(recipes)
        return cls(g)

    def build_state(self, recipe: Recipe) -> BuildStatus:
        return self._dependency_graph.nodes(data=True)[recipe][NodeAttrs.build_status]

    def _set_build_state(self, recipe: Recipe, state: BuildStatus) -> None:
        self._dependency_graph.nodes(data=True)[recipe][NodeAttrs.build_status] = state

    def mark_built(self, recipe: Recipe) -> None:
        """Update the blueprint to reflect that the given node was built successfully"""
        self._set_build_state(recipe, BuildStatus.BUILT)
        self._buildable.remove(recipe)

        # What new recipes are now buildable?
        for successor in self._dependency_graph.successors(recipe):
            if self.build_state(successor) is BuildStatus.NOT_STARTED:

                self._dependency_count[successor] -= 1
                if self._dependency_count[successor] == 0:
                    # This successor is now buildable.
                    self._buildable.add(successor)

    def buildable_recipes(self) -> frozenset[Recipe]:
        """Return recipes can be built (i.e., all of their dependencies were already built)"""
        return frozenset(self._buildable)

    def draw(self, ax: plt.Axes) -> None:
        """Draw the blueprint on the given matplotlib ax object"""
        positions = get_blueprint_layout(self._dependency_graph)

        node_data = self._dependency_graph.nodes(data=True)
        nodes = sorted(self._dependency_graph, key=str)
        labels = {n: str(n) for n in nodes}
        colors = [BUILD_STATUS_TO_COLOR[node_data[n][NodeAttrs.build_status]] for n in nodes]

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
