from __future__ import annotations
import typing as tp

from frame_factory.recipes import Recipe

#  Pretend these are tables
TABLES = {
    "A": {1: 1, 2: 2},
    "b": {3: 3, 4: 4},
}


class TestData(Recipe):
    table_name: str

    def extract_from_dependency(self) -> dict[Recipe, tp.Any]:
        return dict(TABLES[self.table_name])


class TestColumn(Recipe):
    table_name: str
    key: int = 1

    def get_dependency_recipes(self) -> tuple[Recipe]:
        """This depends on a table"""
        return (TestData(table_name=self.table_name),)

    def extract_from_dependency(self, table) -> tp.Any:
        return table[self.key]


class MultiColumn(Recipe):
    columns: tuple[TestColumn, ...]

    def get_dependency_recipes(self) -> tuple[Recipe]:
        """This depends on a table"""
        return self.columns

    def extract_from_dependency(self, *columns) -> tp.Any:
        return columns
