import typing as tp

import typing as tp

import networkx as nx

from frame_factory.recipes import Recipe
from frame_factory import exceptions


class FrameFactory:
    def _build_graph(self, recipes: tp.Iterable[Recipe]) -> nx.DiGraph:
        """Create a dependency graph from the given recipe. The dependeny graph is a directed
        graph, where edges point from dependencies to the recipes that depend on them."""
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
        return g

    def data_from_recipe(self, recipe: Recipe) -> tp.Any:
        """Construct the given recipe, and return whatever it returns."""
        graph = self._build_graph([recipe])

        instantiated = {}
        for intermediate_recipe in nx.topological_sort(graph):

            # The topological_sort guarantees that the dependencies of this intermediate_recipe
            # were seen first.
            dependencies = {d: instantiated[d] for d in graph.predecessors(intermediate_recipe)}
            data = intermediate_recipe.extract_from_dependency(*dependencies.values())
            instantiated[intermediate_recipe] = data
        return instantiated[recipe]
