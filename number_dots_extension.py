import math

import inkex
from inkex import Circle, TextElement
from inkex.localization import inkex_gettext as _


class NumberDots(inkex.EffectExtension):
    """Replace the selection's nodes with numbered dots according to the options"""

    def add_arguments(self, pars):
        pars.add_argument(
            "--dotsize", default="10px", help="Size of the dots on the path nodes"
        )
        pars.add_argument("--fontsize", default="6px", help="Size of node labels")
        pars.add_argument(
            "--start", type=int, default=1, help="First number in the sequence"
        )
        pars.add_argument("--tab", help="The selected UI-tab when OK was pressed")

    def effect(self):
        filtered = self.svg.selection.filter(inkex.PathElement)
        if not filtered:
            raise inkex.AbortExtension(_("Please select at least one path object."))
        for node in filtered:
            self.traverse_node(node)

    def traverse_node(self, node: inkex.PathElement):
        group: inkex.Group = node.getparent().add(inkex.Group())

        dot_group = group.add(inkex.Group())
        dot_group.set("id", "dot_group")
        num_group = group.add(inkex.Group())
        num_group.set("id", "num_group")
        alpha_numeric_group = group.add(inkex.Group())
        alpha_numeric_group.set("id", "alpha_numeric_group")

        path_trans_applied = node.path.transform(node.composed_transform())
        group.transform = -node.getparent().composed_transform()

        end_points_list = list(path_trans_applied.end_points)
        num_points = len(end_points_list)

        for step, (x, y) in enumerate(path_trans_applied.end_points):
            dot_number = self.options.start + step
            circle = dot_group.add(
                Circle(
                    cx=str(x),
                    cy=str(y),
                    r=str(self.svg.unittouu(self.options.dotsize) / 2),
                )
            )

            dot_style = inkex.Style(
                {
                    "stroke": "#ffffff",
                    "stroke-width": "0.1pt",
                    "fill": "#000000",
                }
            )

            dot_style_start_end = inkex.Style(
                {
                    "stroke": "#000000",
                    "stroke-width": "0.1pt",
                    "fill": "#ffffff",
                }
            )

            if step == 0 or step == num_points - 1:
                circle.style = dot_style_start_end
            else:
                circle.style = dot_style
            circle.set("id", f"dot_{dot_number}")

            num_group.append(
                self.add_text(
                    x + (self.svg.unittouu(self.options.dotsize) / 2),
                    y - (self.svg.unittouu(self.options.dotsize) / 2),
                    dot_number,
                    f"num_{dot_number}",
                )
            )
            alpha_numeric_label = self.get_alpha_numeric(self.options.start + step)
            alpha_numeric_group.append(
                self.add_text(
                    x + (self.svg.unittouu(self.options.dotsize) / 2),
                    y + (self.svg.unittouu(self.options.dotsize) / 2),
                    alpha_numeric_label,
                    f"alpha_numeric_{alpha_numeric_label}",
                )
            )

        node.set("id", "source_path")

    def add_text(self, x, y, text, id):
        """Add a text label at the given location"""
        elem = TextElement(x=str(x), y=str(y))
        elem.text = str(text)
        elem.set("id", id)
        elem.style = {
            "font-size": self.svg.unittouu(self.options.fontsize),
            "font-family": "Arial",
            "fill-opacity": "1.0",
            "font-weight": "bold",
            "font-style": "normal",
            "fill": "#000",
        }
        return elem

    def get_alpha_numeric(self, number):
        alpha_numeric_array = [letter for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"]

        first_letter_index = (number - 1) // 26
        second_letter_index = (number - 1) % 26

        first_letter = alpha_numeric_array[
            first_letter_index % len(alpha_numeric_array)
        ]
        second_letter = alpha_numeric_array[second_letter_index]

        return f"{first_letter}{second_letter}"


if __name__ == "__main__":
    NumberDots().run()
