import random
from collections import deque

import dash
import plotly
import plotly.graph_objs as go
from dash import ctx, dcc, html
from dash.dependencies import Input, Output

X = deque(maxlen=20)
X.append(1)

Y = deque(maxlen=20)
Y.append(1)

app = dash.Dash(__name__)

app.layout = html.Div(
    [
        dcc.Graph(id="live-graph", animate=True),
        # The memory store reverts to the default on every page refresh
        dcc.Store("step-index", data=1, storage_type="memory"),
        html.Button("Previous", id="btn-prev"),
        html.Button("Next", id="btn-next"),
    ]
)
steps = []


def make_step():
    X.append(X[-1] + 1)
    Y.append(Y[-1] + Y[-1] * random.uniform(-0.1, 0.1))

    data = plotly.graph_objs.Scatter(
        x=list(X), y=list(Y), name="Scatter", mode="lines+markers"
    )
    return {
        "data": [data],
        "layout": go.Layout(
            xaxis=dict(range=[min(X), max(X)]),
            yaxis=dict(range=[min(Y), max(Y)]),
        ),
    }


@app.callback(
    Output("live-graph", "figure"),
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
