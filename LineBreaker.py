from inkex.elements import PathElement, Line, Group
from inkex import Vector2d
import json


class LineBreaker:
    def __init__(self, path: PathElement, lines_group: Group, dot_connections: list = []):
        self.path = path
        self.lines_group = lines_group
        self.dot_connections = self.build_dot_connections(dot_connections)


    def build_dot_connections(self, dot_connections: list) -> dict:
        """Build a dictionary of dot connections for faster lookup."""
        return {
            (dot['x'], dot['y']): dot
            for dot in dot_connections
        }
    

    def plot_unique_lines(self,dot_connections:list) -> list:
        """Plot lines between connected dots, as specified in the dot_connections list."""
        dots = dot_connections
        unique_pairs = set()

        # Iterate over nodes, stopping before the last node to avoid out-of-range access
        for i in range(len(dots) - 1):
            # Get the coordinates of the start and end nodes
            startX1 = dots[i]['x']
            startY1 = dots[i]['y']
            endX1 = dots[i + 1]['x']
            endY1 = dots[i + 1]['y']
            startLetter = dots[i]['letter_label']
            endLetter = dots[i + 1]['letter_label']
            id = f"{startLetter}_{endLetter}"

            pair = tuple(sorted([startLetter, endLetter]))
            
            # Skip if the pair has already been processed
            if pair not in unique_pairs:
                unique_pairs.add(pair)


                # Create a new line connecting the dots
                line = Line.new(
                    Vector2d(startX1, startY1), Vector2d(endX1, endY1),
                    id=id
                )
                # Add metadata to the line
                line.set("data-start-dot", startLetter)
                line.set("data-end-dot", endLetter)

                # Add line to the lines_group
                self.lines_group.append(line)
            
        
        # Write unique pairs to a JSON file
            with open("unique_pairs.json", "w") as f:
                json.dump(list(unique_pairs), f)


    def convert_path_to_lines(self) -> list:
        """Convert a path element into line segments and store in a group."""
        graph = {}
        line_segments = []
        unique_segments = set()

        segments = self.path.path.to_non_shorthand().break_apart()

        coordinates = self.path.get_path()

        for coordinates in segments:
            if len(coordinates) < 2:
                continue

            start = Vector2d(coordinates[0].x, coordinates[0].y)
            for i in range(1, len(coordinates)):
                end = Vector2d(coordinates[i].x, coordinates[i].y)

                # Round coordinates once for efficiency
                rounded_start = (round(start.x), round(start.y))
                rounded_end = (round(end.x), round(end.y))

                # Create an edge as a frozenset to avoid duplicates
                edge = frozenset([rounded_start, rounded_end])

                if edge in unique_segments:
                    start = end
                    continue
                unique_segments.add(edge)

                graph.setdefault(rounded_start, []).append(rounded_end)
                graph.setdefault(rounded_end, []).append(rounded_start)

                current_id = len(line_segments) + 1
                formatted_id = str(current_id).zfill(3)

                # Get matching dots from the dictionary
                matching_start = self.dot_connections.get(rounded_start)
                matching_end = self.dot_connections.get(rounded_end)

                # Create the line with appropriate ID based on matched dots or coordinates
                if matching_start and matching_end:
                    start_dot_label = matching_start['letter_label']
                    end_dot_label = matching_end['letter_label']
                    
                    line = Line.new(
                        start, end,
                        id=f"{formatted_id}_{start_dot_label}_{end_dot_label}",
                    )
                    line.set("data-start-dot", start_dot_label)
                    line.set("data-end-dot", end_dot_label)
                    line.set("data-step", current_id)
                else:
                    line = Line.new(
                        start, end,
                        id=f"{formatted_id}_{rounded_start[0]}_{rounded_start[1]}_{rounded_end[0]}_{rounded_end[1]}",
                    )
                    
                self.lines_group.add(line)
                line_segments.append({
                    "x1": rounded_start[0],
                    "y1": rounded_start[1],
                    "x2": rounded_end[0],
                    "y2": rounded_end[1]
                })

                start = end

        return line_segments

    
    def save_line_segments(self, line_segments: list) -> bool:
        """Save line segments to a JSON file."""
        try:
            with open("line_segments.json", "w") as f:
                json.dump(line_segments, f)
        except Exception as e:
            return False
        return True
