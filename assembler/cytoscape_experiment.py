from dash import Dash, html
import dash_cytoscape as cyto

cyto.load_extra_layouts()
app = Dash(__name__)

cytoscape = cyto.Cytoscape(
    id="cytoscape-two-nodes",
    layout={"name": "dagre"},
    style={"width": "100vw", "height": "100vh"},
    elements=[
        {
            "data": {"id": "one", "label": "Node 1"},
            # "position": {"x": 75, "y": 75},
            "grabbable": False,
            "classes": "red triangle",
        },
        {
            "data": {"id": "two", "label": "Node 2"},
            # "position": {"x": 200, "y": 200},
            "grabbable": False,
        },
        {"data": {"source": "one", "target": "two"}},
    ],
    stylesheet=[  # Group selectors
        {"selector": "node", "style": {"content": "data(label)"}},
        # Class selectors
        {"selector": ".red", "style": {"background-color": "red", "line-color": "red"}},
        {"selector": ".triangle", "style": {"shape": "triangle"}},
    ],
)
app.layout = html.Div([cytoscape])
if __name__ == "__main__":
    app.run(debug=True)
