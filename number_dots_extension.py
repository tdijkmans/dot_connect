# Import required modules
import json
import math
import random

import inkex
from inkex import (
    AbortExtension,
    Boolean,
    Circle,
    EffectExtension,
    Group,
    Layer,
    PathElement,
    Rectangle,
    Style,
    TextElement,
    Tspan,
)
from inkex.localization import inkex_gettext as _
from inkex.paths import Line, Move, Path


# Create a class named NumberDots that inherits from inkex.EffectExtension
class NumberDots(EffectExtension):
    """Replace the selection's nodes with numbered dots according to the options"""

    coding_sequence = (
        "abcdefghijklmnopqrstuvwxyz" + "1234567890" + "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    )
    fontsize = ""
    fontStyle = Style(
        {
            "font-family": "Consolas",
            "fill-opacity": "1.0",
            "fill": "#000000",
        }
    )

    # Define method to add command-line arguments for the extension
    def add_arguments(self, pars):
        """Add command-line arguments for the extension"""
        pars.add_argument(
            "--align_within",
            type=int,
            default=3,
            help="Co-align the dots within the specified distance",
        )

        pars.add_argument("--fontsize", default="8px", help="Size of node labels")
        pars.add_argument(
            "--fontweight", default="normal", help="Weight of node labels"
        )
        pars.add_argument(
            "--start", type=int, default=1, help="First number in the sequence"
        )
        pars.add_argument("--tab", help="The selected UI-tab when OK was pressed")
        pars.add_argument(
            "--precision",
            type=int,
            default=1,
            help="Precision for coordinates; higher value represents lower resolution",
        )

        pars.add_argument(
            "--extreme_difficulty",
            type=Boolean,
            help="Enable extreme difficulty",
            default=False,
        )

        pars.add_argument(
            "--plot_stats",
            type=Boolean,
            help="Add statistics",
            default=True,
        )

        pars.add_argument(
            "--plot_centroids",
            type=Boolean,
            help="Plot centroids of filled elements",
            default=True,
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

        # have a minimal distance between dots
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
            "--replace_text",
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
            "--plot_copyright",
            type=Boolean,
            help="Add copyright",
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
        self.fontStyle = self.fontStyle
        self.fontStyle["font-weight"] = so.fontweight
        self.fontStyle["font-size"] = self.svg.unittouu(so.fontsize)
        self.fontsize = self.svg.unittouu(so.fontsize)

        # find selected path element
        selected_path: PathElement = self.svg.selection.filter(PathElement)

        if selected_path is None:
            raise AbortExtension(_("Please select at least one path object."))

        # Create layers for puzzle planes, dots, and text
        instructions_layer_id = "instructions_layer"
        dots_layer_id = "dots_layer"
        centroids_layer_id = "centroids_layer"
        solution_layer_id = "solution_layer"

        # Remove layers for puzzle planes, dots, and text if the option is set
        if so.replace_dots:
            self.remove_layer(dots_layer_id)

        if so.replace_centroids:
            self.remove_layer(centroids_layer_id)

        if so.replace_text:
            self.remove_layer(instructions_layer_id)

        self.create_layers(
            [
                solution_layer_id,
                centroids_layer_id,
                dots_layer_id,
                instructions_layer_id,
            ]
        )
        instructions_layer: Layer = self.svg.getElementById(instructions_layer_id)

        # Create a mapping of letter IDs, numbers, and coordinates
        # Also check for collisions and calculate distances
        dot_connections = self.create_mapping(selected_path)
        collisions, sorted_dots = self.check_density(
            dot_connections, so.minimal_distance
        )
        avg_distance, lowest_distance, highest_distance = self.evaluate_distances(
            sorted_dots
        )
        compact_mapping = self.compress_mapping(dot_connections)
        planes = self.count_planes(centroids_layer_id)
        unique_dots = self.get_unique_dots(dot_connections)

        self.annotate_source_page("puzzle_page", "Puzzle")
        self.append_instructions_page("puzzle_instructions", "Instructions")
        self.process_puzzle_path(selected_path, solution_layer_id)

        # Plot the Puzzle Dots and Centroids
        if so.plot_dots:
            self.plot_puzzle_dots(dot_connections, collisions, dots_layer_id)
        # Plot centroids in filled elements
        if so.plot_centroids:
            self.plot_puzzle_centroids(centroids_layer_id, solution_layer_id)

        # Plot the Instructions
        if so.plot_sequence:
            sequenceElement = self.plot_letter_sequence(dot_connections)
            instructions_layer.append(sequenceElement)

        # Add copyright
        if so.plot_copyright:
            self.plot_copyright(so.copyright_text, instructions_layer_id)

        self.plot_title(so.title, instructions_layer_id)
        self.plot_difficulty_level(dot_connections, instructions_layer_id)

        # ADVANCED OPTIONS
        # Plot the sequence as pairs
        if so.extreme_difficulty:
            pairs = self.plot_random_sequence_pairs(dot_connections)
            instructions_layer.append(pairs)
        # Plot the compact sequence
        if so.plot_compact_sequence:
            compact_sequence = self.plot_compact_mapping(compact_mapping)
            instructions_layer.append(compact_sequence)
        # Plot the reference sequence
        if so.plot_reference_sequence:
            self.plot_reference_sequence()

        if so.plot_stats:
            # Print statistics
            self.plot_stats(
                dot_connections,
                len(unique_dots),
                avg_distance,
                lowest_distance,
                highest_distance,
                planes,
                instructions_layer_id,
            )

        instructions_layer.transform = "translate(800, -350)"

        # Combine mappings and write data to a file
        current_file_name = self.svg.get("sodipodi:docname", "")  # Get doc name
        output_name = current_file_name.split(".")[0]  # Remove the file extension

        sequenceString = self.svg.getElementById("sequence_string_textbox_tspan").text
        mappings = {
            "collisions": collisions,
            "sorted_dots": sorted_dots,
            "dot_connections": dot_connections,
            "compact_mapping": compact_mapping,
            "sequence": sequenceString,
            "stats": f"{len(dot_connections)} steps, {len(sorted_dots)} unique dots, {round(lowest_distance)} min {round(avg_distance)} avg {round(highest_distance)} max, {planes} planes",
        }

        # Write combined mappings to a single JSON file
        self.write_mappings_to_file(mappings, f"{output_name}_combined_mappings.json")

    def process_puzzle_path(self, selected_path, layer_id):
        # Set the style of the path
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

    def annotate_source_page(self, page_id, page_label):
        page = self.document.xpath("//inkscape:page", namespaces=inkex.NSS)[0]
        page.set("id", page_id)
        page.set("inkscape:label", page_label)

    def append_instructions_page(self, page_id, page_label):
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

    def plot_title(self, title: str, layer_id):
        layer = self.svg.getElementById(layer_id)
        title_element = TextElement(x="50", y="885", id="puzzle_title_textbox")

        # Set the title of the puzzle as the filename if not provided
        title = title or self.svg.get("sodipodi:docname", "").split(".")[0]
        title_element.text = title
        title_element.style = Style(
            {
                "font-family": "Consolas",
                "fill-opacity": "1.0",
                "fill": "#000000",
                "font-size": "20px",
                "font-weight": "bold",
            }
        )
        layer.append(title_element)

    def plot_copyright(self, copyright_text: str, layer_id):
        layer = self.svg.getElementById(layer_id)
        copyright = TextElement(x="634", y="1040", id="copyright_textbox")
        copyright.text = copyright_text
        copyright.style = Style(
            {
                "font-family": "Garamond",
                "fill-opacity": "1.0",
                "fill": "#000000",
                "font-size": "8px",
            }
        )
        layer.append(copyright)

    def plot_difficulty_level(self, dot_connections, layer_id):
        # Calculate the difficulty level based on the number of steps
        level = (len(dot_connections) // 200) + 1
        grouped_brains = Group()
        grouped_brains.set("id", "grouped_brains")

        self.svg.getElementById(layer_id).append(grouped_brains)
        layer = self.svg.getElementById(layer_id)

        for i in range(5):
            brain_character = TextElement(id=f"brain_character_{i}", y="885")
            brain_character.text = "🧠"
            brain_character.set("font-size", "20px")
            brain_character.set("x", str(150 + (i * 25)))
            brain_character.set("fill", "#000000")

            if i > level:
                brain_character.set("fill", "#e6e6e6")

            grouped_brains.append(brain_character)

        layer.append(grouped_brains)
        # move to right side of the page
        grouped_brains.transform = "translate(450, 0)"

    def remove_layer(self, layer_id):
        """Remove layers for puzzle planes, dots, and text"""
        layer = self.svg.getElementById(layer_id)

        if layer is not None:
            self.svg.remove(layer)

    def create_layers(self, layers: list):
        """Create layers for puzzle planes, dots, and text"""
        for layer in layers:
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
        return colliding_dots, sorted_dots

    def evaluate_distances(self, sorted_distances):
        num_distances = len(sorted_distances)
        total_distance = sum(distance["distance"] for distance in sorted_distances)
        avg_distance = total_distance / num_distances if num_distances > 0 else 0
        lowest_distance = sorted_distances[0]["distance"]
        highest_distance = sorted_distances[-1]["distance"]

        return avg_distance, lowest_distance, highest_distance

    def count_planes(self, puzzle_planes_id):
        processed_planes = self.svg.getElementById(puzzle_planes_id)
        xpath_query = ".//*[@style and contains(@style, 'fill:#ff0000')]"
        red_planes = self.svg.xpath(xpath_query)
        number_of_red_planes = len(red_planes) if red_planes is not None else 0
        number_of_planes = len(processed_planes) if processed_planes is not None else 0

        return number_of_planes or number_of_red_planes

    def plot_puzzle_centroids(
        self, centroids_layer, solutions_layer, target_fill="#ff0000"
    ):
        xpath_query = f".//*[@style and contains(@style, 'fill:{target_fill}')]"
        red_planes = self.svg.xpath(xpath_query)

        if red_planes is None or len(red_planes) == 0:
            return

        for index, plane in enumerate(red_planes):
            endpoints = plane.path.transform(plane.composed_transform()).end_points

            x_coords = []
            y_coords = []

            for _, (x, y) in enumerate(endpoints):
                x_coords.append(x)
                y_coords.append(y)

            if not x_coords or not y_coords:
                continue

            centroid_x = sum(x_coords) / len(x_coords)
            centroid_y = sum(y_coords) / len(y_coords)

            id = index + 1

            text_element = self.add_text(
                centroid_x - 4,
                centroid_y + self.fontsize / 4,  # Adjust Y for centering
                "*",
                f"plane_centroid_label_{id}",
                "#000000",  # Black
            )
            self.svg.getElementById(centroids_layer).append(text_element)

            plane.set("id", f"source_plane_{id}")
            plane.style = Style(
                {
                    "stroke": None,
                    "fill": "#d3d3d3",
                }
            )
            self.svg.getElementById(solutions_layer).append(plane)

    def createRootGroup(self, id: str):
        root_group: Group = self.svg.add(Group())
        root_group.set("id", id)
        root_group.transform = "translate(0, 0)"
        return root_group

    def plot_reference_sequence(self):
        """Create a reference sequence of the letters"""
        reference_sequence_group = self.createRootGroup("reference_sequence")

        # Calculate the maximum number based on the length of coding_sequence
        max_number = len(self.coding_sequence) ** 2

        # Create a rectangle element
        rect = Rectangle(
            x="50",
            y="50",
            width="698",
            height="113",
            id="reference_sequence_rect",
        )

        # Add the rectangle to the <defs> section
        self.svg.defs.append(rect)

        # Create a text element inside the rectangle
        text_element = TextElement(x="50", y="50", id="reference_sequence_textbox")
        text_element.set("shape-inside", f"url(#{rect.get('id')})")

        text_element.style = self.fontStyle
        text_element.style["fill"] = "#000000"

        # Add the text element to the document
        reference_sequence_group.append(text_element)

        # Add the reference sequence
        reference_sequence = ""
        for i in range(1, max_number + 1):
            reference_sequence += self.get_letter_id_from_number(i) + " "

        reference_sequence_group.append(
            self.add_text_in_rect(
                49,
                50,
                698,
                113,
                reference_sequence,
                "reference_sequence_textbox",
                "reference_sequence_rect",
                "#000000",  # Black
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

    def plot_stats(
        self,
        mapping: list,
        total_num_dots: int,
        avg_distance: float,
        lowest_distance: float,
        highest_distance: float,
        planes: int,
        layer_id,
    ):
        """Print statistics about the mapping"""
        self.svg.getElementById(layer_id).append(
            self.add_text(
                50,
                1053,
                f"{len(mapping)} steps, {total_num_dots} unique dots, {round(lowest_distance)} min {round(avg_distance)} avg {round(highest_distance)} max, {planes} planes",
                "puzzle_stats_textbox",
            )
        )

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
            text_element_with_label.style = self.fontStyle
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
        sequence_string = ""
        y_pos = 929
        x_pos = 49
        width = 677
        height = 113

        for index, item in enumerate(mapping):
            if (index + 1) % 5 == 0 and index != 0:
                sequence_string += f"{item['letter_label']}" + " " + " "
            else:
                sequence_string += f"{item['letter_label']}" + " "

        return self.add_text_in_rect(
            x_pos,
            y_pos,
            width,
            height,
            sequence_string,
            "sequence_string_textbox",
            "sequence_string_rect",
            "#000000",  # Black
        )

    def plot_random_sequence_pairs(self, mapping: list):
        """Plot the mapping to the canvas as a sequence of shuffled pairs"""

        pairs = []

        for index, item in enumerate(mapping):
            if index != 0:
                pairs.append(
                    f"{mapping[index-1]['letter_label']}-{item['letter_label']}"
                )

        random.shuffle(pairs)
        sequence_string = " ".join(pairs)

        x_pos = 49
        y_pos = 929
        width = 677
        height = 113

        return self.add_text_in_rect(
            x_pos,
            y_pos,
            width,
            height,
            sequence_string,
            "sequence_string_textbox_extreme",
            "sequence_string_rect_extreme",
            "#000000",  # Black
        )

    def plot_compact_mapping(self, mapping: list):
        """Plot the mapping to the canvas"""
        sequence_string = ""
        x_pos = 49
        y_pos = 80
        width = 677
        height = 113

        if len(mapping) < 500:
            y_pos = 929 + 50

        for item in mapping:
            sequence_string += f"{item}" + " "

        return self.add_text_in_rect(
            x_pos,
            y_pos,
            width,
            height,
            sequence_string,
            "compact_sequence_string_textbox",
            "compact_sequence_string_rect",
            "#000000",  # Black
        )

    def create_mapping(self, nodes: list):
        """Create a mapping of letter IDs, numbers, and coordinates"""
        result_mapping = []
        coord_to_label = {}  # Dictionary for efficient coordinate lookup
        dot_number = self.options.start - 1

        # Get the precision factor from the options
        precision = self.options.precision

        for node in nodes:
            path: Path = node.path
            path_trans_applied = path.transform(node.composed_transform())

            previous_point = None

            for _, (x, y) in enumerate(path_trans_applied.end_points):
                # Round the coordinates using the specified precision factor
                x_rounded = round(x / precision) * precision
                y_rounded = round(y / precision) * precision
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
        elem.style = self.fontStyle
        elem.style["fill"] = color
        return elem

    def add_text_in_rect(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        text_string: str,
        text_id: str,
        rect_id: str,
        color: str = "#000",
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
        text_element.style = self.fontStyle
        text_element.style["fill"] = color
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
    NumberDots().run()
