from __future__ import annotations

import typing as tp
from pathlib import Path

import networkx as nx
import pytest
from frozendict import frozendict

from blueprints import serialization
from blueprints.blueprint import Blueprint
from blueprints.factory import util
from blueprints.recipes import base
from blueprints.recipes import general
from blueprints.recipes import static_frame
from blueprints.tests.conftest import Node


class Case(tp.NamedTuple):
    name: str
    recipes: tuple[base.Recipe]


def function_for_test():
    """For testing serialization"""


def make_examples() -> tp.Iterable[Case]:
    # Underscores in names so that I can test that each name only appears once in result
    # json.
    d = Node(name="dep__")
    r = Node(name="r__", dependencies=(d,))
    e = Node(name="e__", dependencies=(d,))
    yield Case("Shared Dependencies", (Node(name="out__", dependencies=(r, e)),))
    yield Case(
        "Object",
        (
            general.Object(
                payload=(5,),
            ),
        ),
    )

    # Functions
    yield Case("SimpleFunction", (general.FromFunction(function=function_for_test),))

    # Static frame
    series = static_frame.SeriesFromDelimited(
        frame_extract_kwargs=frozendict({"a": "b"}),
        column_name="asdf",
        file_path=Path("a"),
        missing_data_fill_value=0,
    )
    yield Case("SeriesFromDelimited", (series,))
    frame = static_frame.FrameFromDelimited(
        file_path=Path("a"),
        frame_extract_kwargs=frozendict({"a": "b"}),
    )
    yield Case("FrameFromDelimited", (frame,))

    yield Case(
        "FrameFromColumns",
        (static_frame.FrameFromColumns(name="ffc", recipes=(series, frame)),),
    )


@pytest.mark.parametrize("case", make_examples(), ids=lambda c: c.name)
def test_recipe_json(case):
    source = case.recipes

    j = serialization.recipes_to_json(source)

    # Each name should appear exactly once.
    names = [r.short_name() for r, _ in util.recipes_and_dependencies(source)]
    for n in names:
        assert j.count(n) == 1

    deserialized = serialization.recipes_from_json(j)

    assert deserialized == source
    assert hash(deserialized) == hash(source)


@pytest.mark.parametrize("case", make_examples(), ids=lambda c: c.name)
def test_blueprint_json(case):
    bp = Blueprint.from_recipes(case.recipes)

    j = bp.to_json()

    new = Blueprint.from_json(j)

    assert new._buildable == bp._buildable
    assert new.outputs == bp.outputs
    assert new._build_state == bp._build_state
    assert new._dependency_count == bp._dependency_count
    assert nx.utils.graphs_equal(new._dependency_graph, bp._dependency_graph)
