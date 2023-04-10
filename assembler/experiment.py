from collections import deque

import dash
from dash.dependencies import Output, Input
from dash import dcc
from dash import html
from dash import ctx
import plotly
import random
import plotly.graph_objs as go

X = deque(maxlen=20)
X.append(1)

Y = deque(maxlen=20)
Y.append(1)

app = dash.Dash(__name__)

app.layout = html.Div(
    [
        dcc.Graph(id="live-graph", animate=True),
        # dcc.Interval(id="graph-update", interval=1000, n_intervals=0),
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
    [
        Input("btn-prev", "n_clicks"),
        Input("btn-next", "n_clicks"),
    ],
)
def update_graph_scatter(btn_prev_clicks, btn_next_clicks):
    btn_clicked = ctx.triggered_id
    print(btn_clicked)
    n_steps = len(steps)

    if btn_clicked == "btn-next":
        while btn_next_clicks > n_steps:
            steps.append(make_step())
            n_steps = len(steps)
        return steps[btn_next_clicks - 1]
    elif btn_clicked == "btn-prev":
        return steps[btn_prev_clicks - 1]
    else:
        # startup
        steps.append(make_step())
        return steps[-1]


if __name__ == "__main__":
    app.run_server()
