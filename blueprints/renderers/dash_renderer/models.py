from __future__ import annotations

import datetime
import uuid

from flask import Blueprint as FlaskBlueprint
from flask import request, current_app, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import orm
import jwt

from assembler.blueprint import Blueprint

db = SQLAlchemy()
view = FlaskBlueprint("view", __name__)


class Frame(db.Model):
    run_id: orm.Mapped[str] = orm.mapped_column(
        primary_key=True, default=lambda: str(uuid.uuid4())
    )
    frame_id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    blueprint_data: orm.Mapped[str] = orm.mapped_column


@view.post("/blueprint")
def new_blueprint():
    """Post a new blueprint"""
    # Validate the received blueprint by loading it.
    bp = Blueprint.from_serializable_dict(request.json)

    # Note it makes sense to store entire blueprints as frames. It's simpler, and it allows the possibility of the blueprint changing mid run (e.g., combining groupbys)
    new_frame = Frame(blueprint_data=bp.to_json(), frame_id=0)
    db.session.add(new_frame)
    db.session.commit()

    # Should Run ID be a jwt?
    token = jwt.encode(
        {
            "run_id": new_frame.run_id,
            # iat stands for 'Issued At', and is a reserved term in jwt.
            "iat": datetime.datetime.utcnow(),
        },
        key=current_app.config["SECRET_KEY"],
    )
    return jsonify({"token": token, "run_id": new_frame.run_id})
