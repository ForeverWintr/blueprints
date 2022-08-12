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


def to_do():
    # Should I use dataclasses? - yes
    # Multiprocessing
    # Frames
    # CI
    # Real recipe
    # Caching
    assert 0