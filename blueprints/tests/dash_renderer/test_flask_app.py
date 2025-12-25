from unittest import mock

from blueprints.renderers.dash_renderer import flask_app


def test_argparser() -> None:
    p = flask_app.get_argparse()
    args = p.parse_args(["--modules", "a,b,c"])
    assert args.modules == ("a", "b", "c")


@mock.patch.object(flask_app.Flask, "run")
@mock.patch.object(flask_app.importlib, "import_module")
def test_run_locally(mock_import, mock_run) -> None:
    flask_app.run_locally(["--modules", "imaginary.module.a,imaginary.module.b"])

    mock_import.assert_has_calls(
        [mock.call("imaginary.module.a"), mock.call("imaginary.module.b")]
    )
    mock_run.assert_called_once_with(debug=True, use_reloader=False)
