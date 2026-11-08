#!/usr/bin/env python3
"""Inkscape extension: draw evenly spaced holes with crosshairs on a circle."""
import math

import inkex
from inkex import Circle, Group, PathElement


class Mkdrillholes(inkex.EffectExtension):
    def add_arguments(self, pars):
        pars.add_argument("--hole_count", type=int, default=3)
        pars.add_argument("--distance", type=float, default=25.0)
        pars.add_argument("--diameter", type=float, default=5.0)
        pars.add_argument("--cross_size", type=float, default=3.0)
        pars.add_argument("--unit", default="mm")

    def effect(self):
        u = self.svg.unittouu("1" + self.options.unit)
        hole_r = self.options.diameter / 2 * u
        arm = self.options.cross_size * u
        count = max(self.options.hole_count, 1)
        # Neighbouring holes are a chord apart: distance = 2 * R * sin(pi / n)
        radius = 0.0
        if count > 1:
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

        for i in range(count):
            angle = math.pi / 2 + 2 * math.pi * i / count
            # SVG y axis points down, so flip to keep the first hole on top
            x = cx + radius * math.cos(angle)
            y = cy - radius * math.sin(angle)

            circle = Circle.new(center=(x, y), radius=hole_r)
            circle.style = style
            group.append(circle)

            cross = PathElement()
            cross.path = (
                f"M {x - arm},{y} L {x + arm},{y} "
                f"M {x},{y - arm} L {x},{y + arm}"
            )
            cross.style = style
            group.append(cross)


if __name__ == "__main__":
    Mkdrillholes().run()
