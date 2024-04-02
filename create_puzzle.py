# Import required modules
import json
import math
import random

from inkex import (
    NSS,
    AbortExtension,
    Boolean,
    Circle,
    EffectExtension,
    Group,
    Guide,
    Layer,
    PathElement,
    Rectangle,
    Style,
    TextElement,
    Tspan,
)
from inkex.localization import inkex_gettext
from inkex.paths import Path

from CentroidPlotter import CentroidPlotter


# Create a class named NumberDots that inherits from inkex.EffectExtension
class CreatePuzzle(EffectExtension):
    """Replace the selection's nodes with numbered dots according to the options"""

    coding_sequence = (
        "abcdefghijklmnopqrstuvwxyz" + "1234567890" + "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    )
    fontsize = ""
    consolasFont = Style(
        {
            "font-family": "Consolas",
            "fill-opacity": "1.0",
            "fill": "#000000",
        }
    )
    plane_fill = "#808080"

    # Define method to add command-line arguments for the extension
    def add_arguments(self, pars):
        """Add command-line arguments for the extension"""
        pars.add_argument("--fontsize", default="8px", help="Size of node labels")
        pars.add_argument(
            "--page_margin",
            default="7mm 7mm 7mm 7mm",
            help="Page margin. Default is 7mm",
        )
        pars.add_argument(
            "--fontweight", default="normal", help="Weight of node labels"
        )
        pars.add_argument(
            "--start", type=int, default=1, help="First number in the sequence"
        )
        pars.add_argument("--tab", help="The selected UI-tab when OK was pressed")

        pars.add_argument(
            "--extreme_difficulty",
            type=Boolean,
            help="Enable extreme difficulty",
            default=False,
        )

        pars.add_argument(
            "--plot_centroids",
            type=Boolean,
            help="Plot centroids of filled elements",
            default=True,
        )

        pars.add_argument(
            "--centroids_layer",
            help="Layer to plot the centroids",
            default="centroids_layer",
        )

        pars.add_argument(
            "--solution_layer",
            help="Layer to plot the solution",
            default="solution_layer",
        )

        pars.add_argument(
            "--dots_layer",
            help="Layer to plot the dots",
            default="dots_layer",
        )

        pars.add_argument(
            "--instructions_layer",
            help="Layer to plot the instructions",
            default="instructions_layer",
        )

        pars.add_argument(
            "--stats_layer",
            help="Layer to plot the stats",
            default="stats_layer",
        )

        pars.add_argument(
            "--clearance",
            type=int,
            help="Clearance around the centroid",
            default=4,
        )

        pars.add_argument(
            "--fraction",
            type=int,
            help="Fraction of the bounding box to search",
            default=20,
        )

        pars.add_argument(
            "--plane_fill",
            help="Fill color of the plane",
            default="#808080",
            type=str,
        )

        pars.add_argument(
            "--plot_dots",
            type=Boolean,
            help="Plot dots",
            default=True,
        )

        pars.add_argument(
            "--plot_sequence",
            type=Boolean,
            help="Plot sequence",
            default=True,
        )

        pars.add_argument(
            "--plot_compact_sequence",
            type=Boolean,
            help="Plot compact sequence",
            default=False,
        )

        pars.add_argument(
            "--plot_reference_sequence",
            type=Boolean,
            help="Plot reference sequence",
            default=False,
        )

        pars.add_argument(
            "--minimal_distance",
            type=int,
            help="Minimal distance between dots",
            default=6,
        )

        pars.add_argument(
            "--replace_dots",
            type=Boolean,
            help="Replace the dots",
            default=True,
        )

        pars.add_argument(
            "--replace_centroids",
            type=Boolean,
            help="Replace the centroids",
            default=False,
        )

        pars.add_argument(
            "--replace_instructions",
            type=Boolean,
            help="Replace the text",
            default=True,
        )

        pars.add_argument(
            "--title",
            type=str,
            help="Title of the puzzle",
            default="",
        )

        pars.add_argument(
            "--subtitle",
            type=str,
            help="Subtitle of the puzzle",
            default="",
        )

        pars.add_argument(
            "--plot_footer",
            type=Boolean,
            help="Add footer",
            default=False,
        )

        pars.add_argument(
            "--copyright_text",
            type=str,
            help="Text for the copyright",
            default="Copyright © Polydot Puzzles 2024",
        )

    # Define the main effect method
    def effect(self):
        so = self.options  # shorthand for self.options
        self.consolasFont["font-weight"] = so.fontweight
        self.consolasFont["font-size"] = self.svg.unittouu(so.fontsize)
        self.fontsize = self.svg.unittouu(so.fontsize)
        paper_size = self.get_paper_size_info(self.svg)
        source_for_puzzle = self.get_selected_elements()
        # Clean up defs from previous runs
        self.svg.defs.clear()

        # Create layers for puzzle planes, dots, and text
        layers = {
            "solution_layer": {
                "id": so.solution_layer,
                "remove": False,
                "create": True,
            },
            "instructions_layer": {
                "id": so.instructions_layer,
                "remove": so.replace_instructions,
                "create": True,
            },
            "stats_layer": {
                "id": so.stats_layer,
                "remove": True,
                "create": True,
            },
            "dots_layer": {
                "id": so.dots_layer,
                "remove": so.replace_dots,
                "create": True,
            },
            "centroids_layer": {
                "id": so.centroids_layer,
                "remove": so.replace_centroids,
                "create": True,
            },
        }
        self.layers = layers
        self.manage_layers(layers)

        # Create a mapping of letter IDs, numbers, and coordinates
        # Also check for collisions and calculate distances
        dot_connections = self.create_mapping(source_for_puzzle)
        collisions, sorted_dots, all_distances = self.check_density(
            dot_connections, so.minimal_distance
        )
        avg_distance, lowest_distance, highest_distance = self.evaluate_distances(
            sorted_dots
        )
        compact_mapping = self.compress_mapping(dot_connections)
        planes = self.count_planes(layers["centroids_layer"]["id"])

        self.annotate_source_page("puzzle_page", "Puzzle", so.page_margin)
        self.prepend_instructions_page(
            "puzzle_instructions", "Instructions", so.page_margin
        )

        left_guide: Guide = self.svg.getElementById("sequence_guide_left")
        x_guide, y_guide = left_guide.position

        self.process_puzzle_path(source_for_puzzle, layers["solution_layer"]["id"])

        # Plot the Puzzle Dots and Centroids
        if so.plot_dots:
            self.plot_puzzle_dots(
                dot_connections, collisions, layers["dots_layer"]["id"]
            )

        if so.plot_centroids:
            ca = CentroidPlotter(self.svg)
            ca.plot_puzzle_centroids(
                so.centroids_layer,
                so.solution_layer,
                so.clearance,
                so.fraction,
                so.plane_fill,
            )

        # Plot the Instructions
        if so.plot_sequence:
            sequenceElement = self.plot_letter_sequence(
                dot_connections,
                x_guide,
                y_guide + 150,
            )
            self.svg.getElementById(layers["instructions_layer"]["id"]).append(
                sequenceElement
            )

        # Add footer
        if so.plot_footer:
            self.plot_footer(
                so.copyright_text,
                layers["instructions_layer"]["id"],
                x_guide,
                y_guide + 1000,
                paper_size,
            )

        self.plot_title(
            so.title, layers["instructions_layer"]["id"], x_guide, y_guide + 100
        )
        self.plot_tagline(
            so.subtitle, layers["instructions_layer"]["id"], x_guide + 50, y_guide + 500
        )
        self.plot_difficulty_level(
            dot_connections,
            layers["instructions_layer"]["id"],
            x_guide + 500,
            y_guide + 100,
        )

        # Add the source image to the solution layer for reference
        images = self.document.xpath("//svg:image", namespaces=NSS)
        if images and len(images) > 0:
            source_image = images[0]
            source_image.set("id", "source_image")
            self.svg.getElementById(layers["solution_layer"]["id"]).append(source_image)

        # ADVANCED OPTIONS
        # Plot the sequence as pairs
        if so.extreme_difficulty:
            pairs = self.plot_random_sequence_pairs(dot_connections)
            self.svg.getElementById(layers["instructions_layer"]["id"]).append(pairs)
        # Plot the compact sequence
        if so.plot_compact_sequence:
            compact_sequence = self.plot_compact_mapping(compact_mapping)
            self.svg.getElementById(layers["instructions_layer"]["id"]).append(
                compact_sequence
            )
        # Plot the reference sequence
        if so.plot_reference_sequence:
            self.plot_reference_sequence(x_guide, y_guide)

        # Perform analysis and plot stats
        self.perform_analysis(
            dot_connections,
            collisions,
            sorted_dots,
            compact_mapping,
            lowest_distance,
            avg_distance,
            highest_distance,
            planes,
        )
        unique_dots = self.get_unique_dots(dot_connections)
        stats = f"{len(dot_connections)} steps, {len(unique_dots)} unique dots, {round(lowest_distance)} min {round(avg_distance)} avg {round(highest_distance)} max, {planes} planes"

        self.append_stats_page(
            "puzzle_stats",
            "Stats",
            so.page_margin,
            stats,
            all_distances,
        )

    def get_selected_elements(self):
        # Get the selected elements, source path, or first path in the document
        source_p: PathElement = self.svg.getElementById("source_path")
        fallback_p: PathElement = next(
            iter(self.document.xpath("//svg:path", namespaces=NSS)), None
        )
        selected_path = self.svg.selection.filter(PathElement)

        # If any paths are selected, use them; otherwise, fallback to source_p or fallback_p
        if selected_path:
            selected_elements = selected_path
        else:
            selected_elements = (
                [source_p]
                if source_p is not None
                else [fallback_p]
                if fallback_p is not None
                else []
            )

        if not selected_elements:
            raise AbortExtension(
                inkex_gettext("Please select at least one path object.")
            )
        if len(selected_elements) > 1:
            raise AbortExtension(inkex_gettext("Please select only one path object."))

        return selected_elements

    def perform_analysis(
        self,
        dot_connections,
        collisions,
        sorted_dots,
        compact_mapping,
        lowest_distance,
        avg_distance,
        highest_distance,
        planes,
    ):
        # Combine mappings and write data to a file
        current_file_name = self.svg.get("sodipodi:docname", "")  # Get doc name
        output_name = current_file_name.split(".")[0]  # Remove the file extension

        # Perform analysis and plot stats
        unique_dots = self.get_unique_dots(dot_connections)
        sequence = self.svg.getElementById("sequence_string_textbox_tspan").text
        mappings = {
            "collisions": collisions,
            "sorted_dots": sorted_dots,
            "dot_connections": dot_connections,
            "compact_mapping": compact_mapping,
            "sequence": sequence,
            "stats": f"{len(dot_connections)} steps, {len(unique_dots)} unique dots, {round(lowest_distance)} min {round(avg_distance)} avg {round(highest_distance)} max, {planes} planes",
        }

        # Write combined mappings to a single JSON file
        self.write_mappings_to_file(mappings, f"{output_name}_combined_mappings.json")

    def manage_layers(self, layers):
        layers_to_remove = [layer["id"] for layer in layers.values() if layer["remove"]]
        self.remove_layers(layers_to_remove)

        layers_to_create = [layer["id"] for layer in layers.values() if layer["create"]]
        self.create_layers(layers_to_create)

    def process_puzzle_path(self, selected_path, layer_id):
        for puzzle_path in selected_path:
            puzzle_path.set("id", "source_path")
            puzzle_path.style = Style(
                {
                    "stroke": "#000000",
                    "stroke-width": "0.1pt",
                    "fill": "none",
                }
            )
            layer = self.svg.getElementById(layer_id)
            layer.append(puzzle_path)

    def annotate_source_page(self, page_id, page_label, page_margin):
        first_page = self.document.xpath("//inkscape:page", namespaces=NSS)[0]
        first_page.set("id", page_id)
        first_page.set("inkscape:label", page_label)
        first_page.set("margin", page_margin)

    def prepend_instructions_page(self, page_id, page_label, page_margin):
        doc_width = self.svg.get("width")
        doc_height = self.svg.get("height")
        converted_width = self.svg.unittouu(doc_width)
        converted_height = self.svg.unittouu(doc_height)
        x_shift = -(converted_width + 20)

        newpage = self.svg.namedview.new_page(
            str(x_shift),
            str(0),
            str(converted_width),
            str(converted_height),
            page_label,
        )
        newpage.set("id", page_id)
        newpage.set("margin", page_margin)

        left_guide: Guide = self.svg.namedview.add_guide(
            (-(converted_width - 25), 0), (1, 0), "Sequence guide left"
        )
        left_guide.set("id", "sequence_guide_left")
        right_guide: Guide = self.svg.namedview.add_guide(
            (-100, 0), (1, 0), "Sequence guide right"
        )
        right_guide.set("id", "sequence_guide_right")

    def append_stats_page(self, page_id, page_label, page_margin, stats, all_distances):
        connections_str = self.svg.getElementById("sequence_string_textbox_tspan").text
        doc_width = self.svg.get("width")
        doc_height = self.svg.get("height")
        converted_width = self.svg.unittouu(doc_width)
        converted_height = self.svg.unittouu(doc_height)

        x_shift = converted_width + 20
        y_shift = 0

        newpage = self.svg.namedview.new_page(
            str(x_shift),
            str(-y_shift),
            str(converted_width),
            str(converted_height),
            page_label,
        )
        newpage.set("id", page_id)
        newpage.set("margin", page_margin)

        new_guide: Guide = self.svg.namedview.add_guide(
            ((converted_width + 100), 0), (1, 0), "Stats guide"
        )
        new_guide.set("id", "stats_guide")
        x_guide, y_guide = new_guide.position

        self.svg.getElementById(self.layers["stats_layer"]["id"]).append(
            self.add_text_in_rect(
                stats,
                "mapping_textbox",
                "mapping_rect",
                x_guide,
                y_guide + 50,
                width="698",
                height="1000",
                font_size="10px",
            )
        )

        self.make_histogram(all_distances, 10, x_guide, y_guide + 100)
        self.make_connections_histogram(connections_str, x_guide, y_guide + 350)

        return new_guide

    def make_histogram(self, distances, num_bins=10, x=0, y=0):
        # Find the minimum and maximum distances
        min_distance = min(distances)
        max_distance = max(distances)

        # Calculate the bin width
        bin_width = (max_distance - min_distance) / num_bins

        # Initialize distance bins
        distance_bins = {min_distance + i * bin_width: 0 for i in range(num_bins)}

        # Count occurrences within each bin
        for distance in distances:
            for bin_start, bin_end in distance_bins.items():
                if bin_start <= distance < bin_start + bin_width:
                    distance_bins[bin_start] += 1

        # Create a group for the histogram
        histogram_group = self.svg.add(Group())
        histogram_group.set("id", "histogram_group")

        # Append text elements for each bin to stats_layer
        y_pos = y
        for distance, count in sorted(distance_bins.items()):
            bin_width_text = f"{round(distance)} - {round(distance + bin_width)}"
            histogram_text = "|" * count

            self.svg.getElementById("histogram_group").append(
                self.add_text_in_rect(
                    f"{bin_width_text} {histogram_text}",
                    f"distance_textbox_{round(distance)}",  # Unique ID for each text element
                    f"distance_rect_{round(distance)}",  # Unique ID for each rectangle
                    x,
                    y_pos,
                    width="700",
                    height="1000",
                    font_size="8px",
                )
            )
            y_pos += 20  # Increase y coordinate for next appended element

            self.svg.getElementById(self.layers["stats_layer"]["id"]).append(
                histogram_group
            )

    def make_connections_histogram(self, connections_str, x=0, y=0, max_repeat=2):
        text_element = TextElement(
            x="",
            y="",
            id="connections_textbox",
        )
        text_element.style = Style(
            {
                "font-family": "Consolas",
                "font-size": "10pt",
            }
        )
        connections_count = {}

        # Split the sequence into individual connections
        connections = connections_str.split()
        singular_connections = 0
        repeating_connections = 0

        # Iterate over each connection
        for i in range(len(connections) - 1):
            connection = sorted([connections[i], connections[i + 1]])
            connection = " ".join(connection)

            # Count the occurrence of the connection
            connections_count[connection] = connections_count.get(connection, 0) + 1

            if connections_count[connection] == 1:
                singular_connections += 1

        # Sort connections by totals in descending order
        sorted_connections = sorted(
            connections_count.items(), key=lambda x: x[1], reverse=True
        )

        # Plotting connections after all iterations
        for connection, count in sorted_connections:
            if count > max_repeat:
                repeating_connections += 1
                text_element.append(
                    Tspan(
                        f"{connection} : {count * '•'}\n",
                        x=str(x),
                        y=str(y + repeating_connections * 20),
                        id=f"connection_{connection}",
                    )
                )
                self.mark_connection(connection)

        text_element.append(
            Tspan(
                f"Repeating connections (above {max_repeat}): {repeating_connections}\n",
                x=str(x),
                y=str(y + (repeating_connections + 1) * 20),
                id=f"repeating_connections_{repeating_connections}",
                font_weight="bold",
            )
        )
        text_element.append(
            Tspan(
                f"Singular connections: {singular_connections}\n",
                x=str(x),
                y=str(y),
                id=f"singular_connections_{singular_connections}",
                font_weight="bold",
            )
        )

        self.svg.getElementById(self.layers["stats_layer"]["id"]).append(text_element)

    def mark_connection(self, connection, color="#ff0000"):
        left_dot, right_dot = connection.split()
        markStyle = Style({"stroke": color, "stroke-width": "2pt"})
        self.svg.getElementById(f"black_dot_{left_dot}").style = markStyle
        self.svg.getElementById(f"black_dot_{right_dot}").style = markStyle

    def plot_title(self, title_field: str, layer_id, x, y):
        layer = self.svg.getElementById(layer_id)
        title_element = TextElement(x=str(x), y=str(y), id="title_textbox")

        if not title_field:
            docname = self.svg.get("sodipodi:docname", "").split(".")[0]
            # Parse the first two characters of the filename as the number of the puzzle
            title = f"Polydot {docname[:2]}"
        else:
            title = title_field

        title_element.text = title
        title_element.style = Style(
            {
                "font-family": "Consolas",
                "fill-opacity": "1.0",
                "fill": "#000000",
                "font-size": "16pt",
                "font-weight": "bold",
            }
        )
        layer.append(title_element)

    def plot_tagline(self, subtitle: str, layer_id, x, y):
        layer = self.svg.getElementById(layer_id)
        subtitle_element = TextElement(x=str(x), y=str(y), id="subtitle_textbox")
        subtitle_element.text = subtitle
        subtitle_element.style = Style(
            {
                "font-family": "Garamond",
                "fill-opacity": "1.0",
                "fill": "#000000",
                "font-size": "32pt",
                "font-weight": "bold",
                "font-style": "italic",
            }
        )
        layer.append(subtitle_element)

    def plot_footer(
        self,
        copyright_text: str,
        layer_id,
        x_guide,
        y_guide,
        paper_size="A4",
    ):
        layer = self.svg.getElementById(layer_id)
        footerText = TextElement(x=str(x_guide), y=str(y_guide), id="footer_textbox")
        footerText.text = copyright_text + " | " + paper_size
        footerText.style = Style(
            {
                "font-family": "Garamond",
                "fill-opacity": "1.0",
                "fill": "#000000",
                "font-size": "8pt",
            }
        )
        layer.append(footerText)

    def get_paper_size_info(self, svg):
        """Extracts dimensions from SVG and determines the paper size."""
        width_in_mm = round(float(svg.get("width").replace("mm", "")))
        height_in_mm = round(float(svg.get("height").replace("mm", "")))

        if (width_in_mm, height_in_mm) == (210, 297):
            return "A4"
        elif (width_in_mm, height_in_mm) == (216, 279):
            return "US Letter"
        else:
            return "Custom Size"

    def plot_difficulty_level(self, dot_connections, layer_id, x, y):
        # Calculate the difficulty level based on the number of steps
        level = (len(dot_connections) // 200) + 1
        grouped_brains = Group()
        grouped_brains.set("id", "grouped_brains")

        self.svg.getElementById(layer_id).append(grouped_brains)
        layer = self.svg.getElementById(layer_id)

        for i in range(5):
            brain_character = PathElement(id=f"brain_character_{i}")
            brain_character.path = Path(
                "m 15.3568 5.4864 q 0.2066 -0.2066 0.2066 -0.5016 q 0 -0.2949 -0.2066 -0.5016 q -0.4719 -0.4719 -1.1211 -0.7474 q -0.6393 -0.285 -1.367 -0.285 q -0.7276 0 -1.3666 0.285 q -0.6393 0.2751 -1.1112 0.7474 q -0.2066 0.2066 -0.2066 0.5016 q 0 0.2949 0.2066 0.5016 q 0.2066 0.2066 0.4917 0.2066 q 0.2949 0 0.5115 -0.2066 q 0.6097 -0.6097 1.475 -0.6097 q 0.8654 0 1.4849 0.6097 q 0.2066 0.2066 0.5016 0.2066 q 0.2949 0 0.5016 -0.2066 z m -8.2304 -0.6785 q 0.2557 -0.1477 0.5408 -0.0689 q 0.285 0.0689 0.4327 0.3246 q 0.1477 0.2557 0.0689 0.5408 q -0.0689 0.2755 -0.3246 0.4327 q -0.7569 0.4327 -1.3472 1.0914 q -0.5899 0.6489 -0.9537 1.4454 q -0.3737 0.8159 -0.4719 1.711 q -0.0304 0.2949 -0.2656 0.4818 q -0.2261 0.177 -0.521 0.1477 q -0.285 -0.0304 -0.4719 -0.2557 q -0.1869 -0.2359 -0.1477 -0.5309 q 0.118 -1.1211 0.5899 -2.1437 q 0.4521 -0.9933 1.1896 -1.8092 l 0.0023 0.0004 q 0.7375 -0.8159 1.6813 -1.3666 z m 10.7082 7.9157 q 0 0.4426 -0.3147 0.7569 q -0.3147 0.3048 -0.7474 0.3048 l -2.7324 0.0013 q 0.2458 -0.521 0.2458 -1.0618 q 0 -0.2949 -0.2066 -0.5016 q -0.2066 -0.2066 -0.5016 -0.2066 q -0.285 0 -0.5016 0.2066 q -0.2066 0.2066 -0.2066 0.5016 q 0 0.4426 -0.3147 0.7569 q -0.3048 0.3048 -0.7474 0.3048 h -1.5424 q -0.2949 0 -0.5016 0.2066 q -0.2066 0.2066 -0.2066 0.5016 q 0 0.2949 0.2066 0.5016 q 0.2066 0.2066 0.5016 0.2066 l 4.3764 -0.0008 q 0.4426 0 0.7474 0.3147 q 0.3147 0.3147 0.3246 0.7474 q 0 0.2949 0.2066 0.5111 q 0.2066 0.2066 0.5016 0.2066 q 0.285 0 0.4917 -0.2066 q 0.2162 -0.2162 0.2162 -0.5111 q 0 -0.5507 -0.2557 -1.0717 q 0.6587 -0.019 1.1995 -0.3539 q 0.5408 -0.344 0.8555 -0.8947 q 0.3246 -0.5507 0.3246 -1.2193 q 0 -0.2949 -0.2066 -0.5016 q -0.2066 -0.2066 -0.5016 -0.2066 q -0.2949 0 -0.5016 0.2066 q -0.2066 0.2066 -0.2066 0.5016 z m 5.6639 -0.5606 l 0.0023 1.6235 q 0 0.0304 0 0.0788 q -0.0114 0.0392 -0.0114 0.0689 q 0.0114 0.059 0.0114 0.0788 q 0 0.0887 0 0.1279 q 0 0.0689 -0.0392 0.2066 l -0.0027 0.0023 q -0.0304 0.2755 -0.0788 0.5408 q -0.0392 0.2656 -0.118 0.521 q -0.3147 1.0621 -1.0028 1.9173 q -0.6785 0.8456 -1.6421 1.3864 q -0.9537 0.5408 -2.0748 0.6884 l 0.0034 1.8876 q 0 0.3539 -0.3345 0.4917 q -0.3246 0.1378 -0.5705 -0.118 l -2.2126 -2.2027 l -5.0378 -0.0015 q -1.0914 0 -2.0257 -0.462 q -0.9244 -0.462 -1.5732 -1.2585 q -0.6393 -0.8064 -0.8753 -1.829 l -0.884 -0.0013 q -1.1603 0 -2.114 -0.5606 q -0.9537 -0.5705 -1.5241 -1.5241 q -0.5705 -0.9636 -0.5705 -2.1239 q 0 -2.2126 0.8258 -4.1397 q 0.8357 -1.937 2.3009 -3.4022 q 1.4652 -1.4652 3.3923 -2.291 q 1.937 -0.8357 4.1496 -0.8357 l 0.8772 0.0011 q 2.1437 0 4.0412 0.7573 q 1.8978 0.7474 3.3824 2.0847 q 1.4945 1.3373 2.4386 3.1271 q 0.9537 1.7898 1.19 3.8741 q 0.0392 0.3147 0.059 0.6393 q 0.019 0.3147 0.019 0.6489 z m -1.593 2.8416 q 0.1477 -0.5016 0.1671 -1.0717 q -0.0392 -0.7474 -0.344 -1.3963 q -0.2949 -0.6587 -0.7866 -1.1504 q -0.5309 -0.5309 -1.2391 -0.8357 q -0.7078 -0.3048 -1.5142 -0.3048 q -0.0689 0 -0.1967 -0.0392 l -0.0091 0.0027 q -0.5998 0.5115 -1.3666 0.8064 q -0.7569 0.2949 -1.6124 0.2949 q -0.2949 0 -0.5111 -0.2066 q -0.2066 -0.2066 -0.2066 -0.5016 q 0 -0.2949 0.2066 -0.5016 q 0.2162 -0.2066 0.5111 -0.2066 q 0.6587 0 1.2391 -0.2458 q 0.58 -0.2557 1.0127 -0.6884 q 0.4327 -0.4327 0.6785 -1.0127 q 0.2557 -0.58 0.2557 -1.2486 q 0 -0.285 0.2066 -0.4917 q 0.2066 -0.2162 0.5016 -0.2162 q 0.2949 0 0.5016 0.2162 q 0.2066 0.2066 0.2066 0.4917 q 0 1.1801 -0.5606 2.2027 q 0.8258 0.1378 1.5534 0.5115 q 0.7276 0.3737 1.3076 0.9343 q -0.3246 -1.6813 -1.1801 -3.1172 q -0.8555 -1.4454 -2.1338 -2.5174 q -1.2783 -1.0717 -2.8614 -1.6619 q -1.5831 -0.5998 -3.363 -0.5998 l -0.878 -0.0011 q -1.9173 0 -3.599 0.7276 q -1.6813 0.7276 -2.9402 1.9861 q -1.2585 1.2585 -1.9861 2.9402 q -0.7276 1.6813 -0.7276 3.599 q 0 0.5804 0.2162 1.0914 q 0.2261 0.5016 0.5998 0.8848 q 0.3836 0.3836 0.8848 0.5998 q 0.5115 0.2162 1.0914 0.2162 l 0.8095 -0.0005 q 0.118 -0.7866 0.462 -1.4849 q 0.344 -0.6979 0.8753 -1.2486 q -0.0788 -0.4327 -0.3935 -0.7474 q -0.2066 -0.2066 -0.2066 -0.5016 q 0 -0.2949 0.2066 -0.5016 q 0.2162 -0.2066 0.5016 -0.2066 q 0.2949 0 0.5016 0.2066 q 0.3539 0.3539 0.58 0.8456 q 0.5309 -0.2949 1.1306 -0.4521 q 0.5998 -0.1572 1.2486 -0.1572 q 0.2949 0 0.5016 0.2066 q 0.2066 0.2066 0.2066 0.5016 q 0 0.2949 -0.2066 0.5016 q -0.2066 0.2066 -0.5016 0.2066 q -0.7375 0 -1.3864 0.285 q -0.6393 0.2751 -1.1211 0.7569 q -0.462 0.462 -0.7375 1.0816 q -0.2656 0.6097 -0.285 1.3076 l -0.0023 0.051 q 0.0788 0.8064 0.5111 1.4652 q 0.4426 0.6587 1.1306 1.0522 q 0.6983 0.3836 1.534 0.3836 l 7.4457 -0.0012 q 0.9636 0 1.7898 -0.3935 q 0.8258 -0.3935 1.4161 -1.0816 q 0.5998 -0.6884 0.8654 -1.5633 z"
            ).translate(45 + (i * 25) + x, y)

            height = brain_character.path.bounding_box().height
            brain_character.path = Path(brain_character.path).translate(0, -height)

            brain_character.style = (
                Style({"fill": "#d3d3d3"}) if i > level else Style({"fill": "#000000"})
            )
            grouped_brains.append(brain_character)

        layer.append(grouped_brains)

    def remove_layers(self, layerIds: list):
        """Remove layers for puzzle planes, dots, and text"""

        all_layers = self.svg.xpath('//svg:g[@inkscape:groupmode="layer"]')
        for layer in all_layers:
            if layer.get("inkscape:label") in layerIds:
                layer.delete()

    def create_layers(self, layer_ids: list):
        """Create layers for puzzle planes, dots, and text"""
        for layer in layer_ids:
            new_layer = self.svg.add(Layer())
            new_layer.set("id", layer)
            new_layer.set("inkscape:label", layer)

    def check_density(self, dots: list, minimal_distance: int):
        for dot in dots:
            dot["has_collision"] = False
            for other_dot in dots:
                if dot["letter_label"] != other_dot["letter_label"]:
                    distance = math.sqrt(
                        (dot["x"] - other_dot["x"]) ** 2
                        + (dot["y"] - other_dot["y"]) ** 2
                    )
                    dot["distance"] = round(distance, 2)
                    dot["collides_with"] = other_dot["letter_label"]
                    if distance <= minimal_distance:
                        dot["has_collision"] = True
                        break
        sorted_dots = sorted(dots, key=lambda k: k["distance"])
        colliding_dots = [dot for dot in sorted_dots if dot["has_collision"]]
        all_distances = [dot["distance"] for dot in sorted_dots]
        return colliding_dots, sorted_dots, all_distances

    def evaluate_distances(self, sorted_distances):
        num_distances = len(sorted_distances)
        total_distance = sum(distance["distance"] for distance in sorted_distances)
        avg_distance = total_distance / num_distances if num_distances > 0 else 0
        lowest_distance = sorted_distances[0]["distance"]
        highest_distance = sorted_distances[-1]["distance"]

        return avg_distance, lowest_distance, highest_distance

    def count_planes(self, puzzle_planes_id):
        processed_planes = self.svg.getElementById(puzzle_planes_id)
        xpath_query = f".//*[@style and contains(@style, 'fill:{self.plane_fill}')]"
        red_planes = self.svg.xpath(xpath_query)
        number_of_red_planes = len(red_planes) if red_planes is not None else 0
        number_of_planes = len(processed_planes) if processed_planes is not None else 0

        return number_of_planes or number_of_red_planes

    def createRootGroup(self, id: str):
        root_group: Group = self.svg.add(Group())
        root_group.set("id", id)
        root_group.transform = "translate(0, 0)"
        return root_group

    def plot_reference_sequence(self, x_guide, y_guide, width="698", height="113"):
        """Create a reference sequence of the letters"""
        reference_sequence_group = self.createRootGroup("reference_sequence")

        # Calculate the maximum number based on the length of coding_sequence
        max_number = len(self.coding_sequence) ** 2

        # Create a rectangle element
        rect = Rectangle(
            x_guide,
            y_guide,
            width,
            height,
            id="reference_sequence_rect",
        )

        # Add the rectangle to the <defs> section
        self.svg.defs.append(rect)

        # Create a text element inside the rectangle
        text_element = TextElement(
            x=x_guide, y=y_guide, id="reference_sequence_textbox"
        )
        text_element.set("shape-inside", f"url(#{rect.get('id')})")

        text_element.style = self.consolasFont
        text_element.style["fill"] = "#000000"

        # Add the text element to the document
        reference_sequence_group.append(text_element)

        # Add the reference sequence
        reference_sequence = ""
        for i in range(1, max_number + 1):
            reference_sequence += self.get_letter_id_from_number(i) + " "

        reference_sequence_group.append(
            self.add_text_in_rect(
                reference_sequence,
                "reference_sequence_textbox",
                "reference_sequence_rect",
            )
        )

        return reference_sequence

    def get_unique_dots(self, mapping: list):
        """Get the unique dots from the mapping"""
        unique_dots = []

        for entry in mapping:
            x = entry["x"]
            y = entry["y"]
            letter_label = entry["letter_label"]

            # Check if the dot is already in unique_dots
            exists = False
            for dot in unique_dots:
                if (
                    dot["x"] == x
                    and dot["y"] == y
                    and dot["letter_label"] == letter_label
                ):
                    exists = True
                    break

            # If it's not in unique_dots, add it
            if not exists:
                unique_dots.append({"x": x, "y": y, "letter_label": letter_label})

        return unique_dots

    def plot_puzzle_dots(self, mapping: list, collisions: list, layer_id):
        """Plot the mapping to the canvas"""
        unique_dots = []

        # Remove duplicate dots
        for entry in mapping:
            x = entry["x"]
            y = entry["y"]
            letter_element = entry["letter_label"]

            # Check if the dot is already in unique_dots
            exists = False
            for dot in unique_dots:
                if (
                    dot["x"] == x
                    and dot["y"] == y
                    and dot["letter_label"] == letter_element
                ):
                    exists = True
                    break

            # If it's not in unique_dots, add it
            if not exists:
                unique_dots.append({"x": x, "y": y, "letter_label": letter_element})

        for step in unique_dots:
            x_center = step["x"]  # Center of the circle
            y_center = step["y"]

            # Verify is the dot is colliding with another dot
            collision_exists = False
            for collision in collisions:
                if collision["letter_label"] == step["letter_label"]:
                    collision_exists = True
                    break

            # Add the text label
            text_element_with_label = self.svg.getElementById(layer_id).add(
                TextElement(x=str(x_center), y=str(y_center))
            )
            # make the text center horitzontally
            text_element_with_label.text = f"{step['letter_label']}"
            text_element_with_label.set("text-anchor", "middle")
            text_element_with_label.set("dominant-baseline", "middle")
            text_element_with_label.set("id", f"text_label_{step['letter_label']}")
            text_element_with_label.style = self.consolasFont
            text_element_with_label.set("letter-spacing", "1px")
            #  make red when collision
            if collision_exists:
                text_element_with_label.style["fill"] = "#ff0000"

            # Add the dot to the canvas
            black_circle = self.createCircle(
                x_center,
                y_center,
                0.7,
                fill="#000000",
                id=f"black_dot_{step['letter_label']}",
            )

            current_dot_group = self.svg.getElementById(layer_id).add(Group())
            current_dot_group.set("id", f"{step['letter_label']}")
            current_dot_group.append(black_circle)
            current_dot_group.append(text_element_with_label)

    def createCircle(self, x: int, y: int, radius: int, fill="#ffffff", id=""):
        """Create a circle element"""
        circle = Circle(cx=str(x), cy=str(y), r=str(radius))
        circle.style = Style(
            {
                "fill": fill,
            }
        )
        circle.set("id", id)
        return circle

    def plot_letter_sequence(self, mapping: list, x, y):
        """Plot the mapping to the canvas"""
        sequence_string = " ".join(
            item["letter_label"] + ("  " if (index + 1) % 5 == 0 and index != 0 else "")
            for index, item in enumerate(mapping)
        )

        return self.add_text_in_rect(
            sequence_string,
            "sequence_string_textbox",
            "sequence_string_rect",
            x,
            y,
        )

    def plot_random_sequence_pairs(self, mapping: list):
        """Plot the mapping to the canvas as a sequence of shuffled pairs"""

        pairs = [
            f"{mapping[index - 1]['letter_label']}-{item['letter_label']}"
            for index, item in enumerate(mapping)
            if index != 0
        ]

        return self.add_text_in_rect(
            " ".join(random.shuffle(pairs)),
            "sequence_string_textbox_extreme",
            "sequence_string_rect_extreme",
        )

    def plot_compact_mapping(self, mapping: list):
        """Plot the mapping to the canvas"""

        return self.add_text_in_rect(
            " ".join(mapping),
            "compact_sequence_string_textbox",
            "compact_sequence_string_rect",
        )

    def create_mapping(self, elements: list):
        """Create a mapping of letter IDs, numbers, and coordinates"""
        result_mapping = []
        coord_to_label = {}  # Dictionary for efficient coordinate lookup
        dot_number = self.options.start - 1

        for pathElement in elements:
            path: Path = pathElement.path
            path_trans_applied = path.transform(pathElement.composed_transform())

            previous_point = None

            for _, (x, y) in enumerate(path_trans_applied.end_points):
                x_rounded = round(x)
                y_rounded = round(y)
                current_point = (x_rounded, y_rounded)

                if current_point in coord_to_label:
                    # Coordinate already exists, use the same label
                    letter_label = coord_to_label[current_point]
                else:
                    # New coordinate, generate a new label and store it
                    next_unique_dot_number = len(coord_to_label) + 1
                    letter_label = self.get_letter_id_from_number(
                        next_unique_dot_number
                    )
                    coord_to_label[current_point] = letter_label

                # Increment the dot number if the current point is different from the previous point
                if current_point != previous_point:
                    dot_number += 1

                # Add the mapping to the result
                result_mapping.append(
                    {
                        "x": x_rounded,
                        "y": y_rounded,
                        "dot_number": dot_number,
                        "letter_label": letter_label,
                    }
                )

        return result_mapping

    def compress_mapping(self, dot_connections: list):
        """Compress the mapping by filtering out dot numbers of which letters are already in the sequence; return a list of dot connections like: "Am" -> "AA" """

        compressed_mapping = []

        for i in range(
            1, len(dot_connections)
        ):  # Start from 1 to avoid negative indexing
            current_dot_label = dot_connections[i]["letter_label"]
            for j in range(i):
                previous_dot_label = dot_connections[j]["letter_label"]
                if current_dot_label == previous_dot_label:
                    # If the current dot label is the same as a previous dot label, add the mapping
                    compressed_mapping.append(
                        f"{dot_connections[i-1]['letter_label']}:{current_dot_label}"
                    )
                    break  # Stop the inner loop once a match is found

        return compressed_mapping

    def write_mappings_to_file(self, combined_mapping, filename):
        """Write the combined mappings to a file"""
        current_folder = self.svg_path()
        with open(f"{current_folder}/{filename}", "w") as f:
            json.dump(combined_mapping, f)

    # Define a method to set the style of dots based on their position
    def set_dot_style(self, circle, dot_number: int):
        circle.style = Style(
            {
                "stroke": "#ffffff",
                "stroke-width": "0.1pt",
                "fill": "#ffffff",
            }
        )
        circle.set("id", f"dot_{dot_number}")
        return circle

    # Define a method to add text labels
    def add_text(
        self, x: int, y: int, text: str, id: str, color: str = "#000"
    ) -> TextElement:
        """Add a text label at the given location"""

        elem = TextElement(x=str(x), y=str(y))
        elem.text = str(text)
        elem.set("id", id)
        elem.style = self.consolasFont
        elem.style["fill"] = color
        return elem

    def add_text_in_rect(
        self,
        text_string: str,
        text_id: str,
        rect_id: str,
        x,
        y,
        width=675,
        height=900,
        color: str = "#000",
        font_size: str = "11pt",
    ):
        """Add a text element inside a rectangle at the given location with specified properties"""

        # Create a rectangle element
        rect = Rectangle(
            x=str(x), y=str(y), width=str(width), height=str(height), id=rect_id
        )

        # Add the rectangle to the <defs> section
        self.svg.defs.append(rect)

        # Create a text element inside the rectangle
        text_element = TextElement(x=str(x), y=str(y), id=text_id)
        text_element.set(
            "shape-inside", f"url(#{rect_id})"
        )  # Reference the rectangle as the shape inside the text
        text_element.style = self.consolasFont
        text_element.style["fill"] = color
        text_element.style["font-size"] = font_size
        tspan = Tspan(text_string)
        tspan.set_id(f"{text_id}_tspan")
        tspan.text = text_string
        text_element.append(tspan)

        # Add the text element to the document
        self.svg.append(text_element)

        return text_element

    # Define a method to generate letter IDs
    # The max number of dots can be 2074 (52*52)
    def get_letter_id_from_number(self, number):
        """Generate letter IDs from 1 to 2074"""

        # Validate coding_sequence
        if not self.coding_sequence or len(self.coding_sequence) < 2:
            raise ValueError(
                "Invalid coding_sequence. It should contain at least two characters."
            )

        # Calculate the maximum number based on the length of coding_sequence
        max_number = len(self.coding_sequence) ** 2

        if not 1 <= number <= max_number:
            raise ValueError(
                f"Number {number} is out of range. Should be between 1 and {max_number}."
            )

        letter_id_array = [letter for letter in self.coding_sequence]

        first_letter_index = (number - 1) // len(letter_id_array)
        second_letter_index = (number - 1) % len(letter_id_array)

        first_letter = letter_id_array[first_letter_index % len(letter_id_array)]
        second_letter = letter_id_array[second_letter_index]

        return f"{first_letter}{second_letter}"

    def get_number_from_letter_id(self, letter_id):
        """Retrieve the number from letter IDs"""
        letter_id_array = [letter for letter in self.coding_sequence]

        first_letter_index = letter_id_array.index(letter_id[0])
        second_letter_index = letter_id_array.index(letter_id[1])

        number = first_letter_index * len(letter_id_array) + second_letter_index + 1

        return number

    def get_letter_id_from_coordinates(self, x, y, solution_table):
        """Retrieve the letter ID from coordinates"""
        X = math.ceil(x)
        Y = math.ceil(y)
        for item in solution_table:
            if item["x"] == X and item["y"] == Y:
                return item["letter_label"]
        return None


# Entry point of the script
if __name__ == "__main__":
    CreatePuzzle().run()
