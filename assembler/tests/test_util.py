import typing as tp
import dataclasses

import pytest
from frozendict import frozendict

from assembler import util
from assembler.recipes.base import Recipe, Dependencies, Parameters
from assembler.constants import BuildStatus
from assembler.tests.conftest import Node


def test_process_recipe_success() -> None:
    class Success(Recipe):
        def extract_from_dependencies(self, _) -> int:
            return 1

    r = Success()
    deps = Dependencies((), {}, {}, metadata=Parameters(factory_allow_missing=True))
    result = util.process_recipe(r, dependencies=deps)
    assert result.recipe == r
    assert result.status == BuildStatus.BUILT
    assert result.output == 1


def test_process_recipe_missing() -> None:
    class Missing(Recipe):
        missing_data_exceptions: tp.Type[Exception] = ZeroDivisionError
        allow_missing: bool = True

        def extract_from_dependencies(self, _) -> None:
            1 / 0

    r = Missing()
    deps = Dependencies((), {}, {}, metadata=Parameters(factory_allow_missing=True))
    result = util.process_recipe(r, dependencies=deps)
    assert result.recipe == r
    assert result.status == BuildStatus.MISSING
    assert result.output == util.MissingPlaceholder(
        reason="ZeroDivisionError('division by zero')", fill_value=None
    )


def test_process_recipe_raises() -> None:
    class Missing(Recipe):
        missing_data_exceptions: tp.Type[Exception] = ZeroDivisionError
        allow_missing: bool = False

        def extract_from_dependencies(self, _) -> None:
            1 / 0

    r = Missing()
    deps = Dependencies((), {}, {}, metadata=Parameters(factory_allow_missing=True))

    # This fails because the recipe has `allow_missing=False`.
    with pytest.raises(ZeroDivisionError):
        util.process_recipe(r, dependencies=deps)

    # This fails because the value of allow missing is overridden in the dependencies metadata.
    r2 = dataclasses.replace(r, allow_missing=True)
    deps2 = Dependencies((), {}, {}, metadata=Parameters(factory_allow_missing=False))
    with pytest.raises(ZeroDivisionError):
        util.process_recipe(r2, dependencies=deps2)


def test_make_immutable() -> None:
    assert util.make_immutable({1: 1}) == frozendict({1: 1})
    assert util.make_immutable([1, 1]) == (1, 1)

    assert util.make_immutable([1, [2]]) == (1, (2,))
    assert util.make_immutable({1: {1: 2}}) == frozendict({1: frozendict({1: 2})})

    assert util.make_immutable({1: [2, {3: 4, 5: []}, []], 2: {}}) == frozendict(
        {
            1: (2, frozendict({3: 4, 5: ()}), ()),
            2: frozendict({}),
        }
    )


def test_recipes_and_dependencies() -> None:
    d = Node(
        name="dep",
    )
    r = Node(name="r", dependencies=(d,))
    a = Node(name="a", dependencies=(r,))
    assert tuple(r for r, _ in util.recipes_and_dependencies([a])) == (a, r, d)
