from __future__ import annotations
import typing as tp

from frame_factory.recipes import Recipe

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

    def extract_from_dependency(self) -> dict[Recipe, tp.Any]:
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

    def extract_from_dependency(self, table) -> tp.Any:
        return table[self.key]
