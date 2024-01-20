# Import required modules
import math

import inkex
from inkex import Circle, TextElement
from inkex.localization import inkex_gettext as _


# Create a class named NumberDots that inherits from inkex.EffectExtension
class NumberDots(inkex.EffectExtension):
    """Replace the selection's nodes with numbered dots according to the options"""

    # Define method to add command-line arguments for the extension
    def add_arguments(self, pars):
        pars.add_argument(
            "--dotsize", default="10px", help="Size of the dots on the path nodes"
        )
        pars.add_argument("--fontsize", default="6px", help="Size of node labels")
        pars.add_argument(
            "--start", type=int, default=1, help="First number in the sequence"
        )
        pars.add_argument("--tab", help="The selected UI-tab when OK was pressed")

    # Define the main effect method
    def effect(self):
        # Filter selected elements to only include PathElements
        filtered = self.svg.selection.filter(inkex.PathElement)
        if not filtered:
            raise inkex.AbortExtension(_("Please select at least one path object."))

        unique_mapping = self.create_mapping(filtered)
        self.write_mapping_to_file(unique_mapping, "mapping.json")
        self.plot_mapping(unique_mapping)
        self.plot_letter_sequence(unique_mapping)
        self.print_stats(unique_mapping)

        for node in filtered:
            node.set("id", "source_path")

    def createRootGroup(self, id: str):
        root_group: inkex.Group = self.svg.add(inkex.Group())
        root_group.set("id", id)
        root_group.transform = "translate(0, 0)"
        return root_group

    def print_stats(self, mapping: list):
        """Print statistics about the mapping"""
        puzzle_stats_group = self.createRootGroup("puzzle_stats")

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
        puzzle_stats_group.append(
            self.add_text(
                50,
                280,
                f"Total number of dots: {total_num_dots}",
                "total_num_dots",
            )
        )

        total_num_lines = len(mapping)
        puzzle_stats_group.append(
            self.add_text(
                50,
                290,
                f"Total number of lines to draw: {total_num_lines}",
                "total_num_lines",
            )
        )

    def plot_mapping(self, mapping: list):
        """Plot the mapping to the canvas"""
        # Calculate the radius of the dots based on dotsize
        radius = self.svg.unittouu(self.options.dotsize) / 2
        mapping_table_group = self.createRootGroup("mapping_table")

        unique_dots = []

        letter_group = mapping_table_group.add(inkex.Group())
        letter_group.set("id", "letter_group")
        circle_group = mapping_table_group.add(inkex.Group())
        circle_group.set("id", "circle_group")

        # Remove duplicate dots
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

        for step in unique_dots:
            letter_label = self.add_text(
                step["x"],
                step["y"],
                step["letter_label"],
                f"letter_{step['letter_label']}",
                "#ffffff",
            )

            circle: inkex.Circle = Circle(
                cx=str(step["x"]),
                cy=str(step["y"]),
                r=str(radius),
            )
            circle.set("id", f"circle_{step['letter_label']}")

            circle_group.append(circle)
            letter_group.append(letter_label)

    def plot_letter_sequence(self, mapping: list):
        """Plot the mapping to the canvas"""
        sequence_table_group = self.createRootGroup("letter_sequence_table")
        letter_sequence_group = sequence_table_group.add(inkex.Group())
        letter_sequence_group.set("id", "letter_sequence_group")
        dot_sequence_group = sequence_table_group.add(inkex.Group())
        dot_sequence_group.set("id", "dot_sequence_group")

        sequence_string = ""
        x_offset = 50
        y_offset = 200

        for item in mapping:
            letter_sequence_group.append(
                self.add_text(
                    item["dot_number"] * self.svg.unittouu(self.options.fontsize) * 2
                    + x_offset,
                    50 + y_offset,
                    item["letter_label"],
                    f"seq_{item['dot_number']}",
                )
            )
            dot_sequence_group.append(
                self.add_text(
                    item["dot_number"] * self.svg.unittouu(self.options.fontsize) * 2
                    + x_offset,
                    60 + y_offset,
                    item["dot_number"],
                    f"step_{item['dot_number']}",
                )
            )
            sequence_string += f"{item['letter_label']}" + " "

        sequence_table_group.append(
            self.add_text(
                0 + x_offset,
                70 + y_offset,
                sequence_string[:-3],
                "sequence_string",
            )
        )

    def create_mapping(self, nodes: list):
        """Create a mapping of letter IDs, numbers, and coordinates"""
        result_mapping = []
        coord_to_label = {}  # Dictionary for efficient coordinate lookup

        for node in nodes:
            path_trans_applied = node.path.transform(node.composed_transform())

            for step, (x, y) in enumerate(path_trans_applied.end_points):
                dot_number = self.options.start + step
                coord_key = (x, y)  # Create a tuple key for the coordinates

                if coord_key in coord_to_label:
                    # Coordinate already exists, use the same label
                    letter_label = coord_to_label[coord_key]
                else:
                    # New coordinate, generate a new label and store it
                    letter_label = self.get_letter_id_from_number(dot_number)
                    coord_to_label[coord_key] = letter_label

                result_mapping.append(
                    {
                        "x": x,
                        "y": y,
                        "dot_number": dot_number,
                        "letter_label": letter_label,
                    }
                )

        return result_mapping

    def write_mapping_to_file(self, mapping, filename):
        """Write the mapping to a file"""
        with open(filename, "w") as f:
            f.write(str(mapping))

    # Define a method to set the style of dots based on their position
    def set_dot_style(self, circle, total_num_dots: int, dot_number: int):
        dot_style = inkex.Style(
            {
                "stroke": "#ffffff",
                "stroke-width": "0.1pt",
                "fill": "#000000",
            }
        )

        dot_style_start_end = inkex.Style(
            {
                "stroke": "#000000",
                "stroke-width": "0.1pt",
                "fill": "#ffffff",
            }
        )

        if dot_number == 1 or dot_number == total_num_dots:
            circle.style = dot_style_start_end
        else:
            circle.style = dot_style
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
            "font-size": self.svg.unittouu(self.options.fontsize),
            "font-family": "Arial",
            "fill-opacity": "1.0",
            "font-weight": "bold",
            "font-style": "normal",
            "fill": color,
        }
        return elem

    # Define a method to generate letter IDs
    # The max number of dots can be 2074 (52*52)
    def get_letter_id_from_number(self, number):
        """Generate letter IDs from 1 to 2074"""
        letter_id_array = [
            letter for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        ]

        first_letter_index = (number - 1) // len(letter_id_array)
        second_letter_index = (number - 1) % len(letter_id_array)

        first_letter = letter_id_array[first_letter_index % len(letter_id_array)]
        second_letter = letter_id_array[second_letter_index]

        return f"{first_letter}{second_letter}"

    def get_number_from_letter_id(self, letter_id):
        """Retrieve the number from letter IDs"""
        letter_id_array = [
            letter for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        ]

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
