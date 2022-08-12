from __future__ import annotations
import typing as tp

import networkx as nx

from assembler.recipes import Recipe
from assembler import exceptions
from assembler import util


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
        g = nx.DiGraph()
        to_process = list(recipes)
        processed = set()
        while to_process:
            r = to_process.pop()
            g.add_node(r)
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
        return cls(g)
