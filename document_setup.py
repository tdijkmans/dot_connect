import inkex.utils
from inkex import Page
from inkex.base import ISVGDocumentElement
from inkex.elements import Layer


def setup(self, so):
    svg: ISVGDocumentElement = self.svg

    layers = {
        "solution_layer": {
            "id": "solution_layer",
            "remove": False,
            "create": True,
        },
        "instructions_layer": {
            "id": "instructions_layer",
            "remove": so.replace_instructions,
            "create": True,
        },
        "stats_layer": {
            "id": "stats_layer",
            "remove": True,
            "create": True,
        },
        "dots_layer": {
            "id": "dots_layer",
            "remove": so.replace_dots,
            "create": True,
        },
        "centroids_layer": {
            "id": "centroids_layer",
            "remove": so.replace_centroids,
            "create": True,
        },
    }

    paper = {"A4": (794, 1123), "US Letter": (810, 1050)}
    width = paper[so.paper_size][0]
    height = paper[so.paper_size][1]
    svg.set("width", width)
    svg.set("height", height)
    svg.set("viewBox", f"0 0 {width} {height}")

    pages = {
        "instructions": {
            "id": "instructions",
            "label": "Instructions",
            "margin": so.page_margin,
            "left_guide": "instructions_guide_left",
            "right_guide": "instructions_guide_right",
            "title_guide": "instructions_guide_title",
            "number": 2,
            "x": f"{-(width + 50)}",
            "y": 0,
            "width": f"{width}",
            "height": f"{height}",
        },
        "puzzle": {
            "id": "puzzle",
            "label": "Puzzle",
            "margin": so.page_margin,
            "left_guide": "puzzle_guide_left",
            "right_guide": "puzzle_guide_right",
            "center_guide": "puzzle_guide_center",
            "number": 1,
            "x": 0,
            "y": 0,
            "width": f"{width}",
            "height": f"{height}",
        },
        "stats": {
            "id": "stats",
            "label": "Stats",
            "margin": so.page_margin,
            "left_guide": "stats_guide_left",
            "right_guide": "stats_guide_right",
            "center_guide": "stats_guide_center",
            "number": 3,
            "x": f"{width + 50}",
            "y": 0,
            "width": f"{width}",
            "height": f"{height}",
        },
    }

    for page_id, p in pages.items():
        # Extract width and height from paper size dictionary
        width, height = int(p["width"]), int(p["height"])
        l_x = int(p["x"])
        r_x = l_x + width

        # Create a new page with the extracted information
        newpage: Page = svg.namedview.new_page(
            str(p["x"]),
            str(p["y"]),
            str(p["width"]),
            str(p["height"]),
            str(p["label"]),
        )
        newpage.set("id", p["id"])
        newpage.set("margin", p["margin"])

        # Add guides to the page
        pa = 36

        guides = []

        guides.append(
            svg.namedview.add_guide(
                (r_x - pa, pa), (1, 0), f"{p['label']} guide right"
            ).set("id", f"{page_id}_guide_right")
        )

        guides.append(
            svg.namedview.add_guide(
                (l_x + pa, pa), (1, 0), f"{p['label']} guide left"
            ).set("id", f"{page_id}_guide_left")
        )

        if page_id == "puzzle":
            guides.append(
                (
                    svg.namedview.add_guide(
                        (l_x + pa, height - pa), (0, -1), "Puzzle guide bottom"
                    ).set("id", "guide_bottom"),
                )
            )
            guides.append(
                (
                    svg.namedview.add_guide(
                        (l_x + width / 2, height / 2),
                        (1, 0),
                        "Puzzle guide center",
                    ).set("id", "guide_center"),
                )
            )
            guides.append(
                svg.namedview.add_guide((r_x - pa, pa), (0, -1), "Guide top").set(
                    "id", f"{page_id}_guide_top"
                )
            )

        if page_id == "instructions":
            guides.append(
                (
                    svg.namedview.add_guide(
                        (l_x + pa, 3 * pa), (0, -1), "Instructions guide title"
                    ).set("id", "guide_title"),
                )
            )

            guides.append(
                (
                    svg.namedview.add_guide(
                        (r_x - 2.5 * pa, 5 * pa), (0, -1), "Instructions guide sequence"
                    ).set("id", "guide_sequence"),
                )
            )

        if page_id == "stats":
            guides.append(
                (
                    svg.namedview.add_guide(
                        (l_x + pa, 3 * pa), (0, -1), "Stats guide summary"
                    ).set("id", "guide_summary"),
                )
            )
            guides.append(
                (
                    svg.namedview.add_guide(
                        (l_x + pa, 15 * pa), (0, -1), "Stats guide histogram"
                    ).set("id", "guide_histogram"),
                )
            )
            guides.append(
                (
                    svg.namedview.add_guide(
                        (l_x + pa, 7 * pa), (0, -1), "Stats guide connections"
                    ).set("id", "guide_connections"),
                )
            )

    # Remove pages that are not in the pages dictionary
    for page in svg.namedview.get_pages():
        page: Page
        if page.get("id") is not None and page.get("id") not in pages.keys():
            page.delete()

    manage_layers(self, layers)
    return layers, pages, guides, paper


def manage_layers(self, layers):
    layers_to_remove = [layer["id"] for layer in layers.values() if layer["remove"]]
    layers_to_create = [layer["id"] for layer in layers.values() if layer["create"]]

    all_layers = self.svg.xpath('//svg:g[@inkscape:groupmode="layer"]')
    for layer in all_layers:
        if layer.get("inkscape:label") in layers_to_remove:
            layer.delete()

    for layer in layers_to_create:
        new_layer = self.svg.add(Layer())
        new_layer.set("id", layer)
        new_layer.set("inkscape:label", layer)
