import inkex
from inkex import AbortExtension
from inkex.elements import PathElement, Line, Group
from inkex import Vector2d
import json

class BreakUpLinesExtension(inkex.EffectExtension):
    """Break up a path into line segments and add caps at the start and end."""

    def add_arguments(self, pars):
        """Add custom arguments to the parser."""
        pars.add_argument("--line_width", type=float, default=1.0, help="Width of the line")
        pars.add_argument("--save_json", type=inkex.Boolean, default=False, help="Save line segments to JSON")

        pars.add_argument("--tab", help="The selected UI-tab when OK was pressed")

    def effect(self):
        """Main function."""
        # Retrieve parameters from GUI
        line_width = self.options.line_width
        save_json = self.options.save_json


        # Create a new group to hold the line elements
        lines_group = self.svg.get_current_layer().add(
            Group(id="lines_group", style="stroke:#000000;fill:none;stroke-width:1pt")
        )

        # Get selected paths
        target_paths = list(self.svg.selection.filter(PathElement))
        if not target_paths:
            raise AbortExtension("Please select at least one path object.")

        # Process the selected path into lines and apply caps
        line_segments = self.convert_path_to_lines(target_paths[0], lines_group, line_width)
        if save_json:
            self.save_line_segments(line_segments)


    def convert_path_to_lines(self, path: PathElement, lines_group: Group,line_widht:float) -> list:
        """Convert a path element into line segments and store in a group."""
        graph = {}  # Encapsulated within this method
        line_segments = []
        unique_segments = set()  # Store undirected unique edges

        # Extract segments from path and break apart shorthand notation
        segments = path.path.to_non_shorthand().break_apart()

        for coordinates in segments:
            if len(coordinates) < 2:
                continue

            start = Vector2d(coordinates[0].x, coordinates[0].y)
            for i in range(1, len(coordinates)):
                end = Vector2d(coordinates[i].x, coordinates[i].y)

                # Create undirected edge as frozenset of rounded coordinates
                edge = frozenset([
                    (round(start.x), round(start.y)),
                    (round(end.x), round(end.y))
                ])

                # Skip duplicates
                if edge in unique_segments:
                    start = end
                    continue
                unique_segments.add(edge)

                # Build the graph representation
                graph.setdefault(start, []).append(end)
                graph.setdefault(end, []).append(start)


                # Create the line element
                current_id = len(line_segments) + 1
                line = Line.new(start, end, id=f"line_{current_id}", style=f"stroke:#000000;fill:none;stroke-width:{line_widht}")
                lines_group.add(line)
                line_segments.append({
                    "x1": start.x,
                    "y1": start.y,
                    "x2": end.x,
                    "y2": end.y
                })

                # Move start point to current end for next line
                start = end


        return line_segments

    

    def save_line_segments(self, line_segments: list):
        """Save line segments to a JSON file."""
        try:
            with open("line_segments.json", "w") as f:
                json.dump(line_segments, f, indent=4)
        except IOError as e:
            inkex.utils.debug(f"Failed to save line_segments.json: {e}")

if __name__ == "__main__":
    BreakUpLinesExtension().run()
