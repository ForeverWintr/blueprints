from __future__ import annotations
import typing as tp

import pytest

from blueprints.renderers.dash_renderer import flask_app

if tp.TYPE_CHECKING:
    from flask.testing import FlaskClient


@pytest.fixture
def test_client() -> tp.Iterator[FlaskClient]:
    app = flask_app.create_app()
    app.testing = True
    with app.test_client() as client:
        yield client
