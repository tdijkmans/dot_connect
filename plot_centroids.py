# Import required modules

from inkex import Boolean, EffectExtension

from CentroidPlotter import CentroidPlotter


class CentroidPlotExtension(EffectExtension):
    def add_arguments(self, pars):
        pars.add_argument("--tab", help="The selected UI-tab when OK was pressed")
        pars.add_argument(
            "--plot_centroids",
            type=Boolean,
            help="Plot centroids of filled elements",
            default=True,
        )

        pars.add_argument(
            "--centroids_layer",
            help="Layer to plot the centroids",
            default="centroids_layer",
        )

        pars.add_argument(
            "--solution_layer",
            help="Layer to plot the solution",
            default="solution_layer",
        )

        pars.add_argument(
            "--clearance",
            type=int,
            help="Clearance around the centroid",
            default=4,
        )

        pars.add_argument(
            "--fraction",
            type=int,
            help="Fraction of the bounding box to search",
            default=20,
        )

        pars.add_argument(
            "--plane_fill",
            help="Fill color of the plane",
            default="#808080",
            type=str,
        )

    def effect(self):
        so = self.options
        ca = CentroidPlotter(self.svg)
        ca.plot_puzzle_centroids(
            so.centroids_layer,
            so.solution_layer,
            so.clearance,
            so.fraction,
            so.plane_fill,
        )


if __name__ == "__main__":
    CentroidPlotExtension().run()
