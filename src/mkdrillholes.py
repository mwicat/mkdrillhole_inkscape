#!/usr/bin/env python3
"""Inkscape extension: draw evenly spaced holes with crosshairs on a circle."""
import math

import inkex
from inkex import Circle, Group, PathElement


class Mkdrillholes(inkex.EffectExtension):
    def add_arguments(self, pars):
        pars.add_argument("--pattern", default="circular")
        pars.add_argument("--pattern_tabs", default="circular_tab")
        pars.add_argument("--rect_width", type=float, default=40.0)
        pars.add_argument("--rect_height", type=float, default=25.0)
        pars.add_argument("--pitch_rect", type=inkex.Boolean, default=False)
        pars.add_argument("--pitch_rect_width", type=float, default=40.0)
        pars.add_argument("--pitch_rect_height", type=float, default=25.0)
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
        rectangular = self.options.pattern == "rectangular"
        count = 4 if rectangular else max(self.options.hole_count, 1)
        radius = 0.0
        if not rectangular and count > 1:
            if self.options.distance_mode == "distance_hole_to_center":
                radius = self.options.distance * u
            else:
                # Neighbouring holes are a chord apart: distance = 2 * R * sin(pi / n)
                radius = self.options.distance * u / (2 * math.sin(math.pi / count))

        # Hole offsets from the pattern center (y up), before rotation
        if rectangular:
            hw = self.options.rect_width * u / 2
            hh = self.options.rect_height * u / 2
            offsets = [(-hw, hh), (hw, hh), (hw, -hh), (-hw, -hh)]
        else:
            offsets = [
                (
                    radius * math.cos(math.pi / 2 + 2 * math.pi * i / count),
                    radius * math.sin(math.pi / 2 + 2 * math.pi * i / count),
                )
                for i in range(count)
            ]
        rot = math.radians(self.options.rotation)

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

        for i, (ox, oy) in enumerate(offsets):
            # Rotate counter-clockwise; SVG y axis points down, so flip y
            x = cx + ox * math.cos(rot) - oy * math.sin(rot)
            y = cy - (ox * math.sin(rot) + oy * math.cos(rot))

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

        if self.options.pitch_circle and not rectangular:
            pitch_circle = Circle.new(
                center=(cx, cy), radius=self.options.pitch_circle_diameter / 2 * u
            )
            pitch_circle.style = style
            self.name(pitch_circle, "pitch_circle")
            group.append(pitch_circle)

        if self.options.pitch_rect and rectangular:
            pw = self.options.pitch_rect_width * u / 2
            ph = self.options.pitch_rect_height * u / 2
            pts = []
            for ox, oy in [(-pw, ph), (pw, ph), (pw, -ph), (-pw, -ph)]:
                # Same rotation as the holes
                pts.append(
                    (
                        cx + ox * math.cos(rot) - oy * math.sin(rot),
                        cy - (ox * math.sin(rot) + oy * math.cos(rot)),
                    )
                )
            pitch_rect = PathElement()
            pitch_rect.path = "M " + " L ".join(f"{px},{py}" for px, py in pts) + " Z"
            pitch_rect.style = style
            self.name(pitch_rect, "pitch_rectangle")
            group.append(pitch_rect)

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
