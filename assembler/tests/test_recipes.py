import dataclasses
import pytest

from assembler.tests.conftest import TestData, TestColumn, TABLES


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
    assert recipe.extract_from_dependencies() == TABLES["A"]


@pytest.mark.skip
def test_to_do():
    # Should I use dataclasses? - yes
    # Frames
    # What happens to downstream recipes when something is missing?

    #  Hard to check when exception is happening. Should downstream be skipped even if
    #  they don't allow missing? No. Could just pass missing to such a recipe, but that
    #  complicates recipe a lot, because any dependency could be missing. Allow missing
    #  means skipped. Otherwise fail? Failure can report reason, responsible recipe.

    # Caching
    # Don't use args and kwargs in dependencyrequest. Make it more like a dict

    assert 0
