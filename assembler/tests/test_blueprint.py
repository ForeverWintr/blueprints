from __future__ import annotations
import typing as tp

import pytest

from assembler.recipes.base import Recipe, DependencyRequest, Dependencies
from assembler.blueprint import (
    Blueprint,
    get_blueprint_layout,
    make_dependency_graph,
)
from assembler.constants import NodeAttrs, BuildStatus
from assembler import exceptions
from assembler.tests.conftest import TestData, TestColumn


@pytest.fixture
def nodes() -> dict[str, Node]:
    a = Node(name="a")
    d = Node(name="d")
    b = Node(name="b", dependencies=(a,))
    c = Node(name="c", dependencies=(a, d))
    return {
        "a": a,
        "d": d,
        "b": b,
        "c": c,
    }


@pytest.fixture
def basic_blueprint(nodes) -> Blueprint:
    return Blueprint.from_recipes([nodes["b"], nodes["c"]])


class Node(Recipe):
    """A simple recipe used for making graphs"""

    name: str
    dependencies: tuple[Node, ...] = ()

    def get_dependencies(self) -> DependencyRequest:
        return DependencyRequest(*self.dependencies)

    def extract_from_dependencies(self, *args) -> tp.Any:
        pass

    def __repr__(self):
        return f"{(type(self).__name__)}({self.name!r})"

    def __str__(self):
        return self.name


def test_from_recipes() -> None:
    r1 = TestColumn(table_name="A", key=1)
    r2 = TestColumn(table_name="b", key=4)
    r3 = TestColumn(table_name="A", key=2)

    b = Blueprint.from_recipes((r1, r2, r3))

    dep = TestData(table_name="A")
    nodes = b._dependency_graph.nodes(data=True)

    assert set(b._dependency_graph[dep]) == {r1, r3}
    node = nodes[dep]
    node.pop(NodeAttrs.dependency_request)
    assert node == {
        NodeAttrs.is_output: False,
        NodeAttrs.build_status: BuildStatus.BUILDABLE,
    }

    assert set(b._dependency_graph[TestData(table_name="b")]) == {r2}
    node = nodes[r1]
    node.pop(NodeAttrs.dependency_request)
    assert nodes[r1] == {
        NodeAttrs.is_output: True,
        NodeAttrs.build_status: BuildStatus.NOT_STARTED,
    }


def test_from_recipes_no_cycles() -> None:
    # Make sure that the build graph fails if a recipe tries to introduce cycles.
    class Bad(Recipe):
        name: str
        target: str

        def get_dependencies(self) -> DependencyRequest:
            return DependencyRequest(Bad(name=self.target, target=self.name))

        def extract_from_dependencies(self, *args) -> tp.Any:
            pass

        def __repr__(self):
            return f"{(type(self).__name__)}({self.name!r}, {self.target})"

    with pytest.raises(exceptions.ConfigurationError) as e:
        Blueprint.from_recipes([Bad(name="a", target="b")])

        assert e.match("The given recipe produced dependency cycles")


def test_get_blueprint_layout() -> None:
    a = Node(name="a")
    d = Node(name="d")
    b = Node(name="b", dependencies=(a,))
    c = Node(name="c", dependencies=(a, d))

    g = make_dependency_graph([b, c])
    layout = get_blueprint_layout(g)
    assert layout == {b: (0, 0), c: (0.1, 0), a: (0, 0.2), d: (0.1, 0.2)}


def test_set_build_state(basic_blueprint: Blueprint) -> None:
    node = next(iter(basic_blueprint._dependency_graph))

    assert basic_blueprint.get_build_state(node) is BuildStatus.NOT_STARTED
    basic_blueprint._set_build_state(node, BuildStatus.BUILDING)
    assert basic_blueprint.get_build_state(node) is BuildStatus.BUILDING


def test_mark_built(basic_blueprint: Blueprint) -> None:
    name_to_state = {
        r.name: basic_blueprint.get_build_state(r)
        for r in basic_blueprint._dependency_graph
    }
    assert name_to_state == {
        "b": BuildStatus.NOT_STARTED,
        "a": BuildStatus.BUILDABLE,
        "c": BuildStatus.NOT_STARTED,
        "d": BuildStatus.BUILDABLE,
    }

    basic_blueprint.mark_built(Node(name="a"))
    name_to_state = {
        r.name: basic_blueprint.get_build_state(r)
        for r in basic_blueprint._dependency_graph
    }
    assert name_to_state == {
        "b": BuildStatus.BUILDABLE,
        "a": BuildStatus.BUILT,
        "c": BuildStatus.NOT_STARTED,
        "d": BuildStatus.BUILDABLE,
    }


def test_mark_buildable(nodes: dict[str, Node], basic_blueprint: Blueprint) -> None:

    assert basic_blueprint._buildable == {nodes["a"], nodes["d"]}

    # This is a way of awkwardly re-constructing a re
    mark = nodes["c"]
    basic_blueprint.mark_buildable(mark)

    basic_blueprint.buildable_recipes() == {
        n for k, n in nodes.items() if n.name in {"a", "d", "c"}
    }
    for r in basic_blueprint.buildable_recipes():
        assert basic_blueprint.get_build_state(r) == BuildStatus.BUILDABLE


def test_buildable_recipes(basic_blueprint: Blueprint) -> None:
    #  If you use a _to_do copy, you have to iterate over it each time.
    #  If you keep a set of buildable recipes and update it each time one is finished, you only need to check neighbors.
    bldbl = tp.cast(frozenset[Node], basic_blueprint.buildable_recipes())
    assert {n.name for n in bldbl} == {"a", "d"}

    basic_blueprint.mark_built(Node(name="a"))

    bldbl2 = tp.cast(frozenset[Node], basic_blueprint.buildable_recipes())
    assert {n.name for n in bldbl2} == {"d", "b"}


def test_dependency_request():

    # Here I'm pretending integers are recipes.
    c = DependencyRequest(1, 2, 3, foo=5)
    assert tuple(c.recipes()) == (1, 2, 3, 5)

    recipe_to_dependency = {x: str(x) for x in (1, 2, 3, 5)}
    d = Dependencies.from_request(c, recipe_to_dependency, metadata=None)

    assert d.args == ("1", "2", "3")
    assert d.kwargs == {"foo": "5"}


def test_outputs(basic_blueprint):
    assert {n.name for n in basic_blueprint.outputs} == {"b", "c"}


def test_is_built(nodes: dict[str, Node], basic_blueprint: basic_blueprint):
    assert not basic_blueprint.is_built()

    # mark everything built or missing:
    for n in nodes.values():
        basic_blueprint.mark_built(n)
    assert basic_blueprint.is_built()

    basic_blueprint.mark_missing(nodes["a"], instantiated={})
    assert basic_blueprint.is_built()

    basic_blueprint.mark_buildable(nodes["b"])
    assert not basic_blueprint.is_built()


@pytest.mark.skip
def test_visualize() -> None:
    # Slow import.
    from matplotlib import pyplot as plt

    a = Node(name="a")
    d = Node(name="d")
    b = Node(name="b", dependencies=(a,))
    c = Node(name="c", dependencies=(a, d))

    bp = Blueprint.from_recipes([b, c])

    fig = plt.Figure()
    ax = fig.subplots()

    bp.draw(ax)
    fig.savefig("/tmp/tmp.png", bbox_inches="tight")
