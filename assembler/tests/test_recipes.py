import dataclasses
import pytest

from assembler.tests.conftest import TestData, TestColumn, TABLES
from assembler.recipes import general
from assembler.factory import Factory


def test_immutable():
    t = TestColumn(table_name="tname", key=5)

    with pytest.raises(dataclasses.FrozenInstanceError):
        t.name = "sdaf"


def test_repr():
    t = TestColumn(table_name="tname", key=5)
    assert repr(t) == "TestColumn(\n    table_name='tname',\n    key=5,\n)"

    # Default values aren't displayed
    t = TestColumn(table_name="tname")
    assert repr(t) == "TestColumn(\n    table_name='tname',\n)"


def test_hash_eq():
    r1 = TestColumn(table_name="A", key=1)
    r2 = TestColumn(table_name="A", key=1)

    assert r1 == r2
    assert hash(r1) == hash(r2)


def test_extract_from_dependencies():
    recipe = TestData(table_name="A")
    assert recipe.extract_from_dependencies(None) == TABLES["A"]


def test_from_function():
    call_count = 0

    def function(a, b, c):
        nonlocal call_count
        call_count += 1
        return (a, b, c)

    r = general.FromFunction(
        function=function,
        args=(1, 2),
        kwargs={
            "c": 3,
        },
    )
    r2 = general.FromFunction(
        function=function,
        args=(1, 2),
        kwargs={
            "c": 3,
        },
    )
    f = Factory()
    result = f.process_recipes((r, r2))
    assert list(result.values()) == [(1, 2, 3)]

    # the underlying function is only called once.
    assert call_count == 1


def test_object():
    r = general.Object(payload=5)
    assert Factory().process_recipe(r) == 5


@pytest.mark.skip
def test_to_do():
    # Frames
    # What happens to downstream recipes when something is missing?

    #  Hard to check when exception is happening. Should downstream be skipped even if
    #  they don't allow missing? No. Could just pass missing to such a recipe, but that
    #  complicates recipe a lot, because any dependency could be missing.
    #
    #  Allow missing means skipped. Otherwise fail. Failure can report reason,
    #  responsible recipe.

    # Caching
    # Don't use args and kwargs in dependencyrequest. Make it more like a dict

    assert 0
