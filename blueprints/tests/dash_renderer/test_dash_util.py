from __future__ import annotations

import typing as tp

from blueprints.renderers.dash_renderer import dash_util

if tp.TYPE_CHECKING:
    from blueprints.blueprint import Blueprint


def test_blueprint_to_cytoscape(basic_blueprint: Blueprint) -> None:
    c = dash_util.blueprint_to_cytoscape(basic_blueprint)
    assert c == [
        {"data": {"source": "a", "target": "b"}},
        {"data": {"id": "a", "label": "a"}, "grabbable": False, "classes": "BUILDABLE"},
        {
            "data": {"id": "b", "label": "b"},
            "grabbable": False,
            "classes": "NOT_STARTED",
        },
        {"data": {"source": "a", "target": "c"}},
        {"data": {"id": "a", "label": "a"}, "grabbable": False, "classes": "BUILDABLE"},
        {
            "data": {"id": "c", "label": "c"},
            "grabbable": False,
            "classes": "NOT_STARTED",
        },
        {"data": {"source": "d", "target": "c"}},
        {"data": {"id": "d", "label": "d"}, "grabbable": False, "classes": "BUILDABLE"},
        {
            "data": {"id": "c", "label": "c"},
            "grabbable": False,
            "classes": "NOT_STARTED",
        },
    ]
