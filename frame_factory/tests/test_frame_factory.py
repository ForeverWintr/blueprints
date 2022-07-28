from __future__ import annotations
import typing as tp
from collections import defaultdict

import pytest

from frame_factory.recipes import Recipe
from frame_factory.factory import FrameFactory
from frame_factory import exceptions


#  Pretend these are tables

TABLES = {
    "A": {1: 1, 2: 2},
    "b": {3: 3, 4: 4},
}


class TestData(Recipe):
    def __init__(self, table_name):
        """
        For testing. Pretend this is an expensive data source
        """
        self.table_name = table_name

    def identity_key(self) -> tuple[str, str]:
        return (("table_name", self.table_name),)

    def extract_from_dependency(self, dependencies: dict[Recipe, tp.Any]) -> dict[Recipe, tp.Any]:
        return dict(TABLES[self.table_name])


class TestColumn(Recipe):
    def __init__(self, table_name: str, key: int):
        self.table_name = table_name
        self.key = key

    def identity_key(self) -> tuple[str, str]:
        return (
            ("table_name", self.table_name),
            ("key", self.key),
        )

    def get_dependency_recipes(self) -> tuple[Recipe]:
        """This depends on a table"""
        return (TestData(self.table_name),)

    def extract_from_dependency(self, dependencies: tuple) -> tp.Any:
        return


def test_build_graph_no_cycles() -> None:
    # Make sure that the build graph fails if a recipe tries to introduce cycles.
    class Bad(Recipe):
        def __init__(self, name: str, target: str):
            self.name = name
            self.target = target

        def identity_key(self) -> tuple[tuple, ...]:
            return (
                ("name", self.name),
                ("target", self.target),
            )

        def get_dependency_recipes(self) -> tuple[Bad]:
            return (Bad(self.target, self.name),)

        def __repr__(self):
            return f"{(type(self).__name__)}({self.name}, {self.target})"

    with pytest.raises(exceptions.ConfigurationError) as e:
        FrameFactory()._build_graph(Bad("a", "b"))

        assert e.match("The given recipe produced dependency cycles")


def test_build_recipe() -> None:
    factory = FrameFactory()
    result = factory.build_recipe(TestColumn("A", 1))
    assert 0


def test_extract_from_dependency():
    recipe = TestData("A")
    assert recipe.extract_from_dependency((recipe,), dependencies={}) == {recipe: {1: 1, 2: 2}}


def test_group_by_dependency():
    r1 = TestColumn("A", 1)
    r2 = TestColumn("b", 1)
    r3 = TestColumn("A", 2)

    result = TestColumn.get_dependency_recipes((r1, r2, r3))

    assert result == {(TestData("A"),): (r1, r3), (TestData("b"),): (r2,)}


def test_hash_eq():
    r1 = TestColumn("A", 1)
    r2 = TestColumn("A", 1)

    assert r1 == r2
    assert hash(r1) == hash(r2)
