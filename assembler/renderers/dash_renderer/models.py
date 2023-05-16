from __future__ import annotations

from flask import Blueprint as FlaskBlueprint
from flask import request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import orm


db = SQLAlchemy()
view = FlaskBlueprint("view", __name__)


class Blueprint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    structure = db.Column(db.String)
    states: orm.Mapped[list[State]] = orm.relationship(back_populates="parent")


class State(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    blueprint: orm.Mapped[Blueprint] = orm.relationship(back_populates="states")


@view.post("/blueprint")
def new_blueprint():
    request.json

    asdf
