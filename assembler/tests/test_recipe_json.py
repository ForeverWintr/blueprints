from __future__ import annotations
import typing as tp
import dataclasses
import pytest
import json

from assembler.tests.conftest import TestData, TestColumn, TABLES, Node
from assembler.recipes import general, static_frame, base
from assembler.factory import Factory, util
from assembler import serialization


class Case(tp.NamedTuple):
    name: str
    recipe: base.Recipe


def make_examples() -> tp.Iterable[Case]:
    # Underscores in names so that I can test that each name only appears once in result
    # json.
    d = Node(name="dep__")
    r = Node(name="r__", dependencies=(d,))
    e = Node(name="e__", dependencies=(d,))
    yield Case("Shared Dependencies", Node(name="out", dependencies=(r, e)))


@pytest.mark.parametrize("case", make_examples(), ids=lambda c: c.name)
def test_json(case):
    # TODO:
    # Need to handle functions.
    source = case.recipe

    j = serialization.recipe_to_json(source)

    # Each name should appear exactly once.
    names = [r.name for r, _ in util.recipes_and_dependencies([source])]

    for n in names:
        assert j.count(n) == 1

    deserialized = base.Recipe.from_json(j)

    assert deserialized == source
    assert hash(deserialized) == hash(source)
