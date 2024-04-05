from inkex import Boolean


def add_arguments(pars):
    """Add command-line arguments for the extension"""
    pars.add_argument("--fontsize", default="8px", help="Size of node labels")
    pars.add_argument(
        "--page_margin",
        default="7mm 7mm 7mm 7mm",
        help="Page margin. Default is 7mm",
    )
    pars.add_argument("--fontweight", default="normal", help="Weight of node labels")
    pars.add_argument(
        "--start", type=int, default=1, help="First number in the sequence"
    )
    pars.add_argument("--tab", help="The selected UI-tab when OK was pressed")

    pars.add_argument(
        "--plot_centroids",
        type=Boolean,
        help="Plot centroids of filled elements",
        default=True,
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

    pars.add_argument(
        "--plot_dots",
        type=Boolean,
        help="Plot dots",
        default=True,
    )

    pars.add_argument(
        "--plot_sequence",
        type=Boolean,
        help="Plot sequence",
        default=True,
    )

    pars.add_argument(
        "--plot_reference_sequence",
        type=Boolean,
        help="Plot reference sequence",
        default=False,
    )

    pars.add_argument(
        "--minimal_distance",
        type=int,
        help="Minimal distance between dots",
        default=6,
    )

    pars.add_argument(
        "--replace_dots",
        type=Boolean,
        help="Replace the dots",
        default=True,
    )

    pars.add_argument(
        "--replace_centroids",
        type=Boolean,
        help="Replace the centroids",
        default=False,
    )

    pars.add_argument(
        "--replace_instructions",
        type=Boolean,
        help="Replace the text",
        default=True,
    )

    pars.add_argument(
        "--title",
        type=str,
        help="Title of the puzzle",
        default="",
    )

    pars.add_argument(
        "--subtitle",
        type=str,
        help="Subtitle of the puzzle",
        default="",
    )

    pars.add_argument(
        "--plot_footer",
        type=Boolean,
        help="Add footer",
        default=False,
    )

    pars.add_argument(
        "--copyright_text",
        type=str,
        help="Text for the copyright",
        default="Copyright © Polydot Puzzles 2024",
    )

    pars.add_argument(
        "--caption",
        type=str,
        help="Caption for the puzzle",
        default="Paste your caption here",
    )

    pars.add_argument(
        "--paper_size",
        type=str,
        help="Size of the paper",
        default="A4",
    )
