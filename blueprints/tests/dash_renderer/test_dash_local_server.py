from __future__ import annotations
import typing as tp

from flask import url_for

from blueprints.renderers.dash_renderer import flask_app
from blueprints.tests import conftest


if tp.TYPE_CHECKING:
    from flask.testing import FlaskClient


def test_post(test_client: FlaskClient, basic_blueprint: conftest.Blueprint) -> None:
    r = test_client.post("/blueprint", json=basic_blueprint.to_serializable_dict())
    assert r.status_code == 200
    json_data = r.json
    assert set(json_data.keys()) == {"frame_no", "next_frame", "run_id", "token"}
    assert json_data["frame_no"] == 0

    for i in range(1, 4):
        r = test_client.post(
            json_data["next_frame"],
            json=basic_blueprint.to_serializable_dict(),
            headers={
                "Authorization": f"Bearer {json_data['token']}",
            },
        )

        assert r.status_code == 200
        json_data = r.json
        assert set(json_data.keys()) == {"frame_no", "next_frame", "run_id", "token"}
        assert json_data["frame_no"] == i


def test_post_bad_token(
    test_client: FlaskClient, basic_blueprint: conftest.Blueprint
) -> None:
    run_1 = test_client.post("/blueprint", json=basic_blueprint.to_serializable_dict())
    run_2 = test_client.post("/blueprint", json=basic_blueprint.to_serializable_dict())

    bad_tokens = (
        # Valid, but wrong run.
        (run_2.json["token"], 404),
        # Invalid.
        (run_1.json["token"][:-1], 403),
    )

    for token, status in bad_tokens:
        # Fail if we call post with an invalid token
        r = test_client.post(
            run_1.json["next_frame"],
            json=basic_blueprint.to_serializable_dict(),
            headers={
                "Authorization": f"Bearer {token}",
            },
        )
        assert r.status_code == status
