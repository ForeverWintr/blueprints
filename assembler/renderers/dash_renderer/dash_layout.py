from dash import Dash, html, dcc
from dash.dependencies import Input, Output, State
import dash_cytoscape as cyto
from dash import ctx
from flask import request


cyto.load_extra_layouts()
dash_app = Dash(__name__, server=False)


cytoscape = cyto.Cytoscape(
    id="cytoscape-two-nodes",
    layout={"name": "dagre"},
    style={"width": "100vw", "height": "90vh"},
    elements=[],
    stylesheet=[  # Group selectors
        {"selector": "node", "style": {"content": "data(label)"}},
        # Class selectors
        {"selector": ".red", "style": {"background-color": "red", "line-color": "red"}},
        {"selector": ".square", "style": {"shape": "square"}},
    ],
)

dash_app.layout = html.Div(
    [
        cytoscape,
        # The memory store reverts to the default on every page refresh
        # dcc.Store("step-index", data=1, storage_type="memory"),
        # html.Button("Previous", id="btn-prev"),
        # html.Button("Next", id="btn-next"),
    ]
)


@dash_app.callback(
    Output("cytoscape-elements-callbacks-2", "elements"),
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
    app.run()
