from contextlib import contextmanager
import subprocess
import threading
from pathlib import Path

from blueprints.renderers.dash_renderer import flask_app
from blueprints.recipes.base import RECIPE_TYPE_REGISTRY


@contextmanager
def dash_local_renderer():
    """Runs a dash server locally to render the blueprint"""
    server_path = Path(flask_app.__file__)

    # Use the recipe registry to list modules that need to be imported, then pass this
    # to the subprocess that runs the server.

    # Or import from registry?
    asdf
    yield
