from assembler.renderers.dash_renderer import flask_app

from assembler.tests import conftest


def test_update(basic_blueprint: conftest.Blueprint):
    app = flask_app.create_app()
    client = app.test_client()

    r = client.post("/blueprint", json=basic_blueprint.to_serializable_dict())

    assert 0
