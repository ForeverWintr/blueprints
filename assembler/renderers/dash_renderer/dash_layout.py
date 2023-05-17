from dash import Dash, html, dcc
from dash.dependencies import Input, Output, State
import dash_cytoscape as cyto
from dash import ctx
import dash
from flask import request


cyto.load_extra_layouts()
dash_app = Dash(
    __name__,
    server=__name__ == "__main__",
    url_base_pathname="/visualize/",
)


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
        dcc.Store("step-index", data=1, storage_type="memory"),
        html.Button("Previous", id="btn-prev"),
        html.Button("Next", id="btn-next"),
        html.P(id="err-msg", style={"color": "red"}),
        dcc.Location(id="test-location", refresh=False),
    ]
)


@dash_app.callback(
    # Output("cytoscape-two-nodes", "elements"),
    Output("step-index", "data"),
    Output("err-msg", "children"),
    Input("test-location", "pathname"),
    Input("step-index", "data"),
    Input("btn-prev", "n_clicks"),
    Input("btn-next", "n_clicks"),
)
def update_graph_scatter(url, step_idx, btn_prev_clicks, btn_next_clicks):
    components = [c for c in url.split("/") if c]
    if len(components) > 1:
        print("bad")
        return dash.no_update, "Bad!"
    print("good")
    return
    # https://hackersandslackers.com/plotly-dash-with-flask/
    # btn_clicked = ctx.triggered_id

    # if btn_clicked == "btn-next":
    # step_idx = step_idx + 1
    # elif btn_clicked == "btn-prev":
    # step_idx = step_idx - 1

    # while step_idx > len(steps):
    # steps.append(make_step())

    # return steps[step_idx - 1], step_idx


if __name__ == "__main__":
    dash_app.run(debug=True, use_reloader=False, port=5000)
