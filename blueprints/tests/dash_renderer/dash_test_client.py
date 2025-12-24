import pprint
import webbrowser
from pathlib import Path

import requests

from blueprints.renderers.dash_renderer import flask_app
from blueprints.renderers.dash_renderer.local import dash_local_renderer
from blueprints.tests.conftest import Blueprint
from blueprints.tests.conftest import Node


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


def send(bp: Blueprint, url: str, headers=None) -> dict:
    print("Uploading blueprint")
    r = requests.post(url, json=bp.to_serializable_dict(), headers=headers)
    print(r)
    r.raise_for_status()
    return r.json()


def main():
    Path(flask_app.__file__)
    url = "http://127.0.0.1:5000"
    node_map = nodes()

    with dash_local_renderer(launch_server=True):
        bp = basic_blueprint(node_map)
        result_data = send(bp, url=f"{url}/blueprint")

        for node in bp._dependency_graph.nodes:
            bp.mark_built(node)
            result_data = send(
                bp,
                url=f'{url}{result_data["next_frame"]}',
                headers={
                    "Authorization": f"Bearer {result_data['token']}",
                },
            )

        result_data["viz_url"] = f'{url}/visualize/{result_data["run_id"]}'
        pprint.pprint(result_data)

        webbrowser.open(result_data["viz_url"])
        asdf
    # finally:
    # proc.kill()

    # breakpoint()


if __name__ == "__main__":
    main()
