from assembler.renderers.dash_renderer import flask_app


def test_update():
    app = flask_app.create_app()
    client = app.test_client()

    r = client.post("/blueprint", json={"test": 2})

    assert 0
