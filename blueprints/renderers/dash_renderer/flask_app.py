from flask import Flask

from blueprints.renderers.dash_renderer import models, dash_layout
from blueprints.tests import conftest


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

    dash_layout.dash_app.init_app(app)
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, use_reloader=False)
