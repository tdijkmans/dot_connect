import inkex
from inkex import AbortExtension
from inkex.elements import PathElement, Group
from LineBreaker import LineBreaker

class BreakUpLinesExtension(inkex.EffectExtension):
    """Break up a path into line segments and add caps at the start and end."""

    def add_arguments(self, pars):
        """Add custom arguments to the parser."""
        pars.add_argument("--line_width", type=float, default=1.0, help="Width of the line")
        pars.add_argument("--save_json", type=inkex.Boolean, default=False, help="Save line segments to JSON")

        pars.add_argument("--tab", help="The selected UI-tab when OK was pressed")

    def effect(self):
        """Main function."""
        # Retrieve parameters from GUI
        line_width = self.options.line_width
        save_json = self.options.save_json


        # Create a new group to hold the line elements
        lines_group = self.svg.get_current_layer().add(
            Group(id="lines_group", style=f"stroke:#000000;fill:none;stroke-width:{line_width};")
        )

        # Get selected paths
        target_paths = list(self.svg.selection.filter(PathElement))
        if not target_paths:
            raise AbortExtension("Please select at least one path object.")
        
        for path in target_paths:
            line_breaker = LineBreaker(path, lines_group)
            line_segments = line_breaker.convert_path_to_lines()
            if save_json:
                line_breaker.save_line_segments(line_segments)

        
    


    
if __name__ == "__main__":
    BreakUpLinesExtension().run()
