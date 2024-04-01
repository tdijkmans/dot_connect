# Import required modules
import random

import inkex
from inkex import (
    Boolean,
    Circle,
    EffectExtension,
    Style,
)
from inkex.paths import Path


# Create a class named NumberDots that inherits from inkex.EffectExtension
class AddPointWithinPath(EffectExtension):
    plane_fill = "#808080"

    def add_arguments(self, pars):
        pars.add_argument("--tab", help="The selected UI-tab when OK was pressed")
        pars.add_argument(
            "--plot_centroids",
            type=Boolean,
            help="Plot centroids of filled elements",
            default=True,
        )

    def effect(self):
        self.plot_puzzle_centroids(
            "centroids_layer",
            "solution_layer",
        )

    def plot_puzzle_centroids(self, centroids_layer, solutions_layer):
        xpath_query = f".//*[@style and contains(@style, 'fill:{self.plane_fill}')]"
        planes_to_color = self.svg.xpath(xpath_query, namespaces=inkex.NSS)

        if planes_to_color is None or len(planes_to_color) == 0:
            inkex.errormsg("No filled elements found")
            pass

        for index, plane in enumerate(planes_to_color):
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

            inside = self.point_inside_path(centroid_x, centroid_y, plane.get("d"))

            # Plot centroid
            centroid = self.createCircle(
                centroid_x, centroid_y, 1, f"plane_centroid_{id}"
            )
            plane.set("id", f"source_plane_{id}")
            plane.style["stroke"] = None
            centroid.style["stroke"] = "#000000"
            centroid.style["stroke-width"] = "0.5"
            if not inside:
                five_bright_colors = [
                    "#FF0000",
                    "#00FF00",
                    "#0000FF",
                    "#FFFF00",
                    "#00FFFF",
                ]
                random_color = random.choice(five_bright_colors)
                centroid.style["stroke"] = random_color
                plane.style["stroke"] = random_color
                plane.style["stroke-width"] = "2"

            centroid.style["fill"] = "#ffffff"
            plane.style["fill"] = "#808080"
            self.svg.getElementById(centroids_layer).append(centroid)
            self.svg.getElementById(solutions_layer).append(plane)

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


if __name__ == "__main__":
    AddPointWithinPath().run()
