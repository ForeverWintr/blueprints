from __future__ import annotations

import pytest

from assembler.recipes import Recipe
from assembler.factory import Factory, FrameFactoryMP
from assembler.blueprint import Blueprint
from assembler.constants import NodeAttrs
from assembler import exceptions
from assembler.tests.conftest import TestData, TestColumn, TABLES, MultiColumn


def test_from_recipes():
    r1 = TestColumn(table_name="A", key=1)
    r2 = TestColumn(table_name="b", key=4)
    r3 = TestColumn(table_name="A", key=2)

    b = Blueprint.from_recipes((r1, r2, r3))

    dep = TestData(table_name="A")
    nodes = b._dependency_graph.nodes(data=True)

    assert set(b._dependency_graph[dep]) == {r1, r3}
    assert nodes[dep] == {NodeAttrs.output: False}

    assert set(b._dependency_graph[TestData(table_name="b")]) == {r2}
    assert nodes[r1] == {NodeAttrs.output: True}


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
            return f"{(type(self).__name__)}({self.name}, {self.target})"

    with pytest.raises(exceptions.ConfigurationError) as e:
        Blueprint.from_recipes([Bad(name="a", target="b")])

        assert e.match("The given recipe produced dependency cycles")
