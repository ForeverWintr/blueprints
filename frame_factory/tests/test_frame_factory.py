from __future__ import annotations
import typing as tp
from collections import defaultdict

from frame_factory.recipes import Recipe
from frame_factory.factory import FrameFactory


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

    @classmethod
    def extract_from_dependency(
        cls, to_extract: tuple[Recipe], dependencies: dict[Recipe, tp.Any]
    ) -> dict[Recipe, tp.Any]:
        return {r: dict(TABLES[r.table_name]) for r in to_extract}


class TestColumn(Recipe):
    def __init__(self, table_name: str, key: int):
        self.table_name = table_name
        self.key = key

    def identity_key(self) -> tuple[str, str]:
        return (
            ("table_name", self.table_name),
            ("key", self.key),
        )

    @classmethod
    def group_by_dependency(
        cls, recipes: tuple[TestColumn]
    ) -> dict[tuple[Recipe] | None, tuple[Recipe]]:
        """This depends on a table"""
        result = defaultdict(list)
        for r in recipes:
            table = TestData(r.table_name)
            result[(table,)].append(r)
        return {k: tuple(recipes) for k, recipes in result.items()}


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

    result = TestColumn.group_by_dependency((r1, r2, r3))

    assert result == {(TestData("A"),): (r1, r3), (TestData("b"),): (r2,)}


def test_hash_eq():
    r1 = TestColumn("A", 1)
    r2 = TestColumn("A", 1)

    assert r1 == r2
    assert hash(r1) == hash(r2)


test_build_recipe()
test_group_by_dependency()
test_hash_eq()
test_extract_from_dependency()