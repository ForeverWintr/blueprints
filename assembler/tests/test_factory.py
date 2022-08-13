from __future__ import annotations
import typing as tp
from collections import defaultdict

import pytest

from assembler.recipes import Recipe
from assembler.factory import Factory, FrameFactoryMP
from assembler import exceptions
from assembler.tests.conftest import TestData, TestColumn, TABLES, MultiColumn


def test_build_recipe() -> None:
    factory = Factory()
    result = factory.process_recipe(TestColumn(table_name="A", key=1))
    assert result == TABLES["A"][1]


def test_extract_from_dependency():
    recipe = TestData(table_name="A")
    assert recipe.extract_from_dependency() == TABLES["A"]


def test_multiprocess_graph():
    r1 = TestColumn(table_name="A", key=1)
    r2 = TestColumn(table_name="b", key=3)
    r3 = TestColumn(table_name="A", key=2)
    ff = FrameFactoryMP()
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
