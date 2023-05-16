from __future__ import annotations

from flask import Blueprint as FlaskBlueprint
from flask import request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import orm

from assembler.blueprint import Blueprint

db = SQLAlchemy()
view = FlaskBlueprint("view", __name__)


class Frame(db.Model):
    frame_id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    run_id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    blueprint_data: orm.Mapped[str] = orm.mapped_column


@view.post("/blueprint")
def new_blueprint():
    # Validate the received blueprint by loading it.
    bp = Blueprint.from_serializable_dict(request.json)

    asdf
