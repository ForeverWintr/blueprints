import signal
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path

import requests

from blueprints.recipes.base import RECIPE_TYPE_REGISTRY
from blueprints.renderers.dash_renderer import flask_app


@contextmanager
def dash_local_renderer(launch_server: bool = True) -> int | None:
    """Runs a dash server locally to render the blueprint"""
    server_path = Path(flask_app.__file__)

    # Use the recipe registry to list modules that need to be imported, then pass this
    # to the subprocess that runs the server.
    command = [
        sys.executable,
        # "python",
        server_path,
        "--modules",
        ",".join(RECIPE_TYPE_REGISTRY.modules()),
    ]
    print(' '.join(str(c) for c in command))
    proc = None
    if launch_server:
        proc = subprocess.Popen(command)

    server_up = False
    while not server_up:
        time.sleep(0.001)
        r = requests.get("http://127.0.0.1:5000/status")
        server_up = r.status_code == 200
    yield proc

    if launch_server:
        proc.send_signal(signal.SIGINT)
        return proc.wait(timeout=10)
