import typing as tp
import dataclasses

import pytest

from assembler import util
from assembler.recipes.base import Recipe
from assembler.constants import BuildStatus


def test_process_recipe_success():
    class Success(Recipe):
        def extract_from_dependencies(self, _) -> int:
            return 1

    r = Success()
    result = util.process_recipe(r, allow_missing=True, dependencies=None)
    assert result.recipe == r
    assert result.status == BuildStatus.BUILT
    assert result.output == 1


def test_process_recipe_missing():
    class Missing(Recipe):
        missing_data_exceptions: tp.Type[Exception] = ZeroDivisionError
        allow_missing: bool = True

        def extract_from_dependencies(self, _) -> None:
            1 / 0

    r = Missing()
    result = util.process_recipe(r, allow_missing=True, dependencies=None)
    assert result.recipe == r
    assert result.status == BuildStatus.MISSING
    assert result.output == util.MissingPlaceholder(
        reason='division by zero', fill_value=None
    )


def test_process_recipe_raises():
    class Missing(Recipe):
        missing_data_exceptions: tp.Type[Exception] = ZeroDivisionError
        allow_missing: bool = False

        def extract_from_dependencies(self, _) -> None:
            1 / 0

    r = Missing()

    # This fails because the recipe has `allow_missing=False`.
    with pytest.raises(ZeroDivisionError):
        util.process_recipe(r, allow_missing=True, dependencies=None)

    # This fails because the value of allow missing is overridden in the call to process_recipe.
    r2 = dataclasses.replace(r, allow_missing=True)
    with pytest.raises(ZeroDivisionError):
        util.process_recipe(r2, allow_missing=False, dependencies=None)
