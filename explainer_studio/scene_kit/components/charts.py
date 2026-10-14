"""Charts: bars, lines and families of runs, scatter and bubble charts (Rosling), population pyramids, waterfalls,
Sankey flows, parliaments, pies, distributions with shaded areas, and histograms. Every builder returns named parts
so a beat can reveal, highlight or change one piece.

    bubbles = get_scatter({"CHN": (1.2e4, 78, 1.4e9), ...}, is_x_log_scale=True, x_label="income",
                          y_label="life expectancy")
    self.play(*animate_scatter_to(bubbles, point_by_key_map_2020))
    rows = read_csv("shared/assets/data/life_expectancy.csv")   # downloaded with `asset owid download`
"""

from __future__ import annotations

import csv
import itertools
import math

from manimlib import *

from ..context import get_scene_context
from ..parts import KeyedGroup, Parts, choose_tick_step, compute_decimal_place_count
from ..style import SMALL_FONT_SIZE, choose_local_text

__all__ = [
    "CHART_COLORS",
    "CornerAxes",
    "Distribution",
    "animate_bars_to",
    "animate_scatter_to",
    "build_normal_pdf",
    "get_area_under",
    "get_bar_chart",
    "get_distribution",
    "get_histogram",
    "get_line_chart",
    "get_parliament",
    "get_pie",
    "get_population_pyramid",
    "get_run_family",
    "get_sankey",
    "get_scatter",
    "get_waterfall",
    "highlight_run",
    "read_csv",
]


def get_bar_chart(values: list[float], labels: list[str] | None = None, colors: list | None = None,
                  max_value: float | None = None, width: float = 8.0, height: float = 4.0,
                  bar_width_fraction: float = 0.65, should_show_values: bool = True, decimal_place_count: int = 0,
                  font_size: float = SMALL_FONT_SIZE + 2, y_label: str = "") -> VGroup:
    """Vertical bar chart with a baseline, category labels and value labels.
    Parts: .bars[i], .value_labels[i], .labels[i], .baseline, .y_label. Animate changes with
    animate_bars_to(chart, new_values)."""
    bar_count = len(values)
    top_value = max_value or max(max(values), 1e-9) * 1.1
    slot_width = width / bar_count
    baseline = Line(ORIGIN, width * RIGHT).set_stroke(GREY_B, 2)
    bars, value_labels, category_labels = VGroup(), VGroup(), VGroup()
    bar_colors = colors or [BLUE_C] * bar_count
    for i, value in enumerate(values):
        bar_height = max(value / top_value * height, 1e-3)
        bar = Rectangle(width=slot_width * bar_width_fraction, height=bar_height).set_stroke(width=0)
        bar.set_fill(bar_colors[i % len(bar_colors)], 1)
        bar.move_to([slot_width * (i + 0.5), bar_height / 2, 0])
        bars.add(bar)
        if should_show_values:
            value_label = DecimalNumber(value, num_decimal_places=decimal_place_count, font_size=font_size)
            value_labels.add(value_label.next_to(bar, UP, 0.1))
        if labels:
            category_label = Text(str(labels[i]), font_size=font_size).set_color(GREY_A)
            category_labels.add(category_label.next_to([slot_width * (i + 0.5), 0, 0], DOWN, 0.2))
    y_label_mobject = (Text(y_label, font_size=font_size).set_color(GREY_B)
                       .next_to(baseline, UP, height + 0.2, aligned_edge=LEFT) if y_label else VGroup())
    chart = Parts(baseline, bars, value_labels, category_labels, y_label_mobject)
    chart.center()
    chart.bars, chart.value_labels, chart.labels = bars, value_labels, category_labels
    chart.baseline, chart.y_label = baseline, y_label_mobject
    chart.unit_height = height / top_value
    return chart


def animate_bars_to(chart: VGroup, new_values: list[float]) -> list[Animation]:
    """Animations that grow or shrink the bars to new_values; the value labels count along and ride on the bars."""
    animations = []
    base_y = chart.baseline.get_center()[1]
    for i, (bar, value) in enumerate(zip(chart.bars, new_values, strict=False)):
        bar_height = max(value * chart.unit_height, 1e-3)
        target = bar.copy().stretch_to_fit_height(bar_height).move_to([bar.get_center()[0], base_y + bar_height / 2, 0])
        animations.append(Transform(bar, target))
        if len(chart.value_labels) > i:
            label, start_value = chart.value_labels[i], chart.value_labels[i].get_value()

            def update_value_label(mobject, alpha, bar=bar, start_value=start_value, value=value):
                mobject.set_value(interpolate(start_value, value, alpha)).next_to(bar, UP, 0.1)

            animations.append(UpdateFromAlphaFunc(label, update_value_label))
    return animations


def get_line_chart(x_values: list[float], y_values_by_name_map: dict[str, list[float]],
                   color_by_name_map: dict | None = None, width: float = 9.0, height: float = 4.5,
                   x_label: str = "", y_label: str = "", y_range: tuple | None = None,
                   font_size: float = SMALL_FONT_SIZE + 2) -> VGroup:
    """Axes with one polyline per series and end labels. Parts: .axes, .graphs[name], .end_labels[name], .x_label,
    .y_label."""
    xs = list(x_values)
    all_y_values = [y for ys in y_values_by_name_map.values() for y in ys]
    y_min, y_max = (y_range[0], y_range[1]) if y_range else (min(0, min(all_y_values)), max(all_y_values) * 1.1)
    axes = _get_corner_axes((xs[0], xs[-1]), (y_min, y_max), width, height, font_size=font_size)
    graph_by_name_map, end_label_by_name_map = {}, {}
    default_colors = [BLUE_C, TEAL, YELLOW, RED_C, GOLD_C, PURPLE_C]
    group = Parts(axes)
    for index, (name, ys) in enumerate(y_values_by_name_map.items()):
        color = (color_by_name_map or {}).get(name, default_colors[index % len(default_colors)])
        graph = VMobject().set_points_as_corners([axes.c2p(x, y) for x, y in zip(xs, ys)]).set_stroke(color, 3)
        end_label = Text(name, font_size=font_size).set_color(color).next_to(graph.get_end(), RIGHT, 0.15)
        graph_by_name_map[name], end_label_by_name_map[name] = graph, end_label
        group.add(graph, end_label)
    # end labels of series that finish close together would overlap: spread them apart vertically
    end_labels = sorted(end_label_by_name_map.values(), key=lambda label: label.get_center()[1])
    for lower_label, upper_label in itertools.pairwise(end_labels):
        min_label_spacing = (lower_label.get_height() + upper_label.get_height()) / 2 + 0.14
        if upper_label.get_center()[1] - lower_label.get_center()[1] < min_label_spacing:
            upper_label.shift((min_label_spacing - (upper_label.get_center()[1] - lower_label.get_center()[1])) * UP)
    group.x_label = Text(x_label, font_size=font_size).set_color(GREY_B).next_to(axes.x_axis, DOWN, 0.5) if x_label else VGroup()
    group.y_label = Text(y_label, font_size=font_size).set_color(GREY_B).next_to(axes.y_axis, UP, 0.2) if y_label else VGroup()
    group.add(group.x_label, group.y_label)
    group.axes, group.graphs, group.end_labels = axes, KeyedGroup(graph_by_name_map), KeyedGroup(end_label_by_name_map)
    return group


def get_run_family(runs, x_values: list[float] | None = None, width: float = 6.0, height: float = 3.6, color=BLUE_C,
                   y_range: tuple | None = None, x_label: str = "", y_label: str = "",
                   font_size: float = SMALL_FONT_SIZE) -> VGroup:
    """Many runs of one toy on one pair of axes, each a thin translucent line, so the family's shape shows (time
    spread into space). runs: a list of y-sequences, or a dict label -> y-sequence; x_values defaults to 0..n-1.
    Light one run with highlight_run(family, run_key) (its index, or its label) and bring them all back with
    highlight_run(family, None). Parts: .axes, .lines[i] (or .lines[label]), .x_label, .y_label."""
    run_by_key_map = runs if isinstance(runs, dict) else {i: ys for i, ys in enumerate(runs)}
    y_sequences = [list(ys) for ys in run_by_key_map.values()]
    xs = list(x_values) if x_values is not None else list(range(max(len(sequence) for sequence in y_sequences)))
    all_y = [y for sequence in y_sequences for y in sequence]
    y_min, y_max = (y_range[0], y_range[1]) if y_range else (min(0, min(all_y)), max(all_y) * 1.1 or 1.0)
    axes = _get_corner_axes((xs[0], xs[-1]), (y_min, y_max), width, height, font_size=font_size + 2)
    line_by_key_map = {}
    for key, ys in run_by_key_map.items():
        line_by_key_map[key] = VMobject().set_points_as_corners([axes.c2p(x, y) for x, y in zip(xs, ys)]).set_stroke(
            color, 1.5, opacity=0.35)
    family = Parts(axes, *line_by_key_map.values())
    family.x_label = Text(x_label, font_size=font_size).set_color(GREY_B).next_to(axes.x_axis, DOWN, 0.45) if x_label else VGroup()
    family.y_label = Text(y_label, font_size=font_size).set_color(GREY_B).next_to(axes.y_axis, UP, 0.2) if y_label else VGroup()
    family.add(family.x_label, family.y_label)
    family.axes, family.lines, family.color = axes, KeyedGroup(line_by_key_map), color
    return family


def highlight_run(family: VGroup, run_key, color=YELLOW, others_opacity: float = 0.12) -> list[Animation]:
    """Animations that light one run of a get_run_family (thick, coloured, in front) and fade the rest;
    run_key=None puts every run back to the family look."""
    animations = []
    for key, line in family.lines.items():
        if run_key is None:
            animations.append(line.animate.set_stroke(family.color, 1.5, opacity=0.35))
        elif key == run_key:
            line.set_z_index(1)
            animations.append(line.animate.set_stroke(color, 4, opacity=1))
        else:
            line.set_z_index(0)
            animations.append(line.animate.set_stroke(family.color, 1.5, opacity=others_opacity))
    return animations



CHART_COLORS = [BLUE_C, GOLD_C, TEAL, RED_C, PURPLE_C, GREEN_C, MAROON_C, GREY_B]


def read_csv(path: str) -> list[dict]:
    """Rows of a CSV (relative to production/, e.g. one `asset owid download` saved) as dicts; numbers stay strings.
    Scenes never touch the network: download data with the asset commands first."""
    with get_scene_context().resolve_path(path).open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class CornerAxes(Axes):
    """Axes whose c2p reads the two axes wherever they sit (see _get_corner_axes), so it keeps working after the chart
    moves."""
    _is_corner_crossing = False

    def c2p(self, *coords):
        if not self._is_corner_crossing:
            return super().c2p(*coords)
        x, y = coords[:2]
        return np.array([self.x_axis.n2p(x)[0], self.y_axis.n2p(y)[1], 0.0])


def _get_corner_axes(x_range, y_range, width, height, is_x_log_scale=False, font_size=SMALL_FONT_SIZE):
    """Axes that cross at the bottom-left of the data range (ManimGL's Axes always cross at 0, which throws a
    40–90 range far off screen). axes.c2p(x, y) is replaced accordingly and keeps working after the chart moves."""
    axes_kwargs = {"width": width, "height": height, "axis_config": {"stroke_color": GREY_B, "stroke_width": 2}}
    x0, x1 = x_range
    y0, y1 = y_range
    if is_x_log_scale:
        log_x_min, log_x_max = math.floor(math.log10(x0)), math.ceil(math.log10(x1))
        axes = CornerAxes((log_x_min, log_x_max, 1), (y0, y1, choose_tick_step(y1 - y0)), **axes_kwargs)
        convert_x = lambda x: math.log10(max(x, 1e-12))
        x_origin = log_x_min
    else:
        axes = CornerAxes((x0, x1, choose_tick_step(x1 - x0)), (y0, y1, choose_tick_step(y1 - y0)), **axes_kwargs)
        convert_x = lambda x: x
        x_origin = x0
    axes.y_axis.shift((axes.x_axis.n2p(x_origin)[0] - axes.y_axis.n2p(y0)[0]) * RIGHT)
    axes.x_axis.shift((axes.y_axis.n2p(y0)[1] - axes.x_axis.n2p(x_origin)[1]) * UP)
    axes._is_corner_crossing = True
    axes.center()
    if is_x_log_scale:
        for exponent in range(log_x_min, log_x_max + 1):
            axes.add(Text(f"{10 ** exponent:,}", font_size=font_size - 4).set_color(GREY_B)
                     .next_to(axes.c2p(exponent, y0), DOWN, 0.15))
    y_decimal_place_count = compute_decimal_place_count(choose_tick_step(y1 - y0))
    if not is_x_log_scale:
        x_decimal_place_count = compute_decimal_place_count(choose_tick_step(x1 - x0))
        axes.x_axis.add_numbers(font_size=font_size - 4, num_decimal_places=x_decimal_place_count)
    axes.y_axis.add_numbers(font_size=font_size - 4, num_decimal_places=y_decimal_place_count)
    axes._convert_x = convert_x
    return axes


# ---------------------------------------------------------------------------
# Scatter / bubble chart (Rosling)
# ---------------------------------------------------------------------------
def get_scatter(point_by_key_map: dict, x_range=None, y_range=None, is_x_log_scale: bool = False,
                color_by_key_map: dict | None = None, size_range: tuple[float, float] = (0.06, 0.5),
                width: float = 10.0, height: float = 5.2, x_label: str = "", y_label: str = "",
                label_keys: list | None = None, font_size: float = SMALL_FONT_SIZE) -> VGroup:
    """point_by_key_map: {key: (x, y)} or {key: (x, y, size)}; bubble area follows size. Parts: .axes, .dots[key],
    .labels[key] (only for label_keys), .x_label, .y_label. Move to new values with
    animate_scatter_to(chart, new_point_by_key_map)."""
    xs = [point[0] for point in point_by_key_map.values()]
    ys = [point[1] for point in point_by_key_map.values()]
    if x_range is None:
        x_range = (min(xs) * 0.7, max(xs) * 1.4) if is_x_log_scale else (min(0, min(xs)), max(xs) * 1.1)
    if y_range is None:
        y_range = (min(0, min(ys)), max(ys) * 1.1)
    axes = _get_corner_axes(x_range, y_range, width, height, is_x_log_scale, font_size)
    sizes = [point[2] for point in point_by_key_map.values() if len(point) > 2]
    max_size = max(sizes) if sizes else 1
    chart = Parts(axes)
    chart.axes, chart._max_size, chart._size_range = axes, max_size, size_range
    dot_by_key_map, label_by_key_map = {}, {}
    for i, (key, point) in enumerate(point_by_key_map.items()):
        color = (color_by_key_map or {}).get(key, CHART_COLORS[i % len(CHART_COLORS)])
        dot = Dot(radius=_compute_bubble_radius(chart, point), fill_color=color, fill_opacity=0.75)
        dot.set_stroke(WHITE, 0.5)
        dot.move_to(_convert_data_point_to_frame_point(axes, point))
        dot_by_key_map[key] = dot
        if label_keys and key in label_keys:
            label_by_key_map[key] = Text(str(key), font_size=font_size).set_color(color).next_to(dot, UR, 0.05)
    chart.dots, chart.labels = KeyedGroup(dot_by_key_map), KeyedGroup(label_by_key_map)
    chart.add(chart.dots, chart.labels)
    chart.x_label = Text(x_label, font_size=font_size).set_color(GREY_B).next_to(axes.x_axis, DOWN, 0.55) if x_label else VGroup()
    chart.y_label = Text(y_label, font_size=font_size).set_color(GREY_B).next_to(axes.y_axis, UP, 0.2) if y_label else VGroup()
    chart.add(chart.x_label, chart.y_label)
    return chart


def _convert_data_point_to_frame_point(axes, point):
    return axes.c2p(axes._convert_x(point[0]), point[1])


def _compute_bubble_radius(chart, point):
    min_radius, max_radius = chart._size_range
    if len(point) < 3:
        return (min_radius + max_radius) / 4
    return min_radius + (max_radius - min_radius) * math.sqrt(max(point[2], 0) / chart._max_size)


def animate_scatter_to(chart: VGroup, point_by_key_map: dict) -> list[Animation]:
    """Animations moving (and resizing) each bubble to its new value; labels follow."""
    animations = []
    for key, point in point_by_key_map.items():
        if key not in chart.dots:
            continue
        dot = chart.dots[key]
        target = dot.copy().set_width(2 * _compute_bubble_radius(chart, point))
        target.move_to(_convert_data_point_to_frame_point(chart.axes, point))
        animations.append(Transform(dot, target))
        if key in chart.labels:
            animations.append(chart.labels[key].animate.next_to(target, UR, 0.05))
    return animations


# ---------------------------------------------------------------------------
# Population pyramid
# ---------------------------------------------------------------------------
def get_population_pyramid(groups: list[str], left_values: list[float], right_values: list[float],
                           left_label: str | None = None, right_label: str | None = None, left_color=BLUE_C,
                           right_color=RED_C, width: float = 9.0, height: float = 5.5,
                           font_size: float = SMALL_FONT_SIZE) -> VGroup:
    """Age groups bottom-up; bars grow left and right from a centre spine. Parts: .left_bars[i], .right_bars[i],
    .group_labels[i], .left_label, .right_label."""
    left_label = left_label or choose_local_text("男", "Male")
    right_label = right_label or choose_local_text("女", "Female")
    group_count = len(groups)
    top_value = max(max(left_values), max(right_values)) or 1
    row_height = height / group_count
    half_width = (width - 1.4) / 2
    left_bars, right_bars, group_labels = VGroup(), VGroup(), VGroup()
    for i, group_name in enumerate(groups):
        y = -height / 2 + row_height * (i + 0.5)
        left_bar = Rectangle(width=max(left_values[i] / top_value * half_width, 1e-3), height=row_height * 0.82).set_stroke(width=0).set_fill(left_color, 1)
        right_bar = Rectangle(width=max(right_values[i] / top_value * half_width, 1e-3), height=row_height * 0.82).set_stroke(width=0).set_fill(right_color, 1)
        left_bar.move_to([-0.7, y, 0], aligned_edge=RIGHT)
        right_bar.move_to([0.7, y, 0], aligned_edge=LEFT)
        left_bars.add(left_bar)
        right_bars.add(right_bar)
        group_labels.add(Text(group_name, font_size=font_size - 2).set_color(GREY_A).move_to([0, y, 0]))
    left_label_text = Text(left_label, font_size=font_size).set_color(left_color)
    left_label_text.move_to([-half_width / 2 - 0.7, height / 2 + 0.35, 0])
    right_label_text = Text(right_label, font_size=font_size).set_color(right_color)
    right_label_text.move_to([half_width / 2 + 0.7, height / 2 + 0.35, 0])
    chart = Parts(left_bars, right_bars, group_labels, left_label_text, right_label_text)
    chart.left_bars, chart.right_bars, chart.group_labels = left_bars, right_bars, group_labels
    chart.left_label, chart.right_label = left_label_text, right_label_text
    return chart


# ---------------------------------------------------------------------------
# Waterfall (how a total is built up)
# ---------------------------------------------------------------------------
def get_waterfall(steps: list[tuple[str, float]], start_value: float = 0.0, total_label: str | bool = True,
                  up_color=GREEN_C, down_color=RED_C, total_color=BLUE_C, width: float = 10.0, height: float = 4.5,
                  decimal_place_count: int = 0, font_size: float = SMALL_FONT_SIZE) -> VGroup:
    """Each step adds or subtracts from a running total; a final total bar closes it. Parts: .bars[i],
    .value_labels[i], .labels[i], .connectors[i], .baseline."""
    if total_label is True:
        total_label = choose_local_text("合計", "Total")
    running_total, bar_spans = start_value, []
    for _, delta in steps:
        bar_spans.append((running_total, running_total + delta))
        running_total += delta
    if total_label:
        bar_spans.append((0, running_total))
    span_values = [value for span in bar_spans for value in span] + [0]
    min_value, max_value = min(span_values), max(span_values)
    scale = height / ((max_value - min_value) or 1)
    slot_width = width / len(bar_spans)
    convert_value_to_y = lambda value: (value - min_value) * scale
    bars, value_labels, labels, connectors = VGroup(), VGroup(), VGroup(), VGroup()
    bar_names = [step[0] for step in steps] + ([total_label] if total_label else [])
    for i, (span_start, span_end) in enumerate(bar_spans):
        is_total = total_label and i == len(bar_spans) - 1
        color = total_color if is_total else (up_color if span_end >= span_start else down_color)
        bar_height = max(abs(convert_value_to_y(span_end) - convert_value_to_y(span_start)), 1e-3)
        bar = Rectangle(width=slot_width * 0.62, height=bar_height).set_stroke(width=0).set_fill(color, 1)
        bar.move_to([slot_width * (i + 0.5), (convert_value_to_y(span_start) + convert_value_to_y(span_end)) / 2, 0])
        bars.add(bar)
        delta = span_end - span_start
        value_text = f"{delta:+,.{decimal_place_count}f}" if not is_total else f"{span_end:,.{decimal_place_count}f}"
        value_label = Text(value_text, font_size=font_size).set_color(color)
        value_labels.add(value_label.next_to(bar, UP if span_end >= span_start else DOWN, 0.1))
        label = Text(bar_names[i], font_size=font_size).set_color(GREY_A)
        labels.add(label.move_to([slot_width * (i + 0.5), convert_value_to_y(min_value) - 0.35, 0]))
        if i < len(bar_spans) - 1:
            next_start = bar_spans[i + 1][0] if not (total_label and i == len(bar_spans) - 2) else span_end
            connector_start = [slot_width * (i + 0.5) + slot_width * 0.31, convert_value_to_y(span_end), 0]
            connector_end = [slot_width * (i + 1.5) - slot_width * 0.31, convert_value_to_y(next_start), 0]
            connectors.add(DashedLine(connector_start, connector_end, dash_length=0.06).set_stroke(GREY_C, 1.5))
    baseline = Line([0, convert_value_to_y(0), 0], [width, convert_value_to_y(0), 0]).set_stroke(GREY_B, 1.5)
    chart = Parts(baseline, connectors, bars, value_labels, labels).center()
    chart.bars, chart.value_labels, chart.labels = bars, value_labels, labels
    chart.connectors, chart.baseline = connectors, baseline
    return chart


# ---------------------------------------------------------------------------
# Sankey (flows between stages: energy, money, people)
# ---------------------------------------------------------------------------
def get_sankey(flows: list[tuple[str, str, float]], color_by_name_map: dict | None = None, width: float = 11.0,
               height: float = 5.6, node_width: float = 0.22, node_spacing: float = 0.25,
               font_size: float = SMALL_FONT_SIZE, opacity: float = 0.45) -> VGroup:
    """Nodes in columns by depth, bands whose thickness is the flow. Parts: .nodes[name], .bands[(src, dst)],
    .labels[name]. Reveal band by band, or dim all but one path."""
    node_names = []
    for source, target, _ in flows:
        for node_name in (source, target):
            if node_name not in node_names:
                node_names.append(node_name)
    depth_by_node_map = {node_name: 0 for node_name in node_names}
    for _ in node_names:   # longest path from a source
        for source, target, _v in flows:
            depth_by_node_map[target] = max(depth_by_node_map[target], depth_by_node_map[source] + 1)
    column_count = max(depth_by_node_map.values()) + 1
    size_by_node_map = {node_name: max(sum(value for source, _, value in flows if source == node_name),
                                       sum(value for _, target, value in flows if target == node_name))
                        for node_name in node_names}
    nodes_by_column_map = {column_index: [node_name for node_name in node_names
                                          if depth_by_node_map[node_name] == column_index]
                           for column_index in range(column_count)}
    scale = min((height - node_spacing * (len(column_nodes) - 1)) / sum(size_by_node_map[node_name]
                                                                       for node_name in column_nodes)
                for column_nodes in nodes_by_column_map.values())
    convert_column_to_x = lambda column_index: (-width / 2 + (width - node_width)
                                                * (column_index / max(column_count - 1, 1)))
    node_by_name_map, label_by_name_map, next_y_by_node_map = {}, {}, {}
    for column_index, column_nodes in nodes_by_column_map.items():
        column_height = (sum(size_by_node_map[node_name] for node_name in column_nodes) * scale
                         + node_spacing * (len(column_nodes) - 1))
        top = column_height / 2
        for node_name in column_nodes:
            node_height = size_by_node_map[node_name] * scale
            default_color = CHART_COLORS[node_names.index(node_name) % len(CHART_COLORS)]
            color = (color_by_name_map or {}).get(node_name, default_color)
            node_rectangle = Rectangle(width=node_width, height=node_height).set_stroke(width=0).set_fill(color, 1)
            node_rectangle.move_to([convert_column_to_x(column_index) + node_width / 2, top - node_height / 2, 0])
            node_by_name_map[node_name] = node_rectangle
            next_y_by_node_map[node_name] = {"out": top, "in": top}
            side = LEFT if column_index == column_count - 1 else RIGHT
            label = Text(node_name, font_size=font_size).set_color(GREY_A)
            is_outer_column = column_index in (0, column_count - 1)
            label_by_name_map[node_name] = label.next_to(node_rectangle, side if is_outer_column else RIGHT, 0.12)
            if column_index == 0:
                label_by_name_map[node_name].next_to(node_rectangle, LEFT, 0.12)
            top -= node_height + node_spacing
    band_by_edge_map = {}
    for source, target, value in flows:
        band_thickness = value * scale
        source_top, target_top = next_y_by_node_map[source]["out"], next_y_by_node_map[target]["in"]
        next_y_by_node_map[source]["out"] -= band_thickness
        next_y_by_node_map[target]["in"] -= band_thickness
        source_x = node_by_name_map[source].get_right()[0]
        target_x = node_by_name_map[target].get_left()[0]
        mid_x = (source_x + target_x) / 2
        band = VMobject()
        band.start_new_path([source_x, source_top, 0])
        band.add_cubic_bezier_curve_to([mid_x, source_top, 0], [mid_x, target_top, 0], [target_x, target_top, 0])
        band.add_line_to([target_x, target_top - band_thickness, 0])
        band.add_cubic_bezier_curve_to([mid_x, target_top - band_thickness, 0], [mid_x, source_top - band_thickness, 0],
                                       [source_x, source_top - band_thickness, 0])
        band.close_path()
        color = (color_by_name_map or {}).get(source, node_by_name_map[source].get_fill_color())
        band.set_fill(color, opacity).set_stroke(width=0)
        band_by_edge_map[(source, target)] = band
    chart = Parts(KeyedGroup(band_by_edge_map), KeyedGroup(node_by_name_map), KeyedGroup(label_by_name_map))
    chart.bands, chart.nodes, chart.labels = chart[0], chart[1], chart[2]
    return chart


# ---------------------------------------------------------------------------
# Parliament (seats in a hemicycle)
# ---------------------------------------------------------------------------
def get_parliament(seat_count_by_party_map: dict[str, int], color_by_party_map: dict | None = None,
                   radius: float = 3.6, row_count: int | None = None, dot_radius: float | None = None,
                   font_size: float = SMALL_FONT_SIZE) -> VGroup:
    """One dot per seat, parties in order from left to right. Parts: .seats[party] (VGroup of dots), .legend[party],
    .majority (a dashed line at half)."""
    total_seat_count = sum(seat_count_by_party_map.values())
    row_count = row_count or max(3, round(math.sqrt(total_seat_count / 4)))
    radii = [radius * (0.45 + 0.55 * row_index / max(row_count - 1, 1)) for row_index in range(row_count)]
    row_seat_counts = [max(1, round(total_seat_count * row_radius / sum(radii))) for row_radius in radii]
    row_seat_counts[-1] += total_seat_count - sum(row_seat_counts)
    seat_positions = []
    for row_radius, seat_count in zip(radii, row_seat_counts):
        for seat_index in range(seat_count):
            angle = PI - PI * (seat_index + 0.5) / seat_count
            seat_positions.append((angle, row_radius))
    seat_positions.sort(key=lambda seat_position: (-seat_position[0], seat_position[1]))
    resolved_dot_radius = dot_radius or min(0.12, radius * 0.55 / row_count * 0.42)
    party_dots_by_party_map, legend_by_party_map, i = {}, {}, 0
    for j, (party, seat_count) in enumerate(seat_count_by_party_map.items()):
        color = (color_by_party_map or {}).get(party, CHART_COLORS[j % len(CHART_COLORS)])
        party_dots = VGroup(*[Dot([row_radius * math.cos(angle), row_radius * math.sin(angle), 0],
                                  radius=resolved_dot_radius, fill_color=color)
                              for angle, row_radius in seat_positions[i:i + seat_count]])
        party_dots_by_party_map[party] = party_dots
        i += seat_count
        swatch = Square(0.22).set_fill(color, 1).set_stroke(width=0)
        legend_text = Text(f"{party}  {seat_count}", font_size=font_size).set_color(GREY_A)
        legend_by_party_map[party] = VGroup(swatch, legend_text.next_to(swatch, RIGHT, 0.12))
    legend_row = VGroup(*legend_by_party_map.values()).arrange(RIGHT, buff=0.45).next_to(ORIGIN, DOWN, 0.5)
    majority_line = DashedLine([0, radius * 0.4, 0], [0, radius * 1.08, 0]).set_stroke(GREY_B, 1.5)
    chart = Parts(KeyedGroup(party_dots_by_party_map), legend_row, majority_line)
    chart.seats, chart.legend, chart.majority = chart[0], KeyedGroup(legend_by_party_map), majority_line
    return chart


# ---------------------------------------------------------------------------
# Pie / donut
# ---------------------------------------------------------------------------
def get_pie(value_by_name_map: dict[str, float], color_by_name_map: dict | None = None, radius: float = 2.2,
            inner_radius: float = 0.0, font_size: float = SMALL_FONT_SIZE, should_show_percent: bool = True) -> VGroup:
    """Slices clockwise from 12 o'clock. inner_radius > 0 makes a donut. Parts: .slices[name], .labels[name]."""
    total = sum(value_by_name_map.values()) or 1
    start_angle = PI / 2
    slice_by_name_map, label_by_name_map = {}, {}
    for j, (name, value) in enumerate(value_by_name_map.items()):
        angle = TAU * value / total
        color = (color_by_name_map or {}).get(name, CHART_COLORS[j % len(CHART_COLORS)])
        slice_sector = AnnularSector(inner_radius=inner_radius, outer_radius=radius, angle=-angle,
                                     start_angle=start_angle)
        slice_sector.set_fill(color, 1).set_stroke(BLACK, 2)
        mid_angle = start_angle - angle / 2
        label_text = f"{name} {value / total:.0%}" if should_show_percent else name
        label = Text(label_text, font_size=font_size).set_color(color)
        label_point = (radius + 0.55) * np.array([math.cos(mid_angle), math.sin(mid_angle), 0])
        label_by_name_map[name] = label.move_to(label_point)
        slice_by_name_map[name] = slice_sector
        start_angle -= angle
    chart = Parts(KeyedGroup(slice_by_name_map), KeyedGroup(label_by_name_map))
    chart.slices, chart.labels = chart[0], chart[1]
    return chart


# ---------------------------------------------------------------------------
# Distributions (statistics)
# ---------------------------------------------------------------------------
def get_distribution(pdf, x_range: tuple[float, float], width: float = 9.0, height: float = 4.0, color=BLUE_C,
                     x_label: str = "", font_size: float = SMALL_FONT_SIZE) -> VGroup:
    """A density curve pdf(x) over x_range. Parts: .axes, .curve; get_area_between(a, b) returns the filled area
    between a and b (a p-value, a confidence interval). For the normal curve: pdf=build_normal_pdf(mu, sigma)."""
    x0, x1 = x_range
    ys = [pdf(x0 + (x1 - x0) * t / 200) for t in range(201)]
    top_value = max(ys) * 1.15
    axes = Axes((x0, x1, choose_tick_step(x1 - x0)), (0, top_value, top_value), width=width, height=height,
                axis_config={"stroke_color": GREY_B, "stroke_width": 2}, y_axis_config={"stroke_opacity": 0})
    axes.x_axis.add_numbers(font_size=font_size - 4)
    curve = axes.get_graph(pdf, x_range=(x0, x1, (x1 - x0) / 200)).set_stroke(color, 3)
    chart = Distribution(axes, curve)
    chart.axes, chart.curve, chart.pdf = axes, curve, pdf
    if x_label:
        chart.add(Text(x_label, font_size=font_size).set_color(GREY_B).next_to(axes.x_axis, DOWN, 0.5))
    return chart


class Distribution(Parts):
    """What get_distribution returns: .axes, .curve, .pdf, .get_area_between(a, b)."""

    def get_area_between(self, a: float, b: float, fill_color=YELLOW, opacity: float = 0.5) -> VMobject:
        """The filled area under the curve between a and b."""
        axes, pdf = self.axes, self.pdf
        points = [axes.c2p(a, 0)] + [axes.c2p(x, pdf(x)) for x in np.linspace(a, b, 80)] + [axes.c2p(b, 0)]
        return Polygon(*points).set_fill(fill_color, opacity).set_stroke(width=0)


def get_area_under(axes, curve: VMobject, fill_color=BLUE_C, opacity: float = 0.4) -> VMobject:
    """The area between a curve drawn on axes and the x axis, rebuilt from the curve every frame: whatever moves,
    stretches or reshapes the curve (Transform, an updater, a ValueTracker), the area follows it. A curve and an area
    transformed separately come apart halfway through the animation (their points do not correspond)."""
    base_y = 0.0 if axes.y_range[0] <= 0 <= axes.y_range[1] else axes.y_range[0]

    def build() -> VMobject:
        points = curve.get_anchors()
        x0, x1 = axes.p2c(points[0])[0], axes.p2c(points[-1])[0]
        area = Polygon(*points, axes.c2p(x1, base_y), axes.c2p(x0, base_y))
        return area.set_fill(fill_color, opacity).set_stroke(width=0)

    area = build()
    area.add_updater(lambda mobject: mobject.become(build()))
    return area


def build_normal_pdf(mu: float = 0.0, sigma: float = 1.0):
    return lambda x: math.exp(-((x - mu) ** 2) / (2 * sigma ** 2)) / (sigma * math.sqrt(2 * math.pi))


def get_histogram(values: list[float], bin_count: int = 12, x_range: tuple | None = None, width: float = 9.0,
                  height: float = 4.0, color=BLUE_C, x_label: str = "", font_size: float = SMALL_FONT_SIZE) -> VGroup:
    """Counts of values in equal bins. Parts: .axes, .bars[i], .bin_edges."""
    x_min, x_max = x_range or (min(values), max(values))
    bin_width = (x_max - x_min) / bin_count or 1
    counts = [0] * bin_count
    for value in values:
        if x_min <= value <= x_max:
            counts[min(bin_count - 1, int((value - x_min) / bin_width))] += 1
    top_count = max(counts) * 1.15 or 1
    axes = _get_corner_axes((x_min, x_max), (0, top_count), width, height, font_size=font_size)
    bars = VGroup()
    for i, count in enumerate(counts):
        bottom_left, top_right = axes.c2p(x_min + i * bin_width, 0), axes.c2p(x_min + (i + 1) * bin_width, count)
        bar = Rectangle(width=top_right[0] - bottom_left[0], height=max(top_right[1] - bottom_left[1], 1e-3))
        bar.set_fill(color, 0.85).set_stroke(BLACK, 1)
        bars.add(bar.move_to((bottom_left + top_right) / 2))
    chart = Parts(axes, bars)
    chart.axes, chart.bars, chart.bin_edges = axes, bars, [x_min + i * bin_width for i in range(bin_count + 1)]
    if x_label:
        chart.add(Text(x_label, font_size=font_size).set_color(GREY_B).next_to(axes.x_axis, DOWN, 0.5))
    return chart


