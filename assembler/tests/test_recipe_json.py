from __future__ import annotations
import typing as tp
import dataclasses
import pytest
import json
from pathlib import Path

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
    yield Case("SimpleFunction", (general.FromFunction(function=test_function),))

    # Static frame
    series = static_frame.SeriesFromDelimited(
        column_name="asdf", file_path=Path("a"), missing_data_fill_value=0
    )
    yield Case("SeriesFromDelimited", (series,))
    frame = static_frame.FrameFromDelimited(file_path=Path("a"))
    yield Case("FrameFromDelimited", (frame,))

    yield Case(
        "FrameFromRecipes",
        (static_frame.FrameFromRecipes(recipes=(series, frame)),),
    )


@pytest.mark.parametrize("case", make_examples(), ids=lambda c: c.name)
def test_json(case):
    # TODO:
    # Need to handle functions.
    source = case.recipes

    j = serialization.recipes_to_json(source)

    # Each name should appear exactly once.
    names = [r.short_name() for r, _ in util.recipes_and_dependencies(source)]
    for n in names:
        assert j.count(n) == 1

    deserialized = serialization.recipes_from_json(j)

    assert deserialized == source
    assert hash(deserialized) == hash(source)
