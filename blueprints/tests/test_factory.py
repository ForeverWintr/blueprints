from __future__ import annotations
import typing as tp

import functools

import pytest

from blueprints.factory import Factory, FactoryMP
from blueprints.tests.conftest import (
    TestData,
    TestColumn,
    TABLES,
    MultiColumn,
    Raiser,
    BindMissing,
)
from blueprints.blueprint import Blueprint
from blueprints import exceptions
from blueprints import util
from blueprints.recipes.general import Object

FACTORY_TYPES = (Factory, FactoryMP)


@pytest.mark.parametrize("factory_constructor", FACTORY_TYPES)
def test_process_recipe(factory_constructor) -> None:
    factory = factory_constructor()
    result = factory.process_recipe(TestColumn(table_name="A", key=1))
    assert result == TABLES["A"][1]


@pytest.mark.parametrize("factory_constructor", FACTORY_TYPES)
def test_process_recipes(factory_constructor):
    r1 = TestColumn(table_name="A", key=1)
    r2 = TestColumn(table_name="b", key=3)
    r3 = TestColumn(table_name="A", key=2)
    ff = factory_constructor()
    r = ff.process_recipes((r1, r2, r3))

    assert r[r1] == 1
    assert r[r2] == 3
    assert r[r3] == 2


@pytest.mark.parametrize("factory_constructor", FACTORY_TYPES)
def test_recipes_to_build(factory_constructor):
    r = TestData(table_name="A")
    r2 = TestData(table_name="b")
    b = Blueprint.from_recipes((r, r2))

    f = factory_constructor()
    assert f.recipes_to_build(b) == {r, r2}

    assert f.recipes_to_build(b, building={r}) == {r2}
    b.mark_built(r2)
    assert not f.recipes_to_build(b, building={r})


@pytest.mark.parametrize("factory_constructor", FACTORY_TYPES)
def test_recipes_to_build_error(factory_constructor):
    # A malformed blueprint that has no buildable recipes.
    b = Blueprint.from_recipes((TestColumn(table_name="A", key=1),))
    b._buildable = frozenset()

    f = factory_constructor()
    with pytest.raises(exceptions.blueprintsError):
        f.recipes_to_build(b)


@pytest.mark.parametrize("factory_constructor", FACTORY_TYPES)
def test_dependency_order(factory_constructor):
    # Dependency order is guaranteed.

    r = MultiColumn(
        columns=(
            TestColumn(table_name="A", key=1),
            TestColumn(table_name="A", key=1),
            TestColumn(table_name="b", key=4),
            TestColumn(table_name="A", key=2),
            TestColumn(table_name="A", key=1),
        )
    )

    # Buildable includes recipes that are currently building
    assert factory_constructor().process_recipe(r) == (1, 1, 4, 2, 1)


@pytest.mark.parametrize("factory_constructor", FACTORY_TYPES)
def test_allow_missing(factory_constructor):
    recipe = Raiser()
    with pytest.raises(RuntimeError):
        factory_constructor(allow_missing=False).process_recipe(recipe)

    f = factory_constructor(allow_missing=True)
    r = f.process_recipe(recipe)

    assert r == util.MissingPlaceholder(
        reason="RuntimeError()", fill_value="fill_value"
    )


@pytest.mark.parametrize("factory_constructor", FACTORY_TYPES)
def test_missing_skip(factory_constructor):
    # Downstream recipes that have allow_missing true and MissingDependencyBehavior.SKIP
    # are skipped when a dependency is missing.
    f = factory_constructor()
    will_be_skipped = MultiColumn(columns=(Raiser(),), allow_missing=True)
    will_be_skipped_also = MultiColumn(columns=(will_be_skipped,), allow_missing=True)

    manual_missing = Object(payload=util.MissingPlaceholder("test", "test"))
    dummy = Object(payload=5)
    will_be_skipped_too = MultiColumn(
        columns=(manual_missing, dummy), allow_missing=True
    )

    assert f.process_recipe(will_be_skipped_too) == manual_missing.payload
    assert f.process_recipe(will_be_skipped_also) == util.MissingPlaceholder(
        reason="RuntimeError()", fill_value="fill_value"
    )
    assert f.process_recipe(will_be_skipped) == util.MissingPlaceholder(
        reason="RuntimeError()", fill_value="fill_value"
    )


@pytest.mark.parametrize("factory_constructor", FACTORY_TYPES)
def test_missing_fail(factory_constructor):
    # Downstream recipes that have allow_missing false and
    # MissingDependencyBehavior.SKIP OR BIND cause a failure when a dependency is
    # missing.
    f = factory_constructor()
    skip_fail = MultiColumn(columns=(Raiser(),))
    bind_fail = BindMissing(columns=(Raiser(),), allow_missing=False)

    for r in (
        bind_fail,
        skip_fail,
    ):
        with pytest.raises(exceptions.MissingDependencyError) as e:
            f.process_recipe(r)

            assert e.value.args == (
                "Unable to build 1 recipes because RuntimeError() from Raiser(\n)",
            )


@pytest.mark.parametrize("factory_constructor", FACTORY_TYPES)
def test_missing_bind(factory_constructor):
    # Downstream recipes that have allow_missing true and MissingDependencyBehavior.BIND
    # receive a placeholder when a dependency is missing.

    f = factory_constructor()
    will_bind = BindMissing(columns=(Raiser(),))
    will_bind_also = BindMissing(columns=(will_bind,))

    placeholder = util.MissingPlaceholder(
        reason="RuntimeError()", fill_value="fill_value"
    )
    # The tuple wrapping is specific to the BindMissing recipe.
    assert f.process_recipe(will_bind) == (placeholder,)
    assert f.process_recipe(will_bind_also) == ((placeholder,),)


@pytest.mark.skip
def test_mp_timeout():
    assert 0


@pytest.mark.skip
def test_mp_error():
    assert 0


@pytest.mark.skip
def test_get_buildable_recipes():
    assert 0
