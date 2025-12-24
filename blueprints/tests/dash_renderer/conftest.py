from __future__ import annotations

import typing as tp

import pytest

from blueprints.renderers.dash_renderer import flask_app
from blueprints.renderers.dash_renderer import models
from blueprints.tests import conftest

if tp.TYPE_CHECKING:
    from flask.testing import FlaskClient



@pytest.fixture
def test_client() -> tp.Iterator[FlaskClient]:
    app = flask_app.create_app()
    app.testing = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def existing_run_id(
    test_client, basic_blueprint: conftest.Blueprint
) -> tp.Iterator[str]:
    run_id = "fake-run-id"
    with test_client.application.app_context():
        for i, node in enumerate(basic_blueprint._dependency_graph.nodes):
            basic_blueprint.mark_built(node)
            frame = models.Frame(
                run_id=run_id, blueprint_data=basic_blueprint.to_json(), frame_no=i
            )
            models.db.session.add(frame)

        models.db.session.commit()
        yield run_id
