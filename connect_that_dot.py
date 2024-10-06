import inkex
from inkex import AbortExtension
from inkex.elements import PathElement, Line, Group, Defs
from inkex import Vector2d
import json
import math

class ConnectThatDotExtension(inkex.EffectExtension):
    """Break up a path into line segments and add caps at the start and end."""

    def add_arguments(self, pars):
        """Add custom arguments to the parser."""
        pars.add_argument(
            "--line_length",
            type=int,
            default=5,
            help="Size of the cap at the end of the line."
        )
        pars.add_argument(
            "--cap_style",
            type=str,
            default="round",
            choices=["round", "square", "butt"],
            help="Style of the cap at the end of the line."
        )

        pars.add_argument("--stroke_width", type=float, default=1.0, help="Width of the line")
        

        pars.add_argument("--tab", help="The selected UI-tab when OK was pressed")

    def effect(self):
        """Main function."""
        # Retrieve parameters from GUI
        line_length = self.options.line_length
        cap_style = self.options.cap_style
        stroke_width = self.options.stroke_width


        # Get selected paths
        target_paths = list(self.svg.selection.filter(PathElement))
        if not target_paths:
            raise AbortExtension("Please select at least one path object.")
        

        # Process the selected paths into lines and apply caps
        for path in target_paths:
            line_segments = self.convert_path_to_lines(path)
            self.cap_line_segments(line_segments, line_length, cap_style, stroke_width)


    def convert_path_to_lines(self, path: PathElement) -> list:
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


                # Create a line element and add to the group
                line_segments.append({
                    "x1": start.x,
                    "y1": start.y,
                    "x2": end.x,
                    "y2": end.y
                })

                # Move start point to current end for next line
                start = end


        return line_segments

    def cap_line_segments(self, line_segments: list, line_length: int, cap_style: str, stroke_width: float):
        """Plot line caps at start and end of each segment."""
        cap_group = self.svg.get_current_layer().add(
           Group(id="cap_group", style=f"stroke:#0000FF;fill:none;stroke-width:{stroke_width}, stroke-linecap:{cap_style}")
        )

        for point in line_segments:
            try:
                x1, y1 = float(point['x1']), float(point['y1'])
                x2, y2 = float(point['x2']), float(point['y2'])
            except (KeyError, ValueError, TypeError):
                continue  # Skip invalid segments

            length = math.hypot(x2 - x1, y2 - y1)
            if length == 0:
                continue

            # Ensure the capping size is less than or equal to half the segment length
            effective_line_length = min(line_length, length / 2)
            dx, dy = (x2 - x1) / length, (y2 - y1) / length

            # Start cap line
            start_end = Vector2d(x1 + effective_line_length * dx, y1 + effective_line_length * dy)
            start_line = Line.new(Vector2d(x1, y1), start_end)
            cap_group.add(start_line)

            # End cap line
            end_start = Vector2d(x2 - effective_line_length * dx, y2 - effective_line_length * dy)
            end_line = Line.new(Vector2d(x2, y2), end_start)
            cap_group.add(end_line)

    


if __name__ == "__main__":
    ConnectThatDotExtension().run()
