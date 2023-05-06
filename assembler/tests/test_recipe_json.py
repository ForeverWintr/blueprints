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
    recipes: tuple[base.Recipe]


def test_function():
    """For testing serialization"""


def make_examples() -> tp.Iterable[Case]:
    # Underscores in names so that I can test that each name only appears once in result
    # json.
    d = Node(name="dep__")
    r = Node(name="r__", dependencies=(d,))
    e = Node(name="e__", dependencies=(d,))
    yield Case("Shared Dependencies", (Node(name="out__", dependencies=(r, e)),))

    # Functions
    # Registry or importlib?
    # Registry lets you define functions in a loop/function/not module level if you want.
    # Disallows redefinition.
    # Requires the same code to be executed on the server, which could be difficult.
    # So you can only define functions not at module level if you execute the same code on the server.
    yield Case("Function", (general.FromFunction(function=test_function),))


@pytest.mark.parametrize("case", make_examples(), ids=lambda c: c.name)
def test_json(case):
    # TODO:
    # Need to handle functions.
    source = case.recipes

    j = serialization.recipes_to_json(source)

    # Each name should appear exactly once.
    names = [r.name for r, _ in util.recipes_and_dependencies(source)]
    for n in names:
        assert j.count(n) == 1

    deserialized = serialization.recipes_from_json(j)

    assert deserialized == source
    assert hash(deserialized) == hash(source)
