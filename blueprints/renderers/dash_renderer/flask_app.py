import argparse
import importlib
import typing as tp

import jwt
from flask import Flask

from blueprints.renderers.dash_renderer import auth, dash_layout, models


def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = "insecure"

    # In memory db:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"

    # For debugging db in viewer:
    # app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////tmp/project.db"

    models.db.init_app(app)
    with app.app_context():
        models.db.create_all()

    app.register_blueprint(models.view)

    app.errorhandler(jwt.DecodeError)(auth.jwt_auth_error_handler)

    dash_layout.dash_app.init_app(app)
    return app


def _parse_modules(modules: str) -> tuple:
    return tuple(x.strip() for x in modules.split(","))


def get_argparse() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=run_locally.__doc__)
    p.add_argument(
        "--modules",
        help="Comma separated list of modules to import before launching the server.",
        type=_parse_modules,
        default=(),
    )
    return p


def status():
    """Return 200 once the app is running"""
    return ("OK", 200)


def run_locally(argv: list[str] | None = None) -> tp.NoReturn:
    """Launch a local server, for use with dash local renderer"""
    p = get_argparse()
    args = p.parse_args(argv)

    # Import so the server has access to recipes.
    for m in args.modules:
        importlib.import_module(m)

    app = create_app()

    # Register a status endpoing
    app.get("/status")(status)

    app.run(debug=True, use_reloader=False)


if __name__ == "__main__":
    # Note: if using this to debug, remember to import any recipe you plan to send to
    # the server.
    run_locally()
