# Import required modules
import random

import inkex
from inkex import (
    Circle,
    Layer,
    Style,
)
from inkex.paths import Path


class CentroidPlotter:
    def __init__(self, svg):
        self.svg = svg

    def plot_puzzle_centroids(
        self,
        centroids_layer,
        solution_layer,
        clearance,
        fraction,
        plane_fill,
    ):
        """Plot the centroids of filled elements in the puzzle."""
        c_layer, s_layer = self.ensure_layers_exist(centroids_layer, solution_layer)

        hex_color = self.rgb_to_hex(plane_fill)
        planes_to_color = self.get_planes_to_color(hex_color)

        for index, plane in enumerate(planes_to_color):
            transformed_path = plane.path.transform(plane.composed_transform())
            endpoints = transformed_path.end_points
            bounding_box = transformed_path.bounding_box()
            path_string = plane.get("d")

            x, y = self.calculate_centroid(endpoints)
            id = index + 1
            inside = self.has_clearance(
                x, y, path_string, clearance
            ) and self.point_inside_path(x, y, path_string)

            if not inside:
                # Use the bounding box center as the initial position
                x, y = bounding_box.center

                # Check if the initial position is inside the path
                inside = self.has_clearance(
                    x, y, path_string, clearance
                ) and self.point_inside_path(x, y, path_string)

                # If not, adjust the position within a grid pattern
                if not inside:
                    x, y, inside = self.adjust_position_in_grid(
                        x, y, bounding_box, path_string, clearance, fraction
                    )

            centroid = self.createCircle(x, y, 1, f"plane_centroid_{id}")
            plane, centroid = self.set_element_attributes(plane, centroid, id, inside)
            c_layer.append(centroid)
            s_layer.append(plane)

    def get_planes_to_color(self, hex_color):
        xpath_query = f".//*[@style and contains(@style, 'fill:{hex_color}')]"
        return self.svg.xpath(xpath_query, namespaces=inkex.NSS)

    def rgb_to_hex(self, rgb_color):
        return "#{:02x}{:02x}{:02x}".format(*inkex.Color(rgb_color).to_rgb())

    def ensure_layers_exist(self, centroids_layer, solution_layer):
        for layer in [
            solution_layer,
            centroids_layer,
        ]:
            element = self.svg.getElementById(layer)
            if element is None:
                new_layer = self.svg.add(Layer())
                new_layer.set("id", layer)
                new_layer.set("inkscape:label", layer)

        return self.svg.getElementById(centroids_layer), self.svg.getElementById(
            solution_layer
        )

    def adjust_position_in_grid(
        self, x, y, bounding_box, path_string, clearance, fraction
    ):
        """Adjust the position within a grid pattern around the bounding box center."""
        # Define the step sizes for grid search
        step_size_x = bounding_box.width / fraction
        step_size_y = bounding_box.height / fraction

        # Define the range of positions to check around the center
        search_range = range(-5, 6)

        # Iterate over a grid of positions around the bounding box center
        for dx in search_range:
            for dy in search_range:
                # Calculate the new position
                new_x = x + dx * step_size_x
                new_y = y + dy * step_size_y

                # Check if the new position is inside the path
                if self.point_inside_path(
                    new_x,
                    new_y,
                    path_string,
                    # Check if points around the new position have clearance
                ) and self.has_clearance(new_x, new_y, path_string, clearance):
                    # If yes, update the position and stop searching
                    x, y = new_x, new_y
                    return x, y, True

        # If no suitable position found, return the original position
        return x, y, False

    def has_clearance(self, x, y, path_string, clearance):
        """Check if the point has clearance around it."""

        return all(
            self.point_inside_path(x + i * clearance, y + j * clearance, path_string)
            for i in [-1, 0, 1]
            for j in [-1, 0, 1]
        )

    def createCircle(self, x: int, y: int, radius: int, id: str, fill="#000000"):
        circle = Circle(cx=str(x), cy=str(y), r=str(radius))
        circle.style = Style(
            {
                "stroke": fill,
                "fill": None,
            }
        )
        circle.set("id", id)
        return circle

    def calculate_centroid(self, endpoints):
        x_coords = []
        y_coords = []
        for _, (x, y) in enumerate(endpoints):
            x_coords.append(x)
            y_coords.append(y)

        if not x_coords or not y_coords:
            return None, None
        centroid_x = sum(x_coords) / len(x_coords)
        centroid_y = sum(y_coords) / len(y_coords)
        return centroid_x, centroid_y

    def set_element_attributes(self, plane, centroid, id, inside):
        plane.set("id", f"source_plane_{id}")
        plane.style["stroke"] = None
        centroid.style["stroke"] = "#000000"
        centroid.style["stroke-width"] = "0.5"
        bright_colors = [
            "#FF0000",
            "#FFA500",
            "#FFFF00",
            "#00FF00",
            "#0000FF",
            "#4B0082",
            "#9400D3",
            "#FF1493",
            "#00FFFF",
            "#FF00FF",
        ]

        random_color = random.choice(bright_colors)
        centroid.style["stroke"] = random_color
        plane.style["stroke"] = random_color
        plane.style["stroke-width"] = "2"

        centroid.style["fill"] = "#ffffff"
        plane.style["fill"] = "#808080"
        return plane, centroid

    def point_inside_path(self, x, y, path):
        """Check if a point is inside the closed path"""
        # Parse the path string
        parsedPath = Path(path)

        # Get the end points of the path
        coords = list(parsedPath.end_points)

        # Calculate the number of crossings
        num_crossings = 0
        for i in range(len(coords)):
            x1, y1 = coords[i]
            x2, y2 = coords[(i + 1) % len(coords)]  # Wrap around for the last point
            if (y1 < y and y2 >= y) or (y2 < y and y1 >= y):
                if x1 + (y - y1) / (y2 - y1) * (x2 - x1) < x:
                    num_crossings += 1

        # Check if the number of crossings is odd
        return num_crossings % 2 == 1
