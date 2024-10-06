import inkex
from inkex import NSS, AbortExtension
from inkex.elements import PathElement
from inkex.localization import inkex_gettext as _
from inkex.paths import Path

from PointsAggregator import PointsAggregator


class AggregatePointsExtension(inkex.EffectExtension):
    """Inkex effect extension to aggregate points"""

    def add_arguments(self, pars):
        pars.add_argument(
            "--aggregation_radius",
            type=int,
            default=5,
            help="The radius of the neighborhood to aggregate points (default: 5)",
        )

        pars.add_argument("--tab", help="The selected UI-tab when OK was pressed")

    def effect(self):
        """This is the main function of the extension"""
        options = self.options

        target_paths: list[PathElement] = self.svg.selection.filter(PathElement) or [
            self.svg.getElementById("source_path")
            or self.document.xpath("//svg:path", namespaces=NSS)[0]
        ]

        if not target_paths:
            raise AbortExtension(_("Please select at least one path object."))

        for target_paths in target_paths:
            self.aggregate_points(target_paths, options.aggregation_radius)
            # move the original path to the left
            target_paths.transform = "translate(-20,0)"
            target_paths.set("id", "original_path")
            target_paths.set("style", "stroke:#D3D3D3;fill:none;stroke-width:1pt")

    def aggregate_points(self, element: PathElement, aggregation_radius=5):
        """Find the neighbors of the points in the path element and aggregate them"""
        path: Path = element.path.transform(element.composed_transform())
        points = path.to_absolute().control_points

        coords = []
        for x, y in points:
            coords.append((x, y))

        nf = PointsAggregator(coords, aggregation_radius)
        averaged_points, neighbords_merged = nf.evaluate_points()

        # # create new path with averaged points
        new_path = PathElement()
        new_path.path = Path(averaged_points)
        new_path.set("id", "aggregated_path")

        if neighbords_merged:
            # color green  if neighbors merged
            new_path.set("style", "stroke:#00ff00;fill:none;stroke-width:1pt")
        else:
            # color red if neighbors not merged
            new_path.set("style", "stroke:#ff0000;fill:none;stroke-width:1pt")

        self.svg.append(new_path)


if __name__ == "__main__":
    AggregatePointsExtension().run()
