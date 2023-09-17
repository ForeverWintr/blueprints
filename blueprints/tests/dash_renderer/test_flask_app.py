from blueprints.renderers.dash_renderer import flask_app


def test_argparser() -> None:
    p = flask_app.get_argparse()
    args = p.parse_args(["--modules", "a,b,c"])
    assert args.modules == ("a", "b", "c")
