import inkex
from inkex import NSS


class PublishPuzzleExtension(inkex.EffectExtension):
    """Publish puzzle extension"""

    def effect(self):
        """This is the main function of the extension"""

        # Get the selected solution layer
        solution_layer = self.svg.getElementById("solution_layer")
        solution_layer.set("display", "none")

        # Get all circle elements
        xpath = "//svg:circle[@style and contains(@style, 'fill: #000000')]"
        circle_elements = self.svg.xpath(xpath, namespaces=NSS)
        for circle in circle_elements:
            circle.style["stroke"] = "black"


if __name__ == "__main__":
    PublishPuzzleExtension().run()
