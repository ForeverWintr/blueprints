from __future__ import annotations
import typing as tp

import networkx as nx

from assembler.recipes import Recipe
from assembler import exceptions
from assembler import util
from assembler.constants import NodeAttrs, BuildStatus


def get_blueprint_layout(
    g: nx.DiGraph, vertical_increment: int = 2, horizontal_increment: int = 1
) -> dict[Recipe, tuple[int, int]]:
    bottom_layer = {n for n, d in g.out_degree() if d == 0}
    x = 0
    positions = {}

    while bottom_layer:
        next_layer = set()
        y = 0
        for node in bottom_layer:
            positions[node] = (y, x)
            y += vertical_increment
            for p in g.predecessors(node):
                next_layer.add(p)
        bottom_layer = next_layer
        x += horizontal_increment
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
        nx.draw(self._dependency_graph, pos=positions, ax=ax)
