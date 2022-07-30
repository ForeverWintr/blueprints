from frame_factory.tests.conftest import TestData, TestColumn, TABLES


def test_immutable():
    assert 0


def test_repr():
    assert 0


def test_hash_eq():
    r1 = TestColumn(table_name="A", key=1)
    r2 = TestColumn(table_name="A", key=1)

    assert r1 == r2
    assert hash(r1) == hash(r2)


def to_do():
    # Should I use dataclasses?
    #  Benefits:
    #    Immuntablility
    #    Hash, EQ

    #  Drawbacks:
    #    Constructor only

    #  If you want this to be open source, dataclasses may be expected; Provide a good API.
    assert 0
