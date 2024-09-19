import inkex
from inkex import NSS, AbortExtension
from inkex.elements import PathElement
from inkex.elements import Line
from inkex.localization import inkex_gettext as _
from inkex import Vector2d
from inkex.elements import Group

class ConvertPathExtension(inkex.EffectExtension):
    """Convert path to separate line segments"""

    def effect(self):
        """This is the main function of the extension"""

        # Get the target paths from the selection or fallback to an element with id 'source_path'
        target_paths = list(self.svg.selection.filter(PathElement))
        if not target_paths:
            # Try to get 'source_path' by ID if nothing is selected
            target_path = self.svg.getElementById("source_path")
            if target_path:
                target_paths.append(target_path)
            else:
                # Try to get the first path element in the document if 'source_path' is not found
                target_paths = self.document.xpath("//svg:path", namespaces=inkex.NSS)
        
        if not target_paths:
            raise AbortExtension(_("Please select at least one path object."))
        
        lines_group = self.svg.add(Group())
        lines_group.set("id", "lines_group")

        for target_path in target_paths:
            # Get the path data
            path_data = target_path.path.to_absolute()
            
            # Split the path into segments
            segments = path_data.break_apart()
            inkex.debug(segments)  # Debug the segments to see the structure

            # Process the segments to create line elements
            for segment in segments:
                # Ensure the segment has at least two points
                if len(segment) < 2:
                    continue
                
                # Use the first point as the start
                start = Vector2d(segment[0].x, segment[0].y)

                # Iterate over the rest of the points to create lines
                for i in range(1, len(segment)):
                    end = Vector2d(segment[i].x, segment[i].y)
                    
                    # Create the Line element using the new method
                    line = Line.new(start, end)
                    line.style = "stroke:#000000;fill:none;stroke-width:1pt"
                    
                    # Add the new line to the current layer
                    self.svg.get_current_layer().add(line)
                    lines_group.add(line)

                    # Move the start point to the current end point for the next line
                    start = end

if __name__ == "__main__":
    ConvertPathExtension().run()
