from dash import Dash, html, dcc
from dash.dependencies import Input, Output, State
import dash_cytoscape as cyto
from dash import ctx

from blueprints.blueprint import Blueprint
from blueprints.tests.test_blueprint import Node
from blueprints.constants import (
    NodeAttrs,
    BuildStatus,
    BUILD_STATUS_TO_COLOR,
    MissingDependencyBehavior,
)

s = Node(name="source")
a = Node(name="a", dependencies=(s,))
d = Node(name="d")
b = Node(name="out_b", dependencies=(a,))
c = Node(name="out_c", dependencies=(a, d))

bp = Blueprint.from_recipes([b, c])

g = bp._dependency_graph
elements = []
for edge in g.edges:
    a, b = (str(x) for x in edge)
    for n in (a, b):
        element = {
            "data": {"id": n, "label": n},
            "grabbable": False,
            "classes": "square",
        }
        elements.append(element)
    elements.append({"data": {"source": a, "target": b}})

cyto.load_extra_layouts()
app = Dash(__name__)


cytoscape = cyto.Cytoscape(
    id="cytoscape-two-nodes",
    layout={"name": "dagre"},
    style={"width": "100vw", "height": "90vh"},
    elements=elements,
    stylesheet=[  # Group selectors
        {"selector": "node", "style": {"content": "data(label)"}},
        # Class selectors
        {"selector": ".red", "style": {"background-color": "red", "line-color": "red"}},
        {"selector": ".square", "style": {"shape": "square"}},
    ],
)


app.layout = html.Div(
    [
        cytoscape,
        # The memory store reverts to the default on every page refresh
        dcc.Store("step-index", data=1, storage_type="memory"),
        html.Button("Previous", id="btn-prev"),
        html.Button("Next", id="btn-next"),
    ]
)


# @app.callback(
# Output("cytoscape-elements-callbacks", "elements"),
# Output("step-index", "data"),
# Input("step-index", "data"),
# Input("btn-prev", "n_clicks"),
# Input("btn-next", "n_clicks"),
# )
def update_graph_scatter(step_idx, btn_prev_clicks, btn_next_clicks):
    btn_clicked = ctx.triggered_id

    if btn_clicked == "btn-next":
        step_idx = step_idx + 1
    elif btn_clicked == "btn-prev":
        step_idx = step_idx - 1

    while step_idx > len(steps):
        steps.append(make_step())

    return steps[step_idx - 1], step_idx


if __name__ == "__main__":
    app.run(debug=True)
