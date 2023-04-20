from dash import Dash, html, dcc
from dash.dependencies import Input, Output, State
import dash_cytoscape as cyto
from dash import ctx


cyto.load_extra_layouts()
app = Dash(__name__)

cytoscape = cyto.Cytoscape(
    id="cytoscape-two-nodes",
    layout={"name": "dagre"},
    style={"width": "100vw", "height": "90vh"},
    elements=[
        {
            "data": {"id": "one", "label": "Node 1"},
            # "position": {"x": 75, "y": 75},
            "grabbable": False,
            "classes": "red square",
        },
        {
            "data": {"id": "two", "label": "Node 2"},
            # "position": {"x": 200, "y": 200},
            "grabbable": False,
            "classes": "square",
        },
        {
            "data": {"id": "three", "label": "Node 3"},
            # "position": {"x": 200, "y": 200},
            "grabbable": False,
            "classes": "square",
        },
        {"data": {"source": "one", "target": "two"}},
        {"data": {"source": "three", "target": "two"}},
    ],
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


@app.callback(
    Output("cytoscape-elements-callbacks", "elements"),
    Output("step-index", "data"),
    Input("step-index", "data"),
    Input("btn-prev", "n_clicks"),
    Input("btn-next", "n_clicks"),
)
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
