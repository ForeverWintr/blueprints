# It looks like I created this somewhere else and forgot to add it.
import datetime

import jwt
from flask import current_app

def create_jwt(run_id: str):
    return jwt.encode(
            {
                "run_id": run_id,
                # iat stands for 'Issued At', and is a reserved term in jwt.
                "iat": datetime.datetime.utcnow(),
            },
            key=current_app.config["SECRET_KEY"],
        )

