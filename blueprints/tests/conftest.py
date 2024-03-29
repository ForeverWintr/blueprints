from __future__ import annotations
import typing as tp

from blueprints.recipes.base import Recipe, DependencyRequest, Dependencies
from blueprints import constants

#  Pretend these are tables
TABLES = {
    "A": {1: 1, 2: 2},
    "b": {3: 3, 4: 4},
}


### Recipes created for tests.
class TestData(Recipe):
    table_name: str

    def extract_from_dependencies(self, _: Dependencies) -> dict[int, int]:
        return dict(TABLES[self.table_name])


class TestColumn(Recipe):
    table_name: str
    key: int = 1

    def get_dependency_request(self) -> DependencyRequest:
        """This depends on a table"""
        return DependencyRequest(
            TestData(table_name=self.table_name),
        )

    def extract_from_dependencies(self, dependencies: Dependencies) -> tp.Any:
        table = dependencies.args[0]
        return table[self.key]


class MultiColumn(Recipe):
    columns: tuple[TestColumn, ...]

    def get_dependency_request(self) -> DependencyRequest:
        """This depends on a table"""
        return DependencyRequest(*self.columns)

    def extract_from_dependencies(self, dependencies: Dependencies) -> tp.Any:
        columns = tuple(dependencies.recipe_to_result[c] for c in self.columns)
        return columns


class BindMissing(MultiColumn):
    allow_missing: bool = True

    on_missing_dependency: tp.ClassVar[
        constants.MissingDependencyBehavior
    ] = constants.MissingDependencyBehavior.BIND


class Raiser(Recipe):
    """Recipe that raises an error, to test allow_missing"""

    allow_missing: bool = True
    missing_data_exceptions: tp.Type[Exception] = RuntimeError
    raise_in: str = "extract_from_dependencies"
    missing_data_fill_value = "fill_value"

    def get_dependency_request(self) -> DependencyRequest:
        if self.raise_in == "get_dependency_request":
            raise self.missing_data_exceptions()
        return DependencyRequest()

    def extract_from_dependencies(self, *columns) -> tp.Any:
        if self.raise_in == "extract_from_dependencies":
            raise self.missing_data_exceptions()
        return columns


class Node(Recipe):
    """A simple recipe used for making dependency graphs"""

    name: str
    dependencies: tuple[Node, ...] = ()

    def get_dependency_request(self) -> DependencyRequest:
        return DependencyRequest(*self.dependencies)

    def extract_from_dependencies(self, *args) -> tp.Any:
        pass

    def __repr__(self):
        return f"{(type(self).__name__)}({self.name!r})"

    def __str__(self):
        return self.name

    def short_name(self) -> str:
        return self.name
