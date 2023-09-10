from __future__ import annotations
import typing as tp
import datetime
import uuid
from functools import lru_cache, cached_property

from flask import Blueprint as FlaskBlueprint
from flask import request, current_app, jsonify, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import orm
import jwt

from blueprints.blueprint import Blueprint
from blueprints.renderers.dash_renderer import auth

db = SQLAlchemy()
view = FlaskBlueprint("view", __name__)


class Frame(db.Model):
    run_id: orm.Mapped[str] = orm.mapped_column(
        primary_key=True, default=lambda: str(uuid.uuid4())
    )
    frame_no: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    blueprint_data: orm.Mapped[str] = orm.mapped_column()

    @cached_property
    def blueprint(self) -> Blueprint:
        return Blueprint.from_json(self.blueprint_data)


@lru_cache
def get_frame(run_id: str, frame_no: int) -> Frame:
    return (
        db.session.query(Frame)
        .filter(Frame.run_id == run_id, Frame.frame_no == frame_no)
        .one()
    )


def response(frame: Frame, token: dict[str, int | str]) -> dict[str, int | str]:
    return {
        "token": token,
        "run_id": frame.run_id,
        "frame_no": frame.frame_no,
        "next_frame": url_for(
            "view.add_frame",
            run_id=frame.run_id,
            frame_no=frame.frame_no + 1,
        ),
    }


@view.post("/blueprint")
def new_blueprint() -> None:
    """Post a new blueprint"""
    # Validate the received blueprint by loading it.
    bp = Blueprint.from_serializable_dict(request.json)

    # Note it makes sense to store entire blueprints as frames. It's simpler, and it
    # allows the possibility of the blueprint changing mid run (e.g., combining
    # groupbys)
    new_frame = Frame(blueprint_data=bp.to_json(), frame_no=0)
    db.session.add(new_frame)
    db.session.commit()

    token = auth.create_jwt(new_frame.run_id)

    return jsonify(response(new_frame, token))


@view.put("/blueprint/<run_id>/<frame_no>")
def add_frame(run_id: str, frame_no: str) -> None:
    token = jwt.decode(
        jwt=request.headers.get("Authorization").removeprefix("Bearer "),
        key=current_app.config.get("SECRET_KEY"),
        algorithms=["HS256"],
    )
    if token["run_id"] != run_id:
        return jsonify({"message": f"{run_id} does not match token."}), 404

    bp = Blueprint.from_serializable_dict(request.json)
    new_frame = Frame(blueprint_data=bp.to_json(), frame_no=int(frame_no))
    db.session.add(new_frame)
    db.session.commit()

    return jsonify(response(new_frame, token))
