import inkex
from inkex import NSS, AbortExtension
from inkex.elements import PathElement
from inkex.elements import Line
from inkex.localization import inkex_gettext as _
from inkex import Vector2d
from inkex.elements import Group
from inkex import debug
from inkex.transforms import ImmutableVector2d
import json
from collections import defaultdict
import math

class ConvertPathExtension(inkex.EffectExtension):
    """Find Eularian to separate line segments"""

    def effect(self):
        """This is the main function of the extension"""

        # Dictionary to store the graph structure
        graph = {}
        line_segments = []

        # Create a new group to hold the line elements
        lines_group = self.svg.add(Group())
        lines_group.set("id", "lines_group")
        lines_group.set("style", "stroke:#000000;fill:none;stroke-width:1pt")

        # Get the target paths from the selection
        target_paths:list[PathElement] = list(self.svg.selection.filter(PathElement))
        if not target_paths:
            raise AbortExtension(_("Please select at least one path object."))
        
        # Process each path element
        streets = self.convert_path_to_lines(target_paths[0], lines_group, graph, line_segments)

        # Function to calculate Euclidean distance

        def calc_euclidean_distance(x1, y1, x2, y2):
            return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

        # Create a graph as an adjacency list
        graph = defaultdict(list)

        for coordinate in streets:
            x1, y1, x2, y2 = coordinate['x1'], coordinate['y1'], coordinate['x2'], coordinate['y2']
            distance = calc_euclidean_distance(x1, y1, x2, y2)
            
            # Add edges to the graph (both directions for undirected graph)
            graph[(x1, y1)].append(((x2, y2), distance))
            graph[(x2, y2)].append(((x1, y1), distance))
    
        # Convert the graph to a dictionary with string keys for JSON serialization
        graph_serializable = {str(key): value for key, value in graph.items()}

        # Write the graph to a JSON file
        with open("ser_graph.json", "w") as f:
           json.dump(graph_serializable, f, indent=4)

        # Find Eulerian path or near-optimal route
        eulerian_path = self.find_eulerian_path(graph)
        debug(f"Eulerian path: {eulerian_path}")
        with open("eulerian_path.json", "w") as f:
            json.dump(eulerian_path, f, indent=4)
        self.draw_path_or_route(eulerian_path, "eulerian_path_group")
       

    
    def draw_path_or_route(self, path, group_id):
        """Draw the Eulerian path or near-optimal route on the SVG"""
        # Create a new group to hold the path or route elements
        path_group = self.svg.add(Group())
        path_group.set("id", group_id)
        path_group.set("style", "stroke:#FF0000;fill:none;stroke-width:1pt")

        # Draw the path or route
        for i in range(len(path) - 1):
            start = Vector2d(*path[i])
            end = Vector2d(*path[i + 1])
            line = Line.new(start, end, id=f"{group_id}_line_{i + 1}")
            path_group.add(line)

    def find_eulerian_path(self, graph):
        """Find an Eulerian path in the graph"""
        # Count the degrees of each vertex
        degree_count = defaultdict(int)
        for node, neighbors in graph.items():
            degree_count[node] += len(neighbors)
            for neighbor, _ in neighbors:
                degree_count[neighbor] += 1

        # Find the start node for the Eulerian path
        start_node = None
        odd_degree_nodes = [node for node, degree in degree_count.items() if degree % 2 != 0]
        if len(odd_degree_nodes) == 0:
            # Eulerian circuit
            start_node = next(iter(graph))
        elif len(odd_degree_nodes) == 2:
            # Eulerian path
            start_node = odd_degree_nodes[0]
        else:
            # No Eulerian path
            return None

        # Define the function to find the Eulerian path using Hierholzer's algorithm
        def find_path(start_node):
            stack = [start_node]
            path = []
            while stack:
                node = stack[-1]
                if graph[node]:
                    next_node, _ = graph[node].pop()
                    stack.append(next_node)
                    graph[next_node].remove((node, _))
                else:
                    path.append(stack.pop())
            return path

        # Call the `find_path` function to generate and return the Eulerian path
        return find_path(start_node)


    def find_near_optimal_route(self, graph):
        """Find a near-optimal route that visits each edge at least once"""
        # Use a heuristic to find a near-optimal route
        visited_edges = set()
        route = []

        def dfs(node):
            for neighbor, _ in graph[node]:
                edge = frozenset([node, neighbor])
                if edge not in visited_edges:
                    visited_edges.add(edge)
                    dfs(neighbor)
            route.append(node)

        start_node = next(iter(graph))
        dfs(start_node)
        return route[::-1]

    
    def convert_path_to_lines(self, path:PathElement, lines_group:Group, graph:dict, line_segments:list):
        """Convert a path element to a group of line elements"""
        # Get the path data from the path element and break it apart
        segments = path.path.to_non_shorthand().break_apart()

        # Set to keep track of unique segments (undirected edges)
        unique_segments = set()
       
        # Process the segments to create line elements
        for coordinates in segments:
            # Ensure the segment has at least two points
            if len(coordinates) < 2:
                continue
            
            # Use the first point as the start
            start = Vector2d(coordinates[0].x, coordinates[0].y)
            for i in range(1, len(coordinates)):
                end = Vector2d(coordinates[i].x, coordinates[i].y)

                def make_edge(point1, point2):
                # Return a frozenset of tuples for undirected edge comparison
                    rounded_edge = [(round(point1.x), round(point1.y)), (round(point2.x), round(point2.y))]
                    return frozenset([tuple(edge) for edge in rounded_edge])

                # Create an undirected edge between the start and end points
                edge = make_edge(start, end)

                # Skip duplicate segments
                if edge in unique_segments:
                    
                    start = end
                    continue
                
                unique_segments.add(edge)

                # Add the edge to the graph
                if start not in graph:
                    graph[start] = []
                if end not in graph:
                    graph[end] = []
                graph[start].append(end)
                graph[end].append(start)
                
                # Create the Line element using the new method
                current_id = len(line_segments) + 1
                line = Line.new(start, end,id=f"line_{current_id}")
                lines_group.add(line)                

                # Store the line segment and associated line element
                line_segments.append((start, end, line))

                # Move the start point to the current end point for the next line
                start = end

        # JUST SOME DEBUGGING CODE TO PRINT THE GRAPH

        # Write all line segments to a JSON file, in graph format
        formatted_line_segments = [{"x1": start.x,"y1": start.y,"x2": end.x,"y2": end.y} for start, end, _ in line_segments]
        with open("line_segments.json", "w") as f:
            json.dump(formatted_line_segments, f, indent=4)
        
        # write graph to  json file
        formatted_graph = {str(k): [str(v) for v in values] for k, values in graph.items()}
        # Write to JSON file
        with open("graph.json", "w") as f:
            json.dump(formatted_graph, f, indent=4)

        return formatted_line_segments

    def euclidean_distance(self, point1:Vector2d, point2:Vector2d):
        """Calculate the Euclidean distance between two points"""
        return ((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2) ** 0.5 


if __name__ == "__main__":
    ConvertPathExtension().run()

