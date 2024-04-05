# Import required modules
import json
import math
import random

import inkex
from inkex import (
    NSS,
    AbortExtension,
    Circle,
    EffectExtension,
    Group,
    Guide,
    Layer,
    Page,
    PathElement,
    Rectangle,
    Style,
    TextElement,
    Tspan,
)
from inkex.localization import inkex_gettext
from inkex.paths import Path

from CentroidPlotter import CentroidPlotter
from document_setup import setup
from extension_args import add_arguments


# Create a class named NumberDots that inherits from inkex.EffectExtension
class CreatePuzzle(EffectExtension):
    """Replace the selection's nodes with numbered dots according to the options"""

    coding_sequence = (
        "abcdefghijklmnopqrstuvwxyz" + "1234567890" + "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    )
    fontConsolas = Style(
        {
            "font-family": "Consolas",
            "fill-opacity": "1.0",
            "fill": "#000000",
        }
    )
    fontGaramond = Style(
        {
            "font-family": "Garamond",
            "fill-opacity": "1.0",
            "fill": "#000000",
        }
    )

    # Define method to add command-line arguments for the extension
    def add_arguments(self, pars):
        add_arguments(pars)

    # Define the main effect method
    def effect(self):
        so = self.options  # shorthand for self.options
        self.fontConsolas["font-weight"] = so.fontweight
        self.fontConsolas["font-size"] = so.fontsize

        # Clean up defs from previous runs
        self.svg.defs.clear()
        layers, pages, guides, paper = setup(self, so)
        self.layers = layers
        self.pages = pages
        self.guides = guides
        self.paper = paper

        source_path = self.get_selected_elements()
        processed_path, processed_planes = self.process_puzzle_path(
            source_path, so.plane_fill
        )

        # Create a mapping of letter IDs, numbers, and coordinates
        # Also check for collisions and calculate distances
        dot_connections = self.create_mapping(processed_path)
        collisions, sorted_dots, all_distances = self.check_density(
            dot_connections, so.minimal_distance
        )
        avg_distance, lowest_distance, highest_distance = self.evaluate_distances(
            sorted_dots
        )
        planes = self.count_planes("centroids_layer", so.plane_fill)

        # Plot the Puzzle Dots and Centroids
        if so.plot_dots:
            self.plot_puzzle_dots(
                dot_connections,
                collisions,
                "dots_layer",
            )

        if so.plot_centroids:
            ca = CentroidPlotter(self.svg)
            ca.plot_puzzle_centroids(
                "centroids_layer",
                "solution_layer",
                so.clearance,
                so.fraction,
                so.plane_fill,
            )

        # Plot the Instructions
        if so.plot_sequence:
            self.plot_letter_sequence(dot_connections)

        # Add footer
        if so.plot_footer:
            paper_size = self.get_paper_size_info(self.svg)
            self.plot_footer(
                so.copyright_text,
                paper_size,
            )

        self.plot_title(
            so.title,
            so.subtitle,
        )
        self.plot_caption(so.caption)
        self.plot_difficulty_level(dot_connections)

        # # Add the source image to the solution layer for reference
        # images = self.document.xpath("//svg:image", namespaces=NSS)
        # if images and len(images) > 0:
        #     source_image = images[0]
        #     source_image.set("id", "source_image")
        #     self.svg.getElementById(layers["solution_layer"]["id"]).append(source_image)

        # ADVANCED OPTIONS

        if so.plot_reference_sequence:
            self.plot_reference_sequence()

        # Perform analysis and plot stats
        self.perform_analysis(
            dot_connections,
            collisions,
            sorted_dots,
            lowest_distance,
            avg_distance,
            highest_distance,
            planes,
        )

    def plot_caption(self, caption):
        layer = self.svg.getElementById("instructions_layer")
        bx, by = self.svg.getElementById("guide_bottom").position
        rx, _ = self.svg.getElementById("puzzle_guide_right").position
        caption_element = TextElement(id="caption_textbox")
        caption_element.style = Style(
            {
                "font-family": "Garamond",
                "fill-opacity": "1.0",
                "fill": "#000000",
                "font-size": "16pt",
                "font-style": "italic",
                "text-align": "center",
                "text-anchor": "middle",
            }
        )
        # One line of text is approximately 40 units in height and 100 characters in width
        height = len(caption) / 100 * 40
        rect = Rectangle(
            width=f"{rx - bx}",
            height=f"{height}",
            id="caption_rect",
        )
        bbox = rect.bounding_box().height
        rect.set("x", str(bx))
        rect.set("y", str(by - bbox))
        caption_element.set("x", str(bx))
        caption_element.set("y", str(by - bbox))

        self.svg.defs.append(rect)
        caption_element.set("shape-inside", f"url(#{rect.get('id')})")
        ts = Tspan(caption)
        caption_element.append(ts)
        layer.append(caption_element)

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
        stats = f"{len(dot_connections)} steps, {len(unique_dots)} unique dots, {round(lowest_distance)} min {round(avg_distance)} avg {round(highest_distance)} max, {planes} planes"
        mappings = {
            "collisions": collisions,
            "sorted_dots": sorted_dots,
            "dot_connections": dot_connections,
            "sequence": sequence,
            "stats": stats,
        }
        self.append_stats_page(stats, sorted_dots)

        # Write combined mappings to a single JSON file
        self.write_mappings_to_file(mappings, f"{output_name}_combined_mappings.json")

    def process_puzzle_path(self, selected_path, rgb_color):
        hex_color = "#{:02x}{:02x}{:02x}".format(*inkex.Color(rgb_color).to_rgb())
        xpath_query = f".//*[@style and contains(@style, 'fill:{hex_color}')]"
        planes_to_color = self.svg.xpath(xpath_query, namespaces=inkex.NSS)
        # # move the planes_to_color with the puzzle_path
        # for plane in planes_to_color:
        #     inkex.debug(f"plane: {plane}")
        #     plane.transform = f"translate({100}, {100})"

        puzzle_path = selected_path[0]
        puzzle_path.set("id", "source_path")
        puzzle_path.style = Style(
            {
                "stroke": "#000000",
                "stroke-width": "0.1pt",
                "fill": "none",
            }
        )
        layer = self.svg.getElementById("solution_layer")
        layer.append(puzzle_path)
        # align to center of 'puzzle guide center'
        puzzle_path_center = puzzle_path.bounding_box().center
        guide: Guide = self.svg.getElementById("guide_center")
        x_guide, y_guide = guide.position
        dx = x_guide - puzzle_path_center[0]
        dy = y_guide - puzzle_path_center[1]
        puzzle_path.transform = f"translate({dx}, {dy})"

        for plane in planes_to_color:
            plane.transform = f"translate({dx}, {dy})"
            layer.append(plane)

        return selected_path, planes_to_color

    def annotate_source_page(self, page_id: str, page_label: str, page_margin: str):
        first_page: Page = self.document.xpath("//inkscape:page", namespaces=NSS)[0]
        first_page.set("id", page_id)
        first_page.set("inkscape:label", page_label)
        first_page.set("margin", page_margin)
        first_page.set("width", self.svg.get("width"))
        first_page.set("height", self.svg.get("height"))

    def append_stats_page(self, stats, sorted_dots):
        connections_str = self.svg.getElementById("sequence_string_textbox_tspan").text
        xl, y = self.svg.getElementById("guide_summary").position
        xr, _ = self.svg.getElementById("stats_guide_right").position
        width = xr - xl

        self.svg.getElementById("stats_layer").append(
            self.add_text_in_rect(
                stats,
                "mapping_textbox",
                "mapping_rect",
                x=str(xl),
                y=str(y),
                width=str(width),
                height="1000",
                font_size="6pt",
            )
        )

        self.make_histogram(sorted_dots, 10)
        self.make_connections_histogram(connections_str)

    def make_histogram(self, sorted_dots, num_bins=10):
        distances = []
        for i in range(len(sorted_dots) - 1):
            dot1 = sorted_dots[i]
            dot2 = sorted_dots[i + 1]
            distance = math.sqrt(
                (dot1["x"] - dot2["y"]) ** 2 + (dot1["y"] - dot2["y"]) ** 2
            )
            distances.append(distance)
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
        self.svg.getElementById("stats_layer").append(histogram_group)
        x, y = self.svg.getElementById("guide_histogram").position
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
                    font_size="6pt",
                )
            )
            y_pos += 20  # Increase y coordinate for next appended element

    def make_connections_histogram(self, connections_str, max_repeat=2):
        x, y = self.svg.getElementById("guide_connections").position
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

        self.svg.getElementById("stats_layer").append(text_element)

    def mark_connection(self, connection, color="#ff0000"):
        left_dot, right_dot = connection.split()
        markStyle = Style({"stroke": color, "stroke-width": "2pt"})

        self.svg.getElementById(f"black_dot_{left_dot}").style = markStyle
        self.svg.getElementById(f"black_dot_{right_dot}").style = markStyle

    def plot_title(self, title_field: str, subtitle: str):
        layer = self.svg.getElementById("instructions_layer")
        x, y = self.svg.getElementById("guide_title").position
        title_element = TextElement(x=str(x), y=str(y), id="title_textbox")
        layer.append(title_element)

        if not title_field:
            docname = self.svg.get("sodipodi:docname", "").split(".")[0]
            # Parse the first two characters of the filename as the number of the puzzle
            title = f"Polydot {docname[:2]}"
        else:
            title = title_field

        if subtitle:
            title = title + f" | {subtitle}"

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

    def plot_footer(
        self,
        copyright_text: str,
        paper_size="A4",
    ):
        layer = self.svg.getElementById("instructions_layer")
        _, y = self.svg.getElementById("guide_bottom").position
        x, _ = self.svg.getElementById("instructions_guide_left").position

        footer = TextElement(x=str(x), y=str(y), id="footer_textbox")
        layer.append(footer)

        footer.text = copyright_text + " | " + paper_size
        footer.style = Style(
            {
                "font-family": "Garamond",
                "fill-opacity": "1.0",
                "fill": "#000000",
                "font-size": "8pt",
            }
        )

    def get_paper_size_info(self, svg):
        """Extracts dimensions from SVG and determines the paper size."""

        if svg.get("width") == 210 and svg.get("height") == 297:
            return "A4"
        elif svg.get("width") == 216 and svg.get("height") == 279:
            return "US Letter"
        else:
            return f"{svg.get('width')} x {svg.get('height')}"

    def plot_difficulty_level(self, dot_connections):
        # Calculate the difficulty level based on the number of steps
        level = (len(dot_connections) // 200) + 1
        grouped_brains = Group()
        grouped_brains.set("id", "grouped_brains")

        self.svg.getElementById("instructions_layer").append(grouped_brains)
        layer = self.svg.getElementById("instructions_layer")

        for i in range(5):
            brain_character = PathElement(id=f"brain_character_{i}")
            brain_character.path = Path(
                "m 15.3568 5.4864 q 0.2066 -0.2066 0.2066 -0.5016 q 0 -0.2949 -0.2066 -0.5016 q -0.4719 -0.4719 -1.1211 -0.7474 q -0.6393 -0.285 -1.367 -0.285 q -0.7276 0 -1.3666 0.285 q -0.6393 0.2751 -1.1112 0.7474 q -0.2066 0.2066 -0.2066 0.5016 q 0 0.2949 0.2066 0.5016 q 0.2066 0.2066 0.4917 0.2066 q 0.2949 0 0.5115 -0.2066 q 0.6097 -0.6097 1.475 -0.6097 q 0.8654 0 1.4849 0.6097 q 0.2066 0.2066 0.5016 0.2066 q 0.2949 0 0.5016 -0.2066 z m -8.2304 -0.6785 q 0.2557 -0.1477 0.5408 -0.0689 q 0.285 0.0689 0.4327 0.3246 q 0.1477 0.2557 0.0689 0.5408 q -0.0689 0.2755 -0.3246 0.4327 q -0.7569 0.4327 -1.3472 1.0914 q -0.5899 0.6489 -0.9537 1.4454 q -0.3737 0.8159 -0.4719 1.711 q -0.0304 0.2949 -0.2656 0.4818 q -0.2261 0.177 -0.521 0.1477 q -0.285 -0.0304 -0.4719 -0.2557 q -0.1869 -0.2359 -0.1477 -0.5309 q 0.118 -1.1211 0.5899 -2.1437 q 0.4521 -0.9933 1.1896 -1.8092 l 0.0023 0.0004 q 0.7375 -0.8159 1.6813 -1.3666 z m 10.7082 7.9157 q 0 0.4426 -0.3147 0.7569 q -0.3147 0.3048 -0.7474 0.3048 l -2.7324 0.0013 q 0.2458 -0.521 0.2458 -1.0618 q 0 -0.2949 -0.2066 -0.5016 q -0.2066 -0.2066 -0.5016 -0.2066 q -0.285 0 -0.5016 0.2066 q -0.2066 0.2066 -0.2066 0.5016 q 0 0.4426 -0.3147 0.7569 q -0.3048 0.3048 -0.7474 0.3048 h -1.5424 q -0.2949 0 -0.5016 0.2066 q -0.2066 0.2066 -0.2066 0.5016 q 0 0.2949 0.2066 0.5016 q 0.2066 0.2066 0.5016 0.2066 l 4.3764 -0.0008 q 0.4426 0 0.7474 0.3147 q 0.3147 0.3147 0.3246 0.7474 q 0 0.2949 0.2066 0.5111 q 0.2066 0.2066 0.5016 0.2066 q 0.285 0 0.4917 -0.2066 q 0.2162 -0.2162 0.2162 -0.5111 q 0 -0.5507 -0.2557 -1.0717 q 0.6587 -0.019 1.1995 -0.3539 q 0.5408 -0.344 0.8555 -0.8947 q 0.3246 -0.5507 0.3246 -1.2193 q 0 -0.2949 -0.2066 -0.5016 q -0.2066 -0.2066 -0.5016 -0.2066 q -0.2949 0 -0.5016 0.2066 q -0.2066 0.2066 -0.2066 0.5016 z m 5.6639 -0.5606 l 0.0023 1.6235 q 0 0.0304 0 0.0788 q -0.0114 0.0392 -0.0114 0.0689 q 0.0114 0.059 0.0114 0.0788 q 0 0.0887 0 0.1279 q 0 0.0689 -0.0392 0.2066 l -0.0027 0.0023 q -0.0304 0.2755 -0.0788 0.5408 q -0.0392 0.2656 -0.118 0.521 q -0.3147 1.0621 -1.0028 1.9173 q -0.6785 0.8456 -1.6421 1.3864 q -0.9537 0.5408 -2.0748 0.6884 l 0.0034 1.8876 q 0 0.3539 -0.3345 0.4917 q -0.3246 0.1378 -0.5705 -0.118 l -2.2126 -2.2027 l -5.0378 -0.0015 q -1.0914 0 -2.0257 -0.462 q -0.9244 -0.462 -1.5732 -1.2585 q -0.6393 -0.8064 -0.8753 -1.829 l -0.884 -0.0013 q -1.1603 0 -2.114 -0.5606 q -0.9537 -0.5705 -1.5241 -1.5241 q -0.5705 -0.9636 -0.5705 -2.1239 q 0 -2.2126 0.8258 -4.1397 q 0.8357 -1.937 2.3009 -3.4022 q 1.4652 -1.4652 3.3923 -2.291 q 1.937 -0.8357 4.1496 -0.8357 l 0.8772 0.0011 q 2.1437 0 4.0412 0.7573 q 1.8978 0.7474 3.3824 2.0847 q 1.4945 1.3373 2.4386 3.1271 q 0.9537 1.7898 1.19 3.8741 q 0.0392 0.3147 0.059 0.6393 q 0.019 0.3147 0.019 0.6489 z m -1.593 2.8416 q 0.1477 -0.5016 0.1671 -1.0717 q -0.0392 -0.7474 -0.344 -1.3963 q -0.2949 -0.6587 -0.7866 -1.1504 q -0.5309 -0.5309 -1.2391 -0.8357 q -0.7078 -0.3048 -1.5142 -0.3048 q -0.0689 0 -0.1967 -0.0392 l -0.0091 0.0027 q -0.5998 0.5115 -1.3666 0.8064 q -0.7569 0.2949 -1.6124 0.2949 q -0.2949 0 -0.5111 -0.2066 q -0.2066 -0.2066 -0.2066 -0.5016 q 0 -0.2949 0.2066 -0.5016 q 0.2162 -0.2066 0.5111 -0.2066 q 0.6587 0 1.2391 -0.2458 q 0.58 -0.2557 1.0127 -0.6884 q 0.4327 -0.4327 0.6785 -1.0127 q 0.2557 -0.58 0.2557 -1.2486 q 0 -0.285 0.2066 -0.4917 q 0.2066 -0.2162 0.5016 -0.2162 q 0.2949 0 0.5016 0.2162 q 0.2066 0.2066 0.2066 0.4917 q 0 1.1801 -0.5606 2.2027 q 0.8258 0.1378 1.5534 0.5115 q 0.7276 0.3737 1.3076 0.9343 q -0.3246 -1.6813 -1.1801 -3.1172 q -0.8555 -1.4454 -2.1338 -2.5174 q -1.2783 -1.0717 -2.8614 -1.6619 q -1.5831 -0.5998 -3.363 -0.5998 l -0.878 -0.0011 q -1.9173 0 -3.599 0.7276 q -1.6813 0.7276 -2.9402 1.9861 q -1.2585 1.2585 -1.9861 2.9402 q -0.7276 1.6813 -0.7276 3.599 q 0 0.5804 0.2162 1.0914 q 0.2261 0.5016 0.5998 0.8848 q 0.3836 0.3836 0.8848 0.5998 q 0.5115 0.2162 1.0914 0.2162 l 0.8095 -0.0005 q 0.118 -0.7866 0.462 -1.4849 q 0.344 -0.6979 0.8753 -1.2486 q -0.0788 -0.4327 -0.3935 -0.7474 q -0.2066 -0.2066 -0.2066 -0.5016 q 0 -0.2949 0.2066 -0.5016 q 0.2162 -0.2066 0.5016 -0.2066 q 0.2949 0 0.5016 0.2066 q 0.3539 0.3539 0.58 0.8456 q 0.5309 -0.2949 1.1306 -0.4521 q 0.5998 -0.1572 1.2486 -0.1572 q 0.2949 0 0.5016 0.2066 q 0.2066 0.2066 0.2066 0.5016 q 0 0.2949 -0.2066 0.5016 q -0.2066 0.2066 -0.5016 0.2066 q -0.7375 0 -1.3864 0.285 q -0.6393 0.2751 -1.1211 0.7569 q -0.462 0.462 -0.7375 1.0816 q -0.2656 0.6097 -0.285 1.3076 l -0.0023 0.051 q 0.0788 0.8064 0.5111 1.4652 q 0.4426 0.6587 1.1306 1.0522 q 0.6983 0.3836 1.534 0.3836 l 7.4457 -0.0012 q 0.9636 0 1.7898 -0.3935 q 0.8258 -0.3935 1.4161 -1.0816 q 0.5998 -0.6884 0.8654 -1.5633 z"
            )

            # Set the position of the brain character
            dy = brain_character.bounding_box().height
            _, y = self.svg.getElementById("guide_title").position
            x, _ = self.svg.getElementById("guide_sequence").position

            brain_character.transform = f"translate({x - ((i+1) * 25)}, {y - dy})"

            brain_character.style = (
                Style({"display": "none"})
                if i + 1 > level
                else Style({"fill": "#000000"})
            )
            grouped_brains.append(brain_character)

        layer.append(grouped_brains)

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

    def count_planes(self, puzzle_planes_id, plane_fill):
        processed_planes = self.svg.getElementById(puzzle_planes_id)
        xpath_query = f".//*[@style and contains(@style, 'fill:{plane_fill}')]"
        planes_with_fill = self.svg.xpath(xpath_query)
        number_of_f_planes = (
            len(planes_with_fill) if planes_with_fill is not None else 0
        )
        number_of_planes = len(processed_planes) if processed_planes is not None else 0

        return number_of_planes or number_of_f_planes

    def createRootGroup(self, id: str):
        root_group: Group = self.svg.add(Group())
        root_group.set("id", id)
        root_group.transform = "translate(0, 0)"
        return root_group

    def plot_reference_sequence(self):
        """Create a reference sequence of the letters"""
        reference_sequence_group = self.createRootGroup("reference_sequence")

        xr, y = self.svg.getElementById("guide_sequence").position
        xl, _ = self.svg.getElementById("instructions_guide_left").position
        x = xl
        width = xr - xl

        # Calculate the maximum number based on the length of coding_sequence
        max_number = len(self.coding_sequence) ** 2

        # Create a rectangle element
        rect = Rectangle(
            x=str(x),
            y=str(y),
            width=str(width),
            height=str(1000),  # Arbitrary height to fit the text
            id="reference_sequence_rect",
        )

        # Add the rectangle to the <defs> section
        self.svg.defs.append(rect)

        # Create a text element inside the rectangle
        text_element = TextElement(
            x=str(x),
            y=str(y),
            id="reference_sequence_textbox",
        )
        text_element.set("shape-inside", f"url(#{rect.get('id')})")
        text_element.style = self.fontConsolas
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
                x=str(xl),
                y=str(y),
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

    def plot_puzzle_dots(
        self,
        mapping: list,
        collisions: list,
        layer_id,
    ):
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
            text_element_with_label.style = self.fontConsolas
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

    def plot_letter_sequence(self, mapping: list):
        """Plot the mapping to the canvas"""
        sequence_string = " ".join(
            item["letter_label"] + ("  " if (index + 1) % 5 == 0 and index != 0 else "")
            for index, item in enumerate(mapping)
        )
        xr, y = self.svg.getElementById("guide_sequence").position
        xl, _ = self.svg.getElementById("instructions_guide_left").position
        x = xl
        width = xr - xl

        element = self.add_text_in_rect(
            sequence_string,
            "sequence_string_textbox",
            "sequence_string_rect",
            x,
            y,
            width=width,
        )
        self.svg.getElementById("instructions_layer").append(element)

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
        elem.style = self.fontConsolas
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
        align: str = "left",
    ):
        """Add a text element inside a rectangle at the given location with specified properties"""

        # Create a rectangle element
        rect = Rectangle(
            x=str(x), y=str(y), width=str(width), height=str(height), id=rect_id
        )
        if align == "center":
            rect.style = Style(
                {
                    "text-align": align,
                    "text-anchor": "middle",
                }
            )

        # Add the rectangle to the <defs> section
        self.svg.defs.append(rect)

        # Create a text element inside the rectangle
        text_element = TextElement(x=str(x), y=str(y), id=text_id)
        text_element.set(
            "shape-inside", f"url(#{rect_id})"
        )  # Reference the rectangle as the shape inside the text
        text_element.style = self.fontConsolas
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
