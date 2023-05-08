import typing as tp
import dataclasses

import pytest
from frozendict import frozendict
from functools import partial

from assembler import util
from assembler.recipes.base import Recipe, Dependencies, Parameters
from assembler.constants import BuildState, CALLABLE_KEY_IDENTIFIER
from assembler.tests.conftest import Node


def test_process_recipe_success() -> None:
    class Success(Recipe):
        def extract_from_dependencies(self, _) -> int:
            return 1

    r = Success()
    deps = Dependencies((), {}, {}, metadata=Parameters(factory_allow_missing=True))
    result = util.process_recipe(r, dependencies=deps)
    assert result.recipe == r
    assert result.status == BuildState.BUILT
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
    assert result.status == BuildState.MISSING
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


@pytest.mark.skip
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


def test_get_callable_key() -> None:
    k = util.get_callable_key(test_recipes_and_dependencies)
    assert k == (
        CALLABLE_KEY_IDENTIFIER,
        "assembler.tests.test_util",
        "test_recipes_and_dependencies",
    )


def test_callable_from_key() -> None:
    c = util.callable_from_key(
        (
            CALLABLE_KEY_IDENTIFIER,
            "assembler.tests.test_util",
            "test_recipes_and_dependencies",
        )
    )
    assert c is test_recipes_and_dependencies


def test_callable_from_key_module_not_loaded() -> None:
    c = util.callable_from_key(
        (
            CALLABLE_KEY_IDENTIFIER,
            "assembler.tests.unloaded_module_test",
            "func",
        )
    )
    assert c() == "imported"


class QualnameTest:
    def func():
        pass


def test_callable_from_key_qualname() -> None:
    c = util.callable_from_key(
        (CALLABLE_KEY_IDENTIFIER, "assembler.tests.test_util", "QualnameTest.func")
    )
    assert c is QualnameTest.func


_REPLACE_CASES = ""


def test_replace():
    replacer = partial(
        util.replace, is_match=lambda i: i == 5, get_replacement=lambda _: -1
    )

    assert replacer(5) == -1
    assert replacer([5]) == [-1]
    assert replacer([3, 5, 4]) == [3, -1, 4]
    assert replacer([3, [5], [4]]) == [3, [-1], [4]]
    assert replacer([3, {5}, [4]]) == [3, {-1}, [4]]
    assert replacer("5555") == "5555"

    a = [1, 2, 3]
    assert replacer(a) is a

    b = (1, 2, 3)
    assert replacer(b) is b

    c = ("a", "b", (1, 2, 3, 4, 5))
    assert replacer(c) == ("a", "b", (1, 2, 3, 4, -1))

    assert replacer({5: {2: {5: 5}}}) == {-1: {2: {-1: -1}}}
