from blueprints.blueprint import Blueprint


def blueprint_to_cytoscape(blueprint: Blueprint) -> list[dict]:
    """Convert the given blueprint into a list of nodes and edges for cytoscape."""
    # TODO public?
    g = blueprint._dependency_graph
    elements = []
    for edge in g.edges:
        a, b = (x.short_name for x in edge)
        for n in (a, b):
            element = {
                "data": {"id": n, "label": n},
                "grabbable": False,
                "classes": "square",
            }
            elements.append(element)
        elements.append({"data": {"source": a, "target": b}})
    return elements
