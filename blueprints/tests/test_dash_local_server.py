from flask import url_for

from blueprints.renderers.dash_renderer import flask_app
from blueprints.tests import conftest


def test_update(basic_blueprint: conftest.Blueprint):
    app = flask_app.create_app()
    app.testing = True

    with app.test_client() as client:
        r = client.post("/blueprint", json=basic_blueprint.to_serializable_dict())
        json_data = r.json
        assert set(json_data.keys()) == {"frame_no", "next_frame", "run_id", "token"}
        assert json_data["frame_no"] == 0

        r2 = client.put(
            json_data["next_frame"],
            json=basic_blueprint.to_serializable_dict(),
            headers={
                "Authorization": f"Bearer {json_data['token']}",
            },
        )
        assert 0
