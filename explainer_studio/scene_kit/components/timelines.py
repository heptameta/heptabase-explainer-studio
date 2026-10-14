"""Time: a year line with event markers, and the timeline chart with lanes for periods, lives and events."""

from __future__ import annotations

import math

from manimlib import *

from ..parts import KeyedGroup, Parts, choose_tick_step
from ..style import HIGHLIGHT_COLOR, SMALL_FONT_SIZE, YEAR_COLOR
from .charts import CHART_COLORS

__all__ = ["TimelineChart", "get_event_marker", "get_timeline", "get_timeline_chart"]


def get_timeline(start_year: int, end_year: int, step_years: int = 10, width: float = 12) -> NumberLine:
    line = NumberLine((start_year, end_year, step_years), width=width, tick_size=0.05, include_tip=False)
    line.set_stroke(GREY_B, 2)
    line.add_numbers(font_size=SMALL_FONT_SIZE, num_decimal_places=0, group_with_commas=False)
    line.numbers.set_color(YEAR_COLOR)
    return line


def get_event_marker(timeline: NumberLine, year: float, label: str, direction=UP, color=HIGHLIGHT_COLOR) -> VGroup:
    dot = Dot(timeline.n2p(year), radius=0.06).set_color(color)
    text = Text(label, font_size=SMALL_FONT_SIZE).set_color(color)
    # Below the line, clear the year numbers
    text.next_to(dot, direction, SMALL_BUFF if direction[1] > 0 else 0.5)
    return VGroup(dot, text)



def _assign_event_lanes(events: list, compute_label_span, convert_year_to_x) -> list[int]:
    """A lane for each event label below the axis such that labels in a lane do not overlap and no event's stem (a
    vertical line from the axis down to its label) runs through another event's label in a shallower lane. Labels
    run rightwards from their stem, so events are placed right to left: an event whose label covers a stem further
    right goes below that stem's label. Lanes are capped; past the cap the deepest lane is used."""
    placement_by_event_index_map = {}   # index -> (lane, (label_start, label_end), stem_x)
    max_lane = len(events) + 1
    for i in sorted(range(len(events)), key=lambda event_index: -convert_year_to_x(events[event_index][0])):
        label_start, label_end = compute_label_span(events[i])
        stem_x = convert_year_to_x(events[i][0])
        lane = 0
        while lane < max_lane:
            is_clear = True
            for placed_lane, (placed_start, placed_end), placed_stem_x in placement_by_event_index_map.values():
                if (placed_lane == lane and not (label_end + 0.15 < placed_start or label_start > placed_end + 0.15)
                        or placed_lane > lane and label_start - 0.05 < placed_stem_x < label_end + 0.05
                        or placed_lane < lane and placed_start - 0.05 < stem_x < placed_end + 0.05):
                    is_clear = False
            if is_clear:
                break
            lane += 1
        placement_by_event_index_map[i] = (min(lane, max_lane), (label_start, label_end), stem_x)
    return [placement_by_event_index_map[i][0] for i in range(len(events))]


def get_timeline_chart(start_year: float, end_year: float, events: list[tuple] = (), periods: list[tuple] = (),
                       lives: list[tuple] = (), width: float = 12.0, step_years: float | None = None,
                       font_size: float = SMALL_FONT_SIZE, lane_height: float = 0.55,
                       color_by_name_map: dict | None = None,
                       label_by_tick_value_map: dict | None = None) -> VGroup:
    """A year axis with three kinds of rows, lanes assigned so nothing overlaps:
    periods [(from, to, "名稱")] as bands, lives [("人名", born, died)] as thin bars, events [(year, "事件")] as ticks
    with labels. Parts: .axis, .periods[name], .lives[name], .events[label]; tl.convert_year_to_x(year) is the frame x
    of a year. label_by_tick_value_map {value: "label"} replaces the year numbers, for an axis of days or hours
    ({6: "8/6", 9: "8/9"})."""
    step_years = step_years or choose_tick_step(end_year - start_year)
    convert_year_to_x = lambda year: -width / 2 + (year - start_year) / (end_year - start_year) * width
    axis = VGroup(Line([convert_year_to_x(start_year), 0, 0], [convert_year_to_x(end_year), 0, 0])
                  .set_stroke(GREY_B, 2))
    year = math.ceil(start_year / step_years) * step_years
    tick_marks = sorted(label_by_tick_value_map.items()) if label_by_tick_value_map else []
    while not label_by_tick_value_map and year <= end_year:
        tick_marks.append((year, f"{int(year)}"))
        year += step_years
    tick_spans = []
    for tick_value, text in tick_marks:
        tick_x = convert_year_to_x(tick_value)
        axis.add(Line([tick_x, -0.08, 0], [tick_x, 0.08, 0]).set_stroke(GREY_B, 2))
        label = Text(str(text), font_size=font_size - 4)
        axis.add(label.set_color(GREY_B).move_to([tick_x, -0.3, 0]))
        tick_spans.append((label.get_left()[0] - 0.04, label.get_right()[0] + 0.04))

    def assign_lanes(entries, compute_span):
        lane_ends, lanes = [], []
        for entry in entries:
            span_start, span_end = compute_span(entry)
            for lane_index, lane_end in enumerate(lane_ends):
                if span_start > lane_end + 0.15:
                    lane_ends[lane_index] = span_end
                    lanes.append(lane_index)
                    break
            else:
                lane_ends.append(span_end)
                lanes.append(len(lane_ends) - 1)
        return lanes

    period_by_name_map, life_by_name_map, event_by_label_map = {}, {}, {}
    # periods above the axis
    period_specs = list(periods)
    compute_period_span = lambda period_spec: (convert_year_to_x(period_spec[0]), convert_year_to_x(period_spec[1]))
    for (period_start, period_end, name, *rest), lane_index in zip(period_specs,
                                                                  assign_lanes(period_specs, compute_period_span)):
        default_color = CHART_COLORS[len(period_by_name_map) % len(CHART_COLORS)]
        color = (color_by_name_map or {}).get(name, rest[0] if rest else default_color)
        start_x, end_x = convert_year_to_x(period_start), convert_year_to_x(period_end)
        band = (Rectangle(width=max(end_x - start_x, 0.02), height=lane_height * 0.8).set_fill(color, 0.35)
                .set_stroke(color, 1.5))
        band.move_to([(start_x + end_x) / 2, 0.55 + lane_index * lane_height, 0])
        label_mobject = Text(name, font_size=font_size).set_color(WHITE).move_to(band)
        if label_mobject.get_width() > band.get_width() - 0.1:
            label_mobject.next_to(band, RIGHT, 0.08)
        period_by_name_map[name] = VGroup(band, label_mobject)
    period_lane_count = max(assign_lanes(period_specs, compute_period_span), default=-1) + 1
    lives_base_y = 0.55 + period_lane_count * lane_height + 0.15
    life_specs = list(lives)
    measure_label_width = lambda text: Text(text, font_size=font_size - 2).get_width()
    clamp_year = lambda year: min(max(year, start_year), end_year)
    compute_life_span = lambda life_spec: (convert_year_to_x(clamp_year(life_spec[1])),
                                           convert_year_to_x(clamp_year(life_spec[2])) + 0.1
                                           + measure_label_width(life_spec[0]))
    for (name, born, died, *rest), lane_index in zip(life_specs, assign_lanes(life_specs, compute_life_span)):
        color = (color_by_name_map or {}).get(name, rest[0] if rest else GOLD_C)
        bar = (Line([convert_year_to_x(clamp_year(born)), 0, 0], [convert_year_to_x(clamp_year(died)), 0, 0])
               .set_stroke(color, 5).shift((lives_base_y + lane_index * lane_height) * UP))
        label_mobject = Text(name, font_size=font_size - 2).set_color(color).next_to(bar, RIGHT, 0.08)
        life_by_name_map[name] = VGroup(bar, label_mobject)
    sorted_event_specs = sorted(events, key=lambda event_spec: event_spec[0])
    # near the right end: label runs leftwards
    check_does_label_run_left = lambda event_spec: (convert_year_to_x(event_spec[0])
                                                    + measure_label_width(event_spec[1]) > width / 2)

    def compute_label_span(event_spec):
        event_x, label_width = convert_year_to_x(event_spec[0]), measure_label_width(event_spec[1])
        if check_does_label_run_left(event_spec):
            return event_x - label_width - 0.05, event_x + 0.02
        return event_x - 0.02, event_x + label_width + 0.05

    for (event_year, label, *rest), lane_index in zip(
            sorted_event_specs, _assign_event_lanes(sorted_event_specs, compute_label_span, convert_year_to_x)):
        color = rest[0] if rest else YELLOW
        y = -0.75 - lane_index * lane_height
        event_x = convert_year_to_x(event_year)
        # a stem starts below the axis labels it would cross, so it never runs through a date
        stem_top = -0.48 if any(span_start < event_x < span_end for span_start, span_end in tick_spans) else 0
        tick = Line([event_x, stem_top, 0], [event_x, y + 0.12, 0]).set_stroke(color, 1.5)
        dot = Dot([event_x, 0, 0], radius=0.06, fill_color=color)
        label_mobject = Text(label, font_size=font_size - 2).set_color(color).move_to(
            [event_x, y, 0], aligned_edge=RIGHT if check_does_label_run_left((event_year, label)) else LEFT)
        event_by_label_map[label] = VGroup(tick, dot, label_mobject)
    chart = TimelineChart(axis, KeyedGroup(period_by_name_map), KeyedGroup(life_by_name_map),
                          KeyedGroup(event_by_label_map))
    chart.axis, chart.periods, chart.lives, chart.events = axis, chart[1], chart[2], chart[3]
    chart._year_span = (start_year, end_year, width)
    return chart


class TimelineChart(Parts):
    """What get_timeline_chart returns: .axis, .periods[name], .lives[name], .events[label],
    .convert_year_to_x(year)."""

    def convert_year_to_x(self, year: float) -> float:
        """Frame x of a year, as built (before any later move of the chart)."""
        start_year, end_year, width = self._year_span
        return -width / 2 + (year - start_year) / (end_year - start_year) * width
