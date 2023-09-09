import typing as tp

from blueprints.renderers.dash_renderer import flask_app


def main() -> tp.NoReturn:
    # Imports for recipes
    from blueprints.tests import conftest

    app = flask_app.create_app()
    app.run(debug=True, use_reloader=False)


if __name__ == "__main__":
    main()
