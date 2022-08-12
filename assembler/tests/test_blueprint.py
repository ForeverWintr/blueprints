from __future__ import annotations
import typing as tp

import pytest


from assembler.recipes import Recipe
from assembler.factory import Factory, FrameFactoryMP
from assembler.blueprint import Blueprint, get_blueprint_layout, make_dependency_graph
from assembler.constants import NodeAttrs, BuildStatus
from assembler import exceptions
from assembler.tests.conftest import TestData, TestColumn, TABLES, MultiColumn


class Node(Recipe):
    """A simple recipe used for making graphs"""

    name: str
    dependencies: tuple[Node]

    def get_dependency_recipes(self) -> tuple[Node]:
        return self.dependencies

    def extract_from_dependency(self, *args) -> tp.Any:
        pass

    def __repr__(self):
        return f"{(type(self).__name__)}({self.name!r}, {self.dependencies})"

    def __str__(self):
        return self.name


def test_from_recipes():
    r1 = TestColumn(table_name="A", key=1)
    r2 = TestColumn(table_name="b", key=4)
    r3 = TestColumn(table_name="A", key=2)

    b = Blueprint.from_recipes((r1, r2, r3))

    dep = TestData(table_name="A")
    nodes = b._dependency_graph.nodes(data=True)

    assert set(b._dependency_graph[dep]) == {r1, r3}
    assert nodes[dep] == {
        NodeAttrs.output: False,
        NodeAttrs.build_status: BuildStatus.NOT_STARTED,
    }

    assert set(b._dependency_graph[TestData(table_name="b")]) == {r2}
    assert nodes[r1] == {
        NodeAttrs.output: True,
        NodeAttrs.build_status: BuildStatus.NOT_STARTED,
    }


def test_from_recipes_no_cycles() -> None:
    # Make sure that the build graph fails if a recipe tries to introduce cycles.
    class Bad(Recipe):
        name: str
        target: str

        def identity_key(self) -> tuple[tuple, ...]:
            return (
                ("name", self.name),
                ("target", self.target),
            )

        def get_dependency_recipes(self) -> tuple[Bad]:
            return (Bad(name=self.target, target=self.name),)

        def extract_from_dependency(self, *args) -> tp.Any:
            pass

        def __repr__(self):
            return f"{(type(self).__name__)}({self.name!r}, {self.target})"

    with pytest.raises(exceptions.ConfigurationError) as e:
        Blueprint.from_recipes([Bad(name="a", target="b")])

        assert e.match("The given recipe produced dependency cycles")


def test_get_blueprint_layout():
    a = Node(name="a", dependencies=())
    d = Node(name="d", dependencies=())
    b = Node(name="b", dependencies=(a,))
    c = Node(name="c", dependencies=(a, d))

    g = make_dependency_graph([b, c])
    layout = get_blueprint_layout(g)
    assert layout == {b: (0, 0), c: (1, 0), a: (0, 1), d: (1, 1)}


def test_visualize():
    # Slow import.
    from matplotlib import pyplot as plt

    a = Node(name="a", dependencies=())
    d = Node(name="d", dependencies=())
    b = Node(name="b", dependencies=(a,))
    c = Node(name="c", dependencies=(a, d))

    b = Blueprint.from_recipes([b, c])

    fig = plt.Figure()
    ax = fig.subplots()

    b.draw(ax)
    fig.savefig("/tmp/tmp.png", bbox_inches="tight")
    raise NotImplementedError("WIP")  # TODO REMOVE
