#!/usr/bin/env python3
"""Inkscape extension: draw circular / rectangular hole patterns with crosshairs."""
import argparse
import math
from typing import Dict, List, Tuple

import inkex
from inkex import Circle, Group, PathElement

Point = Tuple[float, float]


class Mkdrillholes(inkex.EffectExtension):
    def add_arguments(self, pars: argparse.ArgumentParser) -> None:
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
        pars.add_argument("--center_x", type=float, default=0.0)
        pars.add_argument("--center_y", type=float, default=0.0)
        pars.add_argument("--crosshair", type=inkex.Boolean, default=True)
        pars.add_argument("--cross_size", type=float, default=3.0)
        pars.add_argument("--pitch_circle", type=inkex.Boolean, default=False)
        pars.add_argument("--pitch_circle_diameter", type=float, default=50.0)
        pars.add_argument("--center_hole", type=inkex.Boolean, default=False)
        pars.add_argument("--center_hole_diameter", type=float, default=5.0)
        pars.add_argument("--to_paths", type=inkex.Boolean, default=False)
        pars.add_argument("--unit", default="mm")

    def effect(self) -> None:
        self.u: float = self.svg.unittouu("1" + self.options.unit)
        self.style: Dict[str, str] = {
            "stroke": "#000000",
            "stroke-width": str(0.1 * self.u),
            "fill": "none",
        }
        # Shapes live in viewBox user units, not px
        vb_x, vb_y, _, _ = self.svg.get_viewbox()
        # Pattern center in absolute page coordinates (origin top-left, y downwards)
        self.center: Point = (
            vb_x + self.options.center_x * self.u,
            vb_y + self.options.center_y * self.u,
        )

        rectangular = self.options.pattern == "rectangular"
        layer = self.svg.get_current_layer()
        group = layer.add(Group.new("Rectangle" if rectangular else "Circular"))
        # Cancel any transform on the layer/parents so coordinates stay page-relative
        group.transform = -layer.composed_transform()

        if self.options.center_hole:
            self.add_center_hole(group)

        if rectangular:
            self.draw_rectangular(group)
        else:
            self.draw_circular(group)

        if self.options.to_paths:
            self.convert_to_paths(group)

    # ---- patterns -------------------------------------------------------

    def draw_circular(self, group: Group) -> None:
        """Evenly spaced holes on a circle, optionally with a pitch circle."""
        count = max(self.options.hole_count, 1)
        radius = 0.0
        if count > 1:
            if self.options.distance_mode == "distance_hole_to_center":
                radius = self.options.distance * self.u
            else:
                # Neighbouring holes are a chord apart: distance = 2 * R * sin(pi / n)
                radius = self.options.distance * self.u / (2 * math.sin(math.pi / count))

        # First hole on top, then counter-clockwise (offsets are y up)
        offsets: List[Point] = [
            (
                radius * math.cos(math.pi / 2 + 2 * math.pi * i / count),
                radius * math.sin(math.pi / 2 + 2 * math.pi * i / count),
            )
            for i in range(count)
        ]
        self.add_holes(group, offsets)

        if self.options.pitch_circle:
            cx, cy = self.center
            pitch_circle = Circle.new(
                center=(cx, cy), radius=self.options.pitch_circle_diameter / 2 * self.u
            )
            pitch_circle.style = self.style
            self.name(pitch_circle, "pitch_circle")
            group.append(pitch_circle)

    def draw_rectangular(self, group: Group) -> None:
        """Four holes at the corners of a rectangle, optionally with a pitch rectangle."""
        hw = self.options.rect_width * self.u / 2
        hh = self.options.rect_height * self.u / 2
        # Clockwise from top-left (offsets are y up)
        self.add_holes(group, [(-hw, hh), (hw, hh), (hw, -hh), (-hw, -hh)])

        if self.options.pitch_rect:
            pw = self.options.pitch_rect_width * self.u / 2
            ph = self.options.pitch_rect_height * self.u / 2
            pts = [
                self.place(ox, oy)
                for ox, oy in [(-pw, ph), (pw, ph), (pw, -ph), (-pw, -ph)]
            ]
            pitch_rect = PathElement()
            pitch_rect.path = "M " + " L ".join(f"{x},{y}" for x, y in pts) + " Z"
            pitch_rect.style = self.style
            self.name(pitch_rect, "pitch_rectangle")
            group.append(pitch_rect)

    # ---- helpers --------------------------------------------------------

    def place(self, ox: float, oy: float) -> Point:
        """Rotate an offset (y up) counter-clockwise and move it to the pattern center."""
        rot = math.radians(self.options.rotation)
        cx, cy = self.center
        # SVG y axis points down, so flip y
        return (
            cx + ox * math.cos(rot) - oy * math.sin(rot),
            cy - (ox * math.sin(rot) + oy * math.cos(rot)),
        )

    def add_holes(self, group: Group, offsets: List[Point]) -> None:
        hole_r = self.options.diameter / 2 * self.u
        for i, (ox, oy) in enumerate(offsets):
            x, y = self.place(ox, oy)
            circle = Circle.new(center=(x, y), radius=hole_r)
            circle.style = self.style
            self.name(circle, f"hole_{i + 1}")
            group.append(circle)
            if self.options.crosshair:
                self.add_crosshair(group, x, y, f"hole_{i + 1}_crosshair")

    def add_center_hole(self, group: Group) -> None:
        cx, cy = self.center
        center_hole = Circle.new(
            center=(cx, cy), radius=self.options.center_hole_diameter / 2 * self.u
        )
        center_hole.style = self.style
        self.name(center_hole, "center_hole")
        group.append(center_hole)
        if self.options.crosshair:
            self.add_crosshair(group, cx, cy, "center_hole_crosshair")

    def add_crosshair(self, group: Group, x: float, y: float, label: str) -> None:
        arm = self.options.cross_size * self.u
        cross = PathElement()
        cross.path = (
            f"M {x - arm},{y} L {x + arm},{y} "
            f"M {x},{y - arm} L {x},{y + arm}"
        )
        cross.style = self.style
        self.name(cross, label)
        group.append(cross)

    def convert_to_paths(self, group: Group) -> None:
        for child in list(group):
            if isinstance(child, Circle):
                path = child.to_path_element()
                path.style = self.style
                self.name(path, child.get("inkscape:label"))
                group.replace(child, path)

    @staticmethod
    def name(elem: inkex.BaseElement, label: str) -> None:
        """Give an element a descriptive label (shown in Inkscape's XML/Objects panels)."""
        elem.set("inkscape:label", label)


if __name__ == "__main__":
    Mkdrillholes().run()
