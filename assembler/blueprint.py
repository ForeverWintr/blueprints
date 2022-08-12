from __future__ import annotations
import typing as tp

import networkx as nx
import numpy as np

from assembler.recipes import Recipe
from assembler import exceptions
from assembler import util
from assembler.constants import NodeAttrs, BuildStatus, BUILD_STATUS_TO_COLOR

if tp.TYPE_CHECKING:
    from matplotlib import pyplot as plt


def get_blueprint_layout(
    g: nx.DiGraph, vertical_increment: float = 0.2, horizontal_increment: float = 0.1
) -> dict[Recipe, tuple[float, float]]:
    bottom_layer = {n for n, d in g.out_degree() if d == 0}
    x = 0
    positions = {}

    while bottom_layer:
        next_layer = set()
        y = 0
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
    to_process = list(outputs)
    processed = set()
    while to_process:
        r = to_process.pop()
        g.add_node(
            r,
            **{
                NodeAttrs.output: r in outputs,
                NodeAttrs.build_status: BuildStatus.NOT_STARTED,
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

    @classmethod
    def from_recipes(cls, recipes: tp.Iterable[Recipe]) -> Blueprint:
        """Create a blueprint from the given recipe."""
        g = make_dependency_graph(recipes)
        return cls(g)

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
