from collections import defaultdict


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
        self.r = radius
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
        sx, sy = qx // self.r, qy // self.r
        neighbor_squares = [(sx + i, sy + j) for i in [-1, 0, 1] for j in [-1, 0, 1]]
        for square in neighbor_squares:
            for x, y in self.grid_map[square]:
                if (x, y) != (qx, qy) and (qx - x) ** 2 + (qy - y) ** 2 <= self.r**2:
                    neighbors.append((x, y))
        return neighbors

    def evaluate_points(self):
        """
        Evaluates the points and returns their averaged coordinates.

        Returns:
            list: A list of (x, y) coordinates representing the averaged points.
        """
        averaged_points = []
        for point in self.points:
            neighbors = self.query(*point)
            if neighbors:
                # Compute the average coordinates of the point and its neighbors
                avg_x = (point[0] + sum(n[0] for n in neighbors)) / (len(neighbors) + 1)
                avg_y = (point[1] + sum(n[1] for n in neighbors)) / (len(neighbors) + 1)
                averaged_points.append((avg_x, avg_y))
            else:
                averaged_points.append(point)
        return averaged_points
