from __future__ import annotations
import typing as tp
from collections import defaultdict

import pytest

from frame_factory.recipes import Recipe
from frame_factory.factory import FrameFactory
from frame_factory import exceptions
from frame_factory.tests.conftest import TestData, TestColumn, TABLES


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
    r2 = TestColumn(table_name="b", key=1)
    r3 = TestColumn(table_name="A", key=2)

    g = FrameFactory()._build_graph((r1, r2, r3))

    assert set(g[TestData(table_name="A")]) == {r1, r3}
    assert set(g[TestData(table_name="b")]) == {r2}
