from __future__ import annotations
import typing as tp

from flask import url_for

from blueprints.renderers.dash_renderer import flask_app
from blueprints.tests import conftest


if tp.TYPE_CHECKING:
    from flask.testing import FlaskClient


def test_update(test_client: FlaskClient, basic_blueprint: conftest.Blueprint):
    r = test_client.post("/blueprint", json=basic_blueprint.to_serializable_dict())
    assert r.status_code == 200
    json_data = r.json
    assert set(json_data.keys()) == {"frame_no", "next_frame", "run_id", "token"}
    assert json_data["frame_no"] == 0

    r2 = test_client.put(
        json_data["next_frame"],
        json=basic_blueprint.to_serializable_dict(),
        headers={
            "Authorization": f"Bearer {json_data['token']}",
        },
    )
    assert r2.status_code == 200
    json_data2 = r2.json
    assert set(json_data2.keys()) == {"frame_no", "next_frame", "run_id", "token"}
    assert json_data2["frame_no"] == 1


def test_update_bad_token(basic_blueprint: conftest.Blueprint):
    app = flask_app.create_app()
    app.testing = True
    assert 0
