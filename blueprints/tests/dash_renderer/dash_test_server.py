import typing as tp

from blueprints.renderers.dash_renderer import flask_app


def main() -> tp.NoReturn:
    # Imports for recipes
    from blueprints.tests import conftest

    app = flask_app.create_app()
    app.run(debug=False, use_reloader=False, passthrough_errors=True)


# Component that:
# Attaches to BP and sends updates to server

# with dash_renderer() is tempting, but you don't want to stop the server then (unless I
# change how callbacks work). But if you don't do that, you either make the subprocess a
# daemon, or make the parent process wait. If it's going to wait it should be in a
# context manager.

# Translates a blueprint into cytoscape.


if __name__ == "__main__":
    main()
