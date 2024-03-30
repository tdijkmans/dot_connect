import inkex
from inkex import AbortExtension
from inkex.elements import PathElement
from inkex.localization import inkex_gettext as _
from inkex.paths import Path

from NeigborFinder import NearNeighborFinder


class AggregatePointsExtension(inkex.EffectExtension):
    """Inkex effect extension to aggregate points"""

    def add_arguments(self, pars):
        pars.add_argument(
            "--neighbor_radius",
            type=float,
            default=5.0,
            help="The radius of the neighborhood to aggregate points (default: 5)",
        )

        pars.add_argument("--tab", help="The selected UI-tab when OK was pressed")

    def effect(self):
        """This is the main function of the extension"""
        options = self.options

        selected_paths: list[PathElement] = self.svg.selection.filter(PathElement)

        if not selected_paths:
            raise AbortExtension(_("Please select at least one path object."))

        for path_element in selected_paths:
            self.aggregate_points(path_element, options.neighbor_radius)
            path_element.transform = "translate(-20,0)"
            path_element.set("id", "original_path")
            path_element.set("style", "stroke:#D3D3D3;fill:none;stroke-width:1pt")

    def aggregate_points(self, element: PathElement, r=5.0):
        """Find the neighbors of the points in the path element and aggregate them"""
        path: Path = element.path.transform(element.composed_transform())
        points = path.to_absolute().control_points

        coords = []
        for x, y in points:
            coords.append((x, y))

        nf = NearNeighborFinder(coords, r)
        averaged_points = nf.evaluate_points()

        # # create new path with averaged points
        new_path = PathElement()
        new_path.path = Path(averaged_points)
        new_path.set("id", "aggregated_points")

        new_path.set("style", "stroke:#ff0000;fill:none;stroke-width:1pt")
        self.svg.append(new_path)


if __name__ == "__main__":
    AggregatePointsExtension().run()
