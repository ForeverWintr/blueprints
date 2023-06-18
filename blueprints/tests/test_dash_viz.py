import plotly
from plotly import graph_objects as go

# from plotly import express as px # Requires pandas :|

from blueprints.blueprint import Blueprint, get_blueprint_layout
from blueprints.tests.test_blueprint import Node


def test_visualize() -> None:
    a = Node(name="a")
    d = Node(name="d")
    b = Node(name="b", dependencies=(a,))
    c = Node(name="c", dependencies=(a, d))

    bp = Blueprint.from_recipes([b, c])
    layout = get_blueprint_layout(bp._dependency_graph)

    edge_x = []
    edge_y = []
    node_x = []
    node_y = []
    seen = set()
    for edge in bp._dependency_graph.edges():
        for node in edge:
            x, y = layout[node]
            edge_x.append(x)
            edge_y.append(y)
            if not node in seen:
                node_x.append(x)
                node_y.append(y)
                seen.add(node)

        # Add None to break the line
        edge_x.append(None)
        edge_y.append(None)

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line=dict(width=0.5, color="#888"),
        hoverinfo="none",
        mode="lines",
    )

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        # hoverinfo="text",
        marker_symbol="square",
        marker_size=30,
        text=[str(n) for n in bp._dependency_graph.nodes],
    )
    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            title="<br>Network graph made with Python",
            titlefont_size=16,
            showlegend=False,
            hovermode="closest",
            margin=dict(b=20, l=5, r=5, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        ),
    )
    # fig.show()
    assert 0


def test_cytoscape() -> None:
    # https://dash.plotly.com/cytoscape
    # SRSLY https://dash.plotly.com/cytoscape/callbacks
    a = Node(name="a")
    d = Node(name="d")
    b = Node(name="b", dependencies=(a,))
    c = Node(name="c", dependencies=(a, d))

    bp = Blueprint.from_recipes([b, c])

    g = bp._dependency_graph
    assert 0
