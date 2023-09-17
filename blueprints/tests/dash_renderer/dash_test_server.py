import typing as tp

from blueprints.renderers.dash_renderer import flask_app


def main() -> tp.NoReturn:
    # Imports for recipes
    from blueprints.tests import conftest

    app = flask_app.create_app()
    app.run(debug=False, use_reloader=False, passthrough_errors=True)


# Component that:
# Attaches to BP and sends updates to server
# Translates a blueprint into cytoscape. x


if __name__ == "__main__":
    main()
