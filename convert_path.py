import inkex
from inkex import NSS, AbortExtension
from inkex.elements import PathElement
from inkex.elements import Line
from inkex.localization import inkex_gettext as _
from inkex import Vector2d
from inkex.elements import Group
from inkex import debug
from inkex.transforms import ImmutableVector2d

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



        # Get the target paths from the selection or fallback to an element with id 'source_path'
        target_paths:list[PathElement] = list(self.svg.selection.filter(PathElement))
        if not target_paths:
            # Try to get 'source_path' by ID if nothing is selected
            target_path = self.svg.getElementById("source_path")
            if target_path:
                target_paths.append(target_path)
            else:
                # Try to get the first path element in the document if 'source_path' is not found
                target_paths = self.document.xpath("//svg:path", namespaces=inkex.NSS)
        
        if not target_paths:
            raise AbortExtension(_("Please select at least one path object."))
        
        # Process each path element
        for target_path in target_paths:
            self.convert_path_to_lines(target_path, lines_group, graph, line_segments)

        # Add edges to make the graph Eulerian if needed
        self.make_path_eulerian_with_revisits(graph)

        # Find the Eulerian circuit
        eulerian_circuit = self.find_eulerian_circuit_with_revisits(graph)

         # Create the path data string for the Eulerian path
        path_data = self.create_path_data(eulerian_circuit)

         # Add the Eulerian path as a new path element
        eulerian_path = PathElement()
        eulerian_path.set_id('eulerian_path')
        eulerian_path.set('d', path_data)
        eulerian_path.style = "stroke:#FF0000;fill:none;stroke-width:2pt"
        self.svg.add(eulerian_path)

        # Traverse the Eulerian circuit and add traversal order to line elements
        for step, (u, v) in enumerate(eulerian_circuit):
            for idx, (start, end, line) in enumerate(line_segments):
                if (u, v) == (start, end) or (v, u) == (start, end):
                    # Set the ID to represent the traversal step
                    line.set('id', f'traverse-step-{idx + 1}')
                    break
    
    

    
    def convert_path_to_lines(self, path:PathElement, lines_group:Group, graph:dict, line_segments:list):
        """Convert a path element to a group of line elements"""
        # Get the path data
        path_data = path.path.to_non_shorthand()
        
        # Split the path into segments
        segments = path_data.break_apart()

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
                line = Line.new(start, end)
                line.style = "stroke:#000000;fill:none;stroke-width:1pt"
                lines_group.add(line)

                # Store the line segment and associated line element
                line_segments.append((start, end, line))

                # Move the start point to the current end point for the next line
                start = end

    def create_path_data(self, eulerian_circuit:list[tuple[Vector2d, Vector2d]]):
        """Create the path data string for the Eulerian path"""
        if not eulerian_circuit:
            return ""

        path_data = []
        start_point = eulerian_circuit[0][0]
        path_data.append(f"M {start_point[0]} {start_point[1]}")
        
        for u, v in eulerian_circuit:
            path_data.append(f"L {v[0]} {v[1]}")
        
        return " ".join(path_data)
    
    def make_path_eulerian_with_revisits(self, graph:dict):
        """Identify where to revisit edges to make the graph Eulerian without adding new edges."""
        # Find odd degree vertices
        odd_degree_nodes = [node for node, neighbors in graph.items() if len(neighbors) % 2 != 0]

        # Find minimum cost pairing of odd degree vertices
        while len(odd_degree_nodes) > 1:
            node1 = odd_degree_nodes.pop()
            # Calculate distances to other odd-degree nodes
            distances = [(self.euclidean_distance(node1, node2), node2) for node2 in odd_degree_nodes]
            distances.sort(key=lambda x: x[0])  # Sort by distance
            _, node2 = distances[0]
            odd_degree_nodes.remove(node2)

            # Simulate edge revisit by marking the path for additional traversal
            # We won't modify the graph itself; we simply mark this pair for revisiting
            # Optionally, we can store this information for use in the circuit construction
            debug(f"Revisit edge between {node1} and {node2}")

    def find_eulerian_circuit_with_revisits(self, graph:dict):
            """Find Eulerian circuit with U-turns if necessary using Hierholzer's algorithm."""
        # Find all edges to traverse
            all_edges = {node: set(neighbors) for node, neighbors in graph.items()}
            start_node = next(iter(graph))
            circuit = []
            stack = [start_node]

            while stack:
                u = stack[-1]
                if all_edges[u]:
                    v = all_edges[u].pop()
                    all_edges[v].remove(u)  # Remove the edge in both directions
                    stack.append(v)
                else:
                    circuit.append(stack.pop())

            # Convert circuit to list of edges
            return [(circuit[i], circuit[i + 1]) for i in range(len(circuit) - 1)]

    def euclidean_distance(self, point1:Vector2d, point2:Vector2d):
        """Calculate the Euclidean distance between two points"""
        return ((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2) ** 0.5 


if __name__ == "__main__":
    ConvertPathExtension().run()

