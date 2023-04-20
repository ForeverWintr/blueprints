from dash import Dash, html, dcc
import dash_cytoscape as cyto

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
        {"data": {"source": "one", "target": "two"}},
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
if __name__ == "__main__":
    app.run(debug=True)
