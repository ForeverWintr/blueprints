from frame_factory.tests.conftest import TestData, TestColumn, TABLES


def test_immutable():
    assert 0


def test_repr():
    assert 0


def test_hash_eq():
    r1 = TestColumn("A", 1)
    r2 = TestColumn("A", 1)

    assert r1 == r2
    assert hash(r1) == hash(r2)
