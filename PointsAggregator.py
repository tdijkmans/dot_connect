from collections import defaultdict

import inkex


class PointsAggregator:
    """
    A class that finds the neighbors of given points within a specified radius.

    Args:
        points (list): A list of (x, y) coordinates representing the points.
        r (float): The radius within which to search for neighbors.

    Attributes:
        points (list): A list of (x, y) coordinates representing the points.
        r (float): The radius within which to search for neighbors.
        grid_map (defaultdict): A dictionary that maps grid keys to a list of points.

    Methods:
        query(qx, qy): Returns the neighbors of a given point (qx, qy).
        evaluate_points(): Evaluates the points and returns their averaged coordinates.
    """

    def __init__(self, points, radius: int):
        self.points = points
        self.radius = radius
        self.grid_map = defaultdict(lambda: [])
        for x, y in points:
            key = (x // radius, y // radius)
            self.grid_map[key].append((x, y))

    def query(self, qx, qy):
        """
        Returns the neighbors of a given point (qx, qy).

        Args:
            qx (float): The x-coordinate of the query point.
            qy (float): The y-coordinate of the query point.

        Returns:
            list: A list of (x, y) coordinates representing the neighbors.
        """
        neighbors = []
        sx, sy = qx // self.radius, qy // self.radius
        neighbor_squares = [(sx + i, sy + j) for i in [-1, 0, 1] for j in [-1, 0, 1]]
        for square in neighbor_squares:
            for x, y in self.grid_map[square]:
                if (x, y) != (qx, qy) and (qx - x) ** 2 + (
                    qy - y
                ) ** 2 <= self.radius**2:
                    neighbors.append((x, y))

        return neighbors

    def evaluate_points(self):
        """
        Evaluates the points and returns their averaged coordinates.

        Returns:
            list: A list of (x, y) coordinates representing the averaged points.
        """
        averaged_points = []
        neighbors_merged = False
        duplicates_merged = False
        for i in range(len(self.points)):
            current_point = self.points[i]
            next_point = self.points[i + 1] if i + 1 < len(self.points) else None
            point = current_point
            if next_point and current_point == next_point:
                duplicates_merged = True
                continue
            neighbors = self.query(*point)
            if neighbors:
                # Compute the average coordinates of the point and its neighbors
                neighbors_merged = True
                avg_x = (point[0] + sum(n[0] for n in neighbors)) / (len(neighbors) + 1)
                avg_y = (point[1] + sum(n[1] for n in neighbors)) / (len(neighbors) + 1)
                averaged_points.append((avg_x, avg_y))
            else:
                averaged_points.append(point)

        # Original number of points to the new number of points
        inkex.debug(
            f"Original number of points: {len(self.points)}, New number of points: {len(averaged_points)}, Neighbors merged: {neighbors_merged}, Duplicates merged: {duplicates_merged}"
        )

        return averaged_points, (neighbors_merged or duplicates_merged)
