from flask import Flask
import jwt

from blueprints.renderers.dash_renderer import models, dash_layout, auth


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


if __name__ == "__main__":
    # Note: if using this to debug, remember to import any recipe you plan to send to
    # the server.
    # TODO: add a recipe import hook.
    app = create_app()
    app.run(debug=True, use_reloader=False)
