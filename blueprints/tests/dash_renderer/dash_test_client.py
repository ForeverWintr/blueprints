from pathlib import Path
import subprocess
import sys
import time
import pprint
import webbrowser

import requests

from blueprints.renderers.dash_renderer import flask_app
from blueprints.tests.conftest import Node, Blueprint
from blueprints.factory import Factory


def nodes() -> dict[str, Node]:
    a = Node(name="a")
    d = Node(name="d")
    b = Node(name="b", dependencies=(a,))
    c = Node(name="c", dependencies=(a, d))
    return {
        "a": a,
        "d": d,
        "b": b,
        "c": c,
    }


def basic_blueprint(nodes) -> Blueprint:
    return Blueprint.from_recipes([nodes["b"], nodes["c"]])


def send(bp: Blueprint, url: str) -> dict:
    print("Uploading blueprint")
    r = requests.post(f"{url}/blueprint", json=bp.to_serializable_dict())
    print(r)
    return r.json()


def main():
    server_path = Path(flask_app.__file__)
    url = "http://127.0.0.1:5000"
    node_map = nodes()
    bp = basic_blueprint(node_map)

    result_data = send(bp, url)

    result_data["viz_url"] = f'{url}/visualize/{result_data["run_id"]}'
    pprint.pprint(result_data)

    webbrowser.open(result_data["viz_url"])
    # finally:
    # proc.kill()

    # breakpoint()


if __name__ == "__main__":
    main()
