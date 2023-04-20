from dash import Dash, html, dcc
from dash.dependencies import Input, Output, State
import dash_cytoscape as cyto
from dash import ctx


class DashRenderer:
    def __enter__(self):
        cyto.load_extra_layouts()

        graph = cyto.Cytoscape(
            id="blueprint",
            layout={"name": "dagre"},
            style={"width": "100vw", "height": "90vh"},
            elements=[],
            stylesheet=[
                {"selector": "node", "style": {"content": "data(label)"}},
                {
                    "selector": ".red",
                    "style": {"background-color": "red", "line-color": "red"},
                },
                {"selector": ".square", "style": {"shape": "square"}},
            ],
        )
        self.app = Dash(__name__)
        self.app.layout = html.Div(
            [
                graph,
                # The memory store reverts to the default on every page refresh
                dcc.Store("step-index", data=1, storage_type="memory"),
                html.Button("Previous", id="btn-prev"),
                html.Button("Next", id="btn-next"),
            ]
        )


# Separate server with endpoint for updating graph. Renderer posts to server. Renderer
# launches server with token?
