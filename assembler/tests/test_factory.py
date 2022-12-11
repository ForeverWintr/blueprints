from __future__ import annotations

import pytest

from assembler.factory import Factory, FactoryMP
from assembler.tests.conftest import TestData, TestColumn, TABLES, MultiColumn, Raiser
from assembler.blueprint import Blueprint
from assembler import exceptions
from assembler import util

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
def test_empty_buildable_error(factory_constructor):
    # A malformed blueprint that has no buildable recipes.
    b = Blueprint.from_recipes((TestColumn(table_name="A", key=1),))
    b._buildable = frozenset()

    f = factory_constructor()
    with pytest.raises(exceptions.AssemblerError):
        f.process_blueprint(b)


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

    assert r == util.MissingPlaceholder(reason="", fill_value="fill_value")


@pytest.mark.skip
def test_mp_timeout():

    assert 0


@pytest.mark.skip
def test_mp_error():

    assert 0


@pytest.mark.skip
def test_get_buildable_recipes():

    assert 0
