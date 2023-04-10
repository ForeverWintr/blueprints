import dash
from dash import html
from dash import dcc
from dash.exceptions import PreventUpdate
from dash.dependencies import Input, Output

import networkx as nx
from networkx.drawing.nx_agraph import to_agraph

app = dash.Dash(__name__)

# Define your DAG using the networkx library
G = nx.DiGraph()
G.add_edges_from([("A", "B"), ("A", "C"), ("B", "D"), ("C", "D")])

# Convert the networkx graph to a graphviz Agraph object
A = to_agraph(G)
A.layout(prog="dot")

# Define the layout of your app
app.layout = html.Div(
    [
        html.H1("Interactive DAG"),
        dcc.Input(id="input", type="text", placeholder="Enter a node"),
        html.Div(id="output"),
        html.Iframe(
            id="graph",
            srcDoc=A.draw(format="svg").decode("utf-8"),
            width="100%",
            height="600",
        ),
        dcc.Tooltip(id="tooltip", target="graph", placeholder=""),
    ]
)


# Define the callback that updates the output and tooltip when the input is changed
@app.callback(
    Output("output", "children"),
    Output("tooltip", "children"),
    Input("input", "value"),
)
def update_output(value):
    if not value:
        raise PreventUpdate
    return f'You entered "{value}"', ""


# Define the callback that updates the tooltip when a node is clicked
@app.callback(
    Output("tooltip", "children"),
    Input("graph", "clickData"),
)
def update_tooltip(click_data):
    if not click_data:
        raise PreventUpdate
    node_id = click_data["points"][0]["text"]
    return f'The node you clicked on is "{node_id}"'


if __name__ == "__main__":
    app.run_server(debug=True)
