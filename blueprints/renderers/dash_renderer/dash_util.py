from blueprints.blueprint import Blueprint


def blueprint_to_cytoscape(blueprint: Blueprint) -> list[dict]:
    """Convert the given blueprint into a list of nodes and edges for cytoscape."""
    # TODO public?
    g = blueprint._dependency_graph
    elements = []
    for edge in g.edges:
        names = [n.short_name() for n in edge]
        elements.append({"data": {"source": names[0], "target": names[1]}})

        for node, name in zip(edge, names):
            element = {
                "data": {"id": name, "label": name},
                "grabbable": False,
                "classes": blueprint.get_build_state(node).name,
            }
            elements.append(element)

    return elements
