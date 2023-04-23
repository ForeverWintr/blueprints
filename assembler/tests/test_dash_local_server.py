from assembler.renderers import dash_local_server


def test_update():
    client = dash_local_server.app.server.test_client()

    client.post("/update", json={"test": 2})

    assert 0
