from __future__ import annotations
import typing as tp
from collections import defaultdict

import pytest

from assembler.recipes import Recipe
from assembler.factory import FrameFactory, FrameFactoryMP
from assembler import exceptions
from assembler.tests.conftest import TestData, TestColumn, TABLES, MultiColumn


def test_build_graph_no_cycles() -> None:
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
        FrameFactory()._build_graph([Bad(name="a", target="b")])

        assert e.match("The given recipe produced dependency cycles")


def test_build_recipe() -> None:
    factory = FrameFactory()
    result = factory.process_recipe(TestColumn(table_name="A", key=1))
    assert result == TABLES["A"][1]


def test_extract_from_dependency():
    recipe = TestData(table_name="A")
    assert recipe.extract_from_dependency() == TABLES["A"]


def test_build_graph():
    r1 = TestColumn(table_name="A", key=1)
    r2 = TestColumn(table_name="b", key=4)
    r3 = TestColumn(table_name="A", key=2)

    g = FrameFactory()._build_graph((r1, r2, r3))

    assert set(g[TestData(table_name="A")]) == {r1, r3}
    assert set(g[TestData(table_name="b")]) == {r2}


def test_multiprocess_graph():
    r1 = TestColumn(table_name="A", key=1)
    r2 = TestColumn(table_name="b", key=3)
    r3 = TestColumn(table_name="A", key=2)
    ff = FrameFactoryMP()
    r = ff.process_recipes((r1, r2, r3))

    assert r[r1] == 1
    assert r[r2] == 3
    assert r[r3] == 2


def test_dependency_order():
    # Dependency order should be guaranteed.

    r = MultiColumn(
        columns=(
            TestColumn(table_name="A", key=1),
            TestColumn(table_name="A", key=1),
            TestColumn(table_name="b", key=4),
            TestColumn(table_name="A", key=2),
            TestColumn(table_name="A", key=1),
        )
    )

    assert FrameFactory().process_recipe(r) == (1, 1, 4, 2, 1)


def test_mp_timeout():

    assert 0


def test_mp_error():

    assert 0


def test_get_buildable_recipes():

    assert 0
