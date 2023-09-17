from __future__ import annotations

import typing as tp

from blueprints.renderers.dash_renderer import dash_util

if tp.TYPE_CHECKING:
    from blueprints.blueprint import Blueprint


def test_blueprint_to_cytoscape(basic_blueprint: Blueprint) -> None:
    c = dash_util.blueprint_to_cytoscape(basic_blueprint)
    assert 0
