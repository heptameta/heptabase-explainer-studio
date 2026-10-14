"""Circuit diagrams: standard symbols drawn between two points on a grid, with current that can flow along the
wires (flow_along).

    circuit = get_circuit([("battery", (0, 0), (0, 2), "9 V"), ("wire", (0, 2), (4, 2)),
                           ("resistor", (4, 2), (4, 0), "R1"), ("lamp", (4, 0), (0, 0), "lamp")], unit_size=1.4)
    current_path = circuit.get_current_path([(0, 0), (0, 2), (4, 2), (4, 0), (0, 0)])
    self.play(flow_along(get_flow_token(YELLOW), [current_path]))
"""

from __future__ import annotations

import math

from manimlib import *

from ..parts import KeyedGroup, Parts
from ..style import SMALL_FONT_SIZE

__all__ = ["COMPONENT_KINDS", "Circuit", "get_circuit", "get_component"]

COMPONENT_KINDS = ("wire", "resistor", "capacitor", "inductor", "battery", "source", "ac_source", "lamp",
                   "switch_open", "switch_closed", "diode", "led", "ground", "ammeter", "voltmeter")


def _get_symbol(kind: str, length: float, stroke_width: float, color) -> VGroup:
    """The symbol along +x from 0 to length, centred on y = 0; leads fill the rest."""
    body_length = 0.9 if kind not in ("wire", "ground") else 0.0
    body_start, body_end = (length - body_length) / 2, (length + body_length) / 2
    if body_length:
        lead = VGroup(Line(ORIGIN, body_start * RIGHT), Line(body_end * RIGHT, length * RIGHT))
    else:
        lead = VGroup(Line(ORIGIN, length * RIGHT))
    body = VGroup()
    if kind == "resistor":
        zigzag_count = 6
        points = ([body_start * RIGHT]
                  + [[body_start + body_length * (k + 0.5) / zigzag_count, 0.16 * (1 if k % 2 == 0 else -1), 0]
                     for k in range(zigzag_count)]
                  + [body_end * RIGHT])
        body.add(VMobject().set_points_as_corners([np.array(point, dtype=float) for point in points]))
    elif kind == "capacitor":
        middle = length / 2
        lead = VGroup(Line(ORIGIN, (middle - 0.09) * RIGHT), Line((middle + 0.09) * RIGHT, length * RIGHT))
        body.add(Line([middle - 0.09, -0.3, 0], [middle - 0.09, 0.3, 0]),
                 Line([middle + 0.09, -0.3, 0], [middle + 0.09, 0.3, 0]))
    elif kind == "inductor":
        for k in range(4):
            body.add(Arc(start_angle=PI, angle=-PI, radius=body_length / 8)
                     .move_to([body_start + body_length * (2 * k + 1) / 8, 0.06, 0]))
    elif kind == "battery":
        middle = length / 2
        lead = VGroup(Line(ORIGIN, (middle - 0.08) * RIGHT), Line((middle + 0.08) * RIGHT, length * RIGHT))
        body.add(Line([middle - 0.08, -0.34, 0], [middle - 0.08, 0.34, 0]),
                 Line([middle + 0.08, -0.17, 0], [middle + 0.08, 0.17, 0]).set_stroke(width=stroke_width * 2))
        body.add(Text("+", font_size=22).move_to([middle - 0.26, 0.34, 0]))
    elif kind in ("source", "ac_source", "lamp", "ammeter", "voltmeter"):
        circle = Circle(radius=body_length / 2).move_to(length / 2 * RIGHT)
        body.add(circle)
        if kind == "ac_source":
            body.add(FunctionGraph(lambda x: 0.12 * math.sin(x * TAU / 0.5), x_range=(-0.25, 0.25, 0.01))
                     .move_to(circle))
        elif kind == "source":
            body.add(Text("+", font_size=22).move_to(circle.get_center() + 0.2 * LEFT),
                     Text("−", font_size=22).move_to(circle.get_center() + 0.2 * RIGHT))
        elif kind == "lamp":
            radius = body_length / 2 * 0.7
            center = circle.get_center()
            body.add(Line(center + radius * (UL / math.sqrt(2) * 1.0), center + radius * (DR / math.sqrt(2))),
                     Line(center + radius * (UR / math.sqrt(2)), center + radius * (DL / math.sqrt(2))))
        else:
            body.add(Text("A" if kind == "ammeter" else "V", font_size=26).move_to(circle))
    elif kind in ("switch_open", "switch_closed"):
        body.add(Dot(body_start * RIGHT, radius=0.05), Dot(body_end * RIGHT, radius=0.05))
        end = body_end * RIGHT if kind == "switch_closed" else [body_end - 0.1, 0.38, 0]
        body.add(Line(body_start * RIGHT, np.array(end, dtype=float)))
    elif kind in ("diode", "led"):
        triangle = Polygon([body_start, 0.25, 0], [body_start, -0.25, 0], [body_end - 0.1, 0, 0]).set_fill(color, 1)
        body.add(triangle, Line([body_end - 0.1, 0.25, 0], [body_end - 0.1, -0.25, 0]))
        if kind == "led":
            for dy in (0.0, 0.18):
                body.add(Arrow([body_start + 0.3, 0.3 + dy, 0], [body_start + 0.6, 0.55 + dy, 0], buff=0,
                               thickness=0.02, fill_color=color))
    elif kind == "ground":
        lead = VGroup(Line(ORIGIN, (length - 0.05) * RIGHT))
        for k, plate_width in enumerate((0.5, 0.32, 0.14)):
            body.add(Line([length + 0.1 * k, -plate_width / 2, 0], [length + 0.1 * k, plate_width / 2, 0]))
    symbol = VGroup(lead, body)
    symbol.set_stroke(color, stroke_width)
    symbol.lead, symbol.body = lead, body
    return symbol


def get_component(kind: str, start, end, label: str = "", color=WHITE, stroke_width: float = 4,
                  font_size: float = SMALL_FONT_SIZE + 2, label_side: float = 1) -> VGroup:
    """One symbol from start to end (frame points). Parts: .lead (the wires), .body (the symbol), .label."""
    if kind not in COMPONENT_KINDS:
        raise ValueError(f"kind must be one of {COMPONENT_KINDS}")
    start_point, end_point = np.array(start, dtype=float), np.array(end, dtype=float)
    direction = end_point - start_point
    length = float(np.linalg.norm(direction))
    symbol = _get_symbol(kind, length, stroke_width, color)
    angle = math.atan2(direction[1], direction[0])
    symbol.rotate(angle, about_point=ORIGIN).shift(start_point)
    label_mobject = VGroup()
    if label:
        normal = np.array([-math.sin(angle), math.cos(angle), 0])
        if normal[1] < -1e-6 or (abs(normal[1]) < 1e-6 and normal[0] > 0):
            normal = -normal   # labels go above horizontal parts and left of vertical ones
        label_offset = 0.8 if kind in ("source", "ac_source", "lamp", "ammeter", "voltmeter") else 0.55
        label_mobject = (Text(label, font_size=font_size).set_color(color)
                         .move_to((start_point + end_point) / 2 + normal * label_offset * label_side))
    component = Parts(symbol, label_mobject)
    component.lead, component.body, component.label, component.kind = symbol.lead, symbol.body, label_mobject, kind
    return component


class Circuit(Parts):
    """Parts: circuit[label] (a component; unlabelled ones are keyed "kind#i"), .components, .wires (every lead and
    wire), .nodes (dots where three or more ends meet), .get_grid_point(x, y) (grid → frame),
    .get_current_path(points) (a path for flow_along)."""

    def __init__(self, component_specs: list[tuple], unit_size: float = 1.2, color=WHITE, stroke_width: float = 4):
        super().__init__()
        xs = [coordinate for spec in component_specs for coordinate in (spec[1][0], spec[2][0])]
        ys = [coordinate for spec in component_specs for coordinate in (spec[1][1], spec[2][1])]
        self._origin = np.array([-(min(xs) + max(xs)) / 2 * unit_size, -(min(ys) + max(ys)) / 2 * unit_size, 0])
        self._unit_size = unit_size
        component_by_key_map, end_count_by_point_map = {}, {}
        for index, (kind, start, end, *rest) in enumerate(component_specs):
            label = rest[0] if rest else ""
            component = get_component(kind, self.get_grid_point(*start), self.get_grid_point(*end), label, color,
                                      stroke_width)
            if label:   # labels go on the outside of the loop, away from the circuit's middle
                mid = (self.get_grid_point(*start) + self.get_grid_point(*end)) / 2
                center = self._origin * 0
                if np.linalg.norm(component.label.get_center() - center) < np.linalg.norm(mid - center):
                    component.label.move_to(2 * mid - component.label.get_center())
            key = label or f"{kind}#{index}"
            component_by_key_map[key] = component
            for end_point in (tuple(start), tuple(end)):
                end_count_by_point_map[end_point] = end_count_by_point_map.get(end_point, 0) + 1
        self.components = KeyedGroup(component_by_key_map)
        self.wires = VGroup(*[component.lead for component in component_by_key_map.values()])
        self.nodes = VGroup(*[Dot(self.get_grid_point(*end_point), radius=0.07, fill_color=color)
                              for end_point, end_count in end_count_by_point_map.items() if end_count >= 3])
        self.add(self.components, self.nodes)
        # get_center is a live view: copy it
        self._built_center_and_width = (np.array(self.get_center(), dtype=float), self.get_width())

    def __getitem__(self, key):
        if isinstance(key, (int, slice)):
            return super().__getitem__(key)
        return self.components[key]

    def get_grid_point(self, x: float, y: float) -> np.ndarray:
        """Grid point → frame point, following the circuit if it was moved or scaled after it was built."""
        unscaled_point = self._origin + np.array([x * self._unit_size, y * self._unit_size, 0])
        if not hasattr(self, "_built_center_and_width"):
            return unscaled_point
        built_center, built_width = self._built_center_and_width
        scale = self.get_width() / built_width if built_width else 1.0
        return self.get_center() + (unscaled_point - built_center) * scale

    def get_current_path(self, points: list[tuple[float, float]]) -> VMobject:
        """A polyline through grid points (in the direction current flows) for flow_along."""
        return VMobject().set_points_as_corners([self.get_grid_point(*grid_point) for grid_point in points])


def get_circuit(component_specs: list[tuple], **kwargs) -> Circuit:
    """component_specs: (kind, (x0, y0), (x1, y1), "label") on a grid; kinds: """ + ", ".join(COMPONENT_KINDS) + """."""
    return Circuit(component_specs, **kwargs)
