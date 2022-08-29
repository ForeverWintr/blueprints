from __future__ import annotations

import pytest

from assembler.factory import Factory, FactoryMP
from assembler.tests.conftest import TestData, TestColumn, TABLES, MultiColumn

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


def test_dependency_order():
    # Dependency order should be guaranteed.

    r = MultiColumn(
        columns=(
            TestColumn(table_name="A", key=1),
            TestColumn(table_name="A", key=1),
            TestColumn(table_name="b", key=4),
            TestColumn(table_name="A", key=2),
            TestColumn(table_name="A", key=1),
        )
    )

    assert Factory().process_recipe(r) == (1, 1, 4, 2, 1)


def test_mp_timeout():

    assert 0


def test_mp_error():

    assert 0


def test_get_buildable_recipes():

    assert 0


def test_allow_missing():
    assert 0
