from flask import Flask

from assembler.renderers.dash_renderer.models import db


def create_app():
    app = Flask(__name__)

    # In memory db:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"

    # For debugging db in viewer:
    # app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////tmp/project.db"

    db.init_app(app)
    with app.app_context():
        db.create_all()
    return app


if __name__ == "__main__":
    app = create_app()
    app.run()
