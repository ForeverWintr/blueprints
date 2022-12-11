from __future__ import annotations
import typing as tp

from assembler.recipes.base import Recipe, Dependencies

#  Pretend these are tables
TABLES = {
    "A": {1: 1, 2: 2},
    "b": {3: 3, 4: 4},
}


class TestData(Recipe):
    table_name: str

    def extract_from_dependencies(self) -> dict[int, int]:
        return dict(TABLES[self.table_name])


class TestColumn(Recipe):
    table_name: str
    key: int = 1

    def get_dependencies(self) -> Dependencies:
        """This depends on a table"""
        return Dependencies(
            TestData(table_name=self.table_name),
        )

    def extract_from_dependencies(self, table) -> tp.Any:
        return table[self.key]


class MultiColumn(Recipe):
    columns: tuple[TestColumn, ...]

    def get_dependencies(self) -> Dependencies:
        """This depends on a table"""
        return Dependencies(*self.columns)

    def extract_from_dependencies(self, *columns) -> tp.Any:
        return columns


class Raiser(Recipe):
    """Recipe that raises an error, to test allow_missing"""

    allow_missing = True
    missing_data_exceptions: tp.Type[Exception] = RuntimeError
    raise_in: str = "extract_from_dependencies"
    missing_data_fill_value = "fill_value"

    def get_dependencies(self) -> Dependencies:
        if self.raise_in == "get_dependencies":
            raise self.missing_data_exceptions()
        return Dependencies()

    def extract_from_dependencies(self, *columns) -> tp.Any:
        if self.raise_in == "extract_from_dependencies":
            raise self.missing_data_exceptions()
        return columns
