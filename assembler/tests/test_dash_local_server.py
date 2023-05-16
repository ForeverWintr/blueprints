from assembler.renderers.dash_renderer import flask_app

from assembler.tests import conftest


def test_update(basic_blueprint: conftest.Blueprint):
    app = flask_app.create_app()
    app.testing = True

    with app.test_client() as client:
        r = client.post("/blueprint", json=basic_blueprint.to_serializable_dict())

    assert set(r.json.keys()) == {"token", "run_id"}
