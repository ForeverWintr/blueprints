from __future__ import annotations
import typing as tp

from assembler.recipes import Recipe, Call

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

    def get_dependencies(self) -> Call:
        """This depends on a table"""
        return Call(
            TestData(table_name=self.table_name),
        )

    def extract_from_dependencies(self, table) -> tp.Any:
        return table[self.key]


class MultiColumn(Recipe):
    columns: tuple[TestColumn, ...]

    def get_dependencies(self) -> tuple[TestColumn, ...]:
        """This depends on a table"""
        return Call(self.columns)

    def extract_from_dependencies(self, *columns) -> tp.Any:
        return columns
