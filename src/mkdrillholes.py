#!/usr/bin/env python3
"""Inkscape extension: draw evenly spaced holes with crosshairs on a circle."""
import math

import inkex
from inkex import Circle, Group, PathElement


class Mkdrillholes(inkex.EffectExtension):
    def add_arguments(self, pars):
        pars.add_argument("--hole_count", type=int, default=3)
        pars.add_argument("--distance_mode", default="distance_hole_to_hole")
        pars.add_argument("--distance", type=float, default=25.0)
        pars.add_argument("--diameter", type=float, default=5.0)
        pars.add_argument("--rotation", type=float, default=0.0)
        pars.add_argument("--crosshair", type=inkex.Boolean, default=True)
        pars.add_argument("--cross_size", type=float, default=3.0)
        pars.add_argument("--pitch_circle", type=inkex.Boolean, default=False)
        pars.add_argument("--pitch_circle_diameter", type=float, default=50.0)
        pars.add_argument("--center_hole", type=inkex.Boolean, default=False)
        pars.add_argument("--center_hole_diameter", type=float, default=5.0)
        pars.add_argument("--to_paths", type=inkex.Boolean, default=False)
        pars.add_argument("--unit", default="mm")

    def effect(self):
        u = self.svg.unittouu("1" + self.options.unit)
        hole_r = self.options.diameter / 2 * u
        arm = self.options.cross_size * u
        count = max(self.options.hole_count, 1)
        radius = 0.0
        if count > 1:
            if self.options.distance_mode == "distance_hole_to_center":
                radius = self.options.distance * u
            else:
                # Neighbouring holes are a chord apart: distance = 2 * R * sin(pi / n)
                radius = self.options.distance * u / (2 * math.sin(math.pi / count))

        # Shapes live in viewBox user units, not px, so centre on the viewBox
        vb_x, vb_y, vb_w, vb_h = self.svg.get_viewbox()
        cx = vb_x + vb_w / 2
        cy = vb_y + vb_h / 2

        style = {"stroke": "#000000", "stroke-width": str(0.1 * u), "fill": "none"}
        layer = self.svg.get_current_layer()
        group = layer.add(Group.new("Holes"))
        # Cancel any transform on the layer/parents so coordinates stay page-relative
        group.transform = -layer.composed_transform()

        if self.options.center_hole:
            center_hole = Circle.new(
                center=(cx, cy), radius=self.options.center_hole_diameter / 2 * u
            )
            center_hole.style = style
            self.name(center_hole, "center_hole")
            group.append(center_hole)
            if self.options.crosshair:
                cross = PathElement()
                cross.path = (
                    f"M {cx - arm},{cy} L {cx + arm},{cy} "
                    f"M {cx},{cy - arm} L {cx},{cy + arm}"
                )
                cross.style = style
                self.name(cross, "center_hole_crosshair")
                group.append(cross)

        for i in range(count):
            angle = (
                math.pi / 2
                + math.radians(self.options.rotation)
                + 2 * math.pi * i / count
            )
            # SVG y axis points down, so flip to keep the first hole on top
            x = cx + radius * math.cos(angle)
            y = cy - radius * math.sin(angle)

            circle = Circle.new(center=(x, y), radius=hole_r)
            circle.style = style
            self.name(circle, f"hole_{i + 1}")
            group.append(circle)

            if self.options.crosshair:
                cross = PathElement()
                cross.path = (
                    f"M {x - arm},{y} L {x + arm},{y} "
                    f"M {x},{y - arm} L {x},{y + arm}"
                )
                cross.style = style
                self.name(cross, f"hole_{i + 1}_crosshair")
                group.append(cross)

        if self.options.pitch_circle:
            pitch_circle = Circle.new(
                center=(cx, cy), radius=self.options.pitch_circle_diameter / 2 * u
            )
            pitch_circle.style = style
            self.name(pitch_circle, "pitch_circle")
            group.append(pitch_circle)

        if self.options.to_paths:
            for child in list(group):
                if isinstance(child, Circle):
                    path = child.to_path_element()
                    path.style = style
                    self.name(path, child.get("inkscape:label"))
                    group.replace(child, path)

    @staticmethod
    def name(elem, label):
        """Give an element a descriptive label (shown in Inkscape's XML/Objects panels)."""
        elem.set("inkscape:label", label)


if __name__ == "__main__":
    Mkdrillholes().run()
