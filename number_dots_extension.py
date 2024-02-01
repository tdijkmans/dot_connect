# Import required modules
import math

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


# Create a class named NumberDots that inherits from inkex.EffectExtension
class NumberDots(EffectExtension):
    """Replace the selection's nodes with numbered dots according to the options"""

    coding_sequence = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    fontsize = ""
    text_layer: Layer = None

    # Define method to add command-line arguments for the extension
    def add_arguments(self, pars):
        pars.add_argument("--fontsize", default="6px", help="Size of node labels")
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
            default=True,
        )

        pars.add_argument(
            "--plot_reference_sequence",
            type=Boolean,
            help="Plot reference sequence",
            default=False,
        )

    # Define the main effect method
    def effect(self):
        so = self.options  # shorthand for self.options
        # Filter selected elements to only include PathElements
        selected_path = self.svg.selection.filter(PathElement)
        if not selected_path:
            raise AbortExtension(_("Please select at least one path object."))

        # Get the fontsize from the options
        self.fontsize = self.svg.unittouu(so.fontsize)

        puzzle_planes_layer = self.svg.add(Layer())
        puzzle_planes_layer.set("id", "puzzle_planes")
        puzzle_dots_layer = self.svg.add(Layer())
        puzzle_dots_layer.set("id", "puzzle_dots")
        text_layer = self.svg.add(Layer())
        text_layer.set("id", "text_layer")

        # Plot centroids in filled elements
        if so.plot_centroids:
            self.plot_puzzle_centroids()

        dot_connections = self.create_mapping(selected_path)

        if so.plot_dots:
            self.plot_puzzle_dots(dot_connections)

        if so.plot_sequence:
            sequence = self.plot_letter_sequence(dot_connections)
            text_layer.append(sequence)
        compact_mapping = self.compress_mapping(dot_connections)
        if so.plot_compact_sequence:
            compact_sequence = self.plot_compact_mapping(compact_mapping)
            text_layer.append(compact_sequence)

        self.write_mapping_to_file(dot_connections, "connections.json")
        self.write_mapping_to_file(compact_mapping, "compact_mapping.json")
        self.print_stats(dot_connections)

        if so.plot_reference_sequence:
            self.createReferenceSequence()

        for puzzle_path in selected_path:
            puzzle_path.set("id", "source_path")
            puzzle_path.style = Style(
                {
                    "stroke": "#000000",
                    "stroke-width": "0.1pt",
                    "fill": "none",
                }
            )

    def plot_puzzle_centroids(self, target_fill="#ff0000"):
        xpath_query = f".//*[@style and contains(@style, 'fill:{target_fill}')]"
        red_planes = self.svg.xpath(xpath_query)

        for index, plane in enumerate(red_planes):
            endpoints = plane.path.transform(plane.composed_transform()).end_points

            x_coords = []
            y_coords = []

            for _, (x, y) in enumerate(endpoints):
                x_coords.append(x)
                y_coords.append(y)

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
            self.svg.getElementById("puzzle_planes").append(text_element)
            plane.set("id", f"source_plane_{id}")
            plane.style = Style(
                {
                    "stroke": None,
                    "fill": "#d3d3d3",
                }
            )

    def createRootGroup(self, id: str):
        root_group: Group = self.svg.add(Group())
        root_group.set("id", id)
        root_group.transform = "translate(0, 0)"
        return root_group

    def createReferenceSequence(self):
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

        text_element.style = {
            "font-size": self.fontsize,
            "font-family": "Consolas",
            "fill-opacity": "1.0",
            "font-style": "normal",
            "fill": "#000000",
        }

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

    def print_stats(self, mapping: list):
        """Print statistics about the mapping"""
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

        total_num_dots = len(unique_dots)
        self.svg.getElementById("text_layer").append(
            self.add_text(
                50,
                1053,
                f"{len(mapping)} connections ({total_num_dots} dots)",
                "total_num_dots",
            )
        )

    def plot_puzzle_dots(self, mapping: list):
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

            first_letter = step["letter_label"][0]
            second_letter = step["letter_label"][1]

            first_letter_label = self.add_text(
                x_center - 4,
                y_center + self.fontsize / 4,  # Adjust Y for centering
                first_letter,
                f"01_{first_letter} of {step['letter_label']}",
                "#000000",  # Black
            )

            second_letter_label = self.add_text(
                x_center + 1,
                y_center + self.fontsize / 4,  # Adjust Y for centering
                second_letter,
                f"02_{second_letter} of {step['letter_label']}",
                "#000000",  # Black
            )

            black_circle = self.createCircle(
                x_center,
                y_center,
                0.5,
                fill="#000000",
                id=f"black_dot_{step['letter_label']}",
            )

            current_dot_group = self.svg.getElementById("puzzle_dots").add(Group())
            current_dot_group.set("id", f"{step['letter_label']}")
            current_dot_group.append(black_circle)
            current_dot_group.append(first_letter_label)
            current_dot_group.append(second_letter_label)

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
        width = 698
        height = 113

        if len(mapping) < 500:
            y_pos = 929 + 50

        for item in mapping:
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

    def plot_compact_mapping(self, mapping: list):
        """Plot the mapping to the canvas"""
        sequence_string = ""
        x_pos = 49
        y_pos = 80
        width = 698
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
            path_trans_applied = node.path.transform(node.composed_transform())

            for _, (x, y) in enumerate(path_trans_applied.end_points):
                dot_number += 1

                # Round the coordinates using the specified precision factor
                x_rounded = round(x / precision) * precision
                y_rounded = round(y / precision) * precision
                rounded_coords = (x_rounded, y_rounded)

                if rounded_coords in coord_to_label:
                    # Coordinate already exists, use the same label
                    letter_label = coord_to_label[rounded_coords]
                else:
                    # New coordinate, generate a new label and store it
                    next_unique_dot_number = len(coord_to_label) + 1
                    letter_label = self.get_letter_id_from_number(
                        next_unique_dot_number
                    )
                    coord_to_label[rounded_coords] = letter_label

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

    def write_mapping_to_file(self, mapping, filename):
        """Write the mapping to a file"""
        with open(filename, "w") as f:
            f.write(str(mapping))

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
        elem.style = {
            "font-size": self.fontsize,
            "font-family": "Consolas",
            "fill-opacity": "1.0",
            "font-style": "normal",
            "fill": color,
        }
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
        text_element.style = {
            "font-size": self.fontsize,
            "font-family": "Consolas",
            "fill-opacity": "1.0",
            "font-style": "normal",
            "fill": color,
        }
        tspan = Tspan(text_string)
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
