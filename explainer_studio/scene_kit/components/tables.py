"""Tables and grids of numbers: plain tables lit cell by cell, heatmaps (attention patterns, matrices) and column
vectors."""

from __future__ import annotations

from manimlib import *

from ..parts import Parts
from ..style import HIGHLIGHT_COLOR, SMALL_FONT_SIZE

__all__ = ["GridTable", "get_cell_highlight", "get_heatmap", "get_table", "get_vector_column"]


class GridTable(Parts):
    """What get_table returns: .cells[row_index][column_index], .header_cells[column_index], .grid,
    .get_row(row_index), .get_column(column_index)."""

    def get_row(self, row_index: int) -> VGroup:
        return VGroup(*self.cells[row_index])

    def get_column(self, column_index: int) -> VGroup:
        return VGroup(*(row[column_index] for row in self.cells))


def get_table(rows: list[list], header: list | None = None, font_size: float = SMALL_FONT_SIZE + 4,
              column_widths: list[float] | None = None, row_height: float = 0.6, header_color=GREY_A,
              line_color=GREY_D) -> GridTable:
    """A plain grid table. Parts: .cells[row_index][column_index] (the header is .header_cells[column_index]),
    .get_row(row_index), .get_column(column_index), .grid."""
    def get_cell_text(value):
        return Text(str(value), font_size=font_size)

    column_count = max(len(row) for row in ([header] if header else []) + rows)
    text_rows = [[get_cell_text(value) for value in row] + [VGroup() for _ in range(column_count - len(row))]
                 for row in rows]
    header_texts = [get_cell_text(value).set_color(header_color) for value in header] if header else []

    def check_is_filled(cell):
        return len(cell.get_family()) > 1 or cell.has_points()

    resolved_column_widths = column_widths or [
        max([cell.get_width() for cell in column if check_is_filled(cell)] + [0.6]) + 0.5
        for column in zip(*(([header_texts] if header_texts else []) + text_rows))]
    column_xs = np.cumsum([0] + resolved_column_widths)
    cell_rows = VGroup()
    all_rows = ([header_texts] if header_texts else []) + text_rows
    for row_index, row in enumerate(all_rows):
        for column_index, cell in enumerate(row):
            if check_is_filled(cell):
                cell.move_to([(column_xs[column_index] + column_xs[column_index + 1]) / 2, -row_index * row_height,
                              0])
        cell_rows.add(VGroup(*row))
    grid = VGroup()
    total_height = len(all_rows) * row_height
    for row_index in range(len(all_rows) + 1):
        y = row_height / 2 - row_index * row_height
        stroke_width = 2 if (header_texts and row_index == 1) else 1
        grid.add(Line([0, y, 0], [column_xs[-1], y, 0]).set_stroke(line_color, stroke_width))
    for column_index in range(1, len(resolved_column_widths)):
        column_x = column_xs[column_index]
        grid.add(Line([column_x, row_height / 2, 0], [column_x, row_height / 2 - total_height, 0])
                 .set_stroke(line_color, 1))
    table = GridTable(grid, cell_rows).center()
    table.grid = grid
    table.header_cells = cell_rows[0] if header_texts else VGroup()
    table.cells = VGroup(*(cell_rows[1:] if header_texts else cell_rows))
    table.row_height = row_height
    return table


def get_cell_highlight(table: GridTable, row_index: int, column_index: int, color=HIGHLIGHT_COLOR,
                       buff: float = 0.08) -> Rectangle:
    """A thin rectangle around table.cells[row_index][column_index], sized to the grid cell."""
    cell = table.cells[row_index][column_index]
    line_xs = sorted({round(line.get_start()[0], 4) for line in table.grid
                 if abs(line.get_start()[0] - line.get_end()[0]) < 1e-6})
    left = max([x for x in line_xs if x <= cell.get_center()[0]] + [table.get_left()[0]])
    right = min([x for x in line_xs if x >= cell.get_center()[0]] + [table.get_right()[0]])
    rectangle = Rectangle(width=right - left - buff, height=table.row_height - buff)
    return rectangle.move_to([(left + right) / 2, cell.get_center()[1], 0]).set_stroke(color, 2.5)


def _interpolate_stop_color(stop_colors: list[str], t: float) -> str:
    t = min(max(t, 0.0), 1.0) * (len(stop_colors) - 1)
    i = min(int(t), len(stop_colors) - 2)
    return interpolate_color(stop_colors[i], stop_colors[i + 1], t - i)


def get_heatmap(values, row_labels: list[str] | None = None, column_labels: list[str] | None = None,
                cell_size: float = 0.45, min_value: float | None = None, max_value: float | None = None,
                stop_colors: tuple = ("#101820", "#1C758A", "#58C4DD", "#FFFF00"), should_show_values: bool = False,
                label_font_size: float = SMALL_FONT_SIZE, decimal_place_count: int = 2) -> VGroup:
    """A grid of coloured squares (an attention pattern, a weight matrix). Colours interpolate through `stop_colors`
    from min_value to max_value (min_value defaults to 0 for non-negative data). Parts: .cells[i][j], .row_labels,
    .column_labels."""
    array = np.array(values, dtype=float)
    low_value = (0.0 if array.min() >= 0 else array.min()) if min_value is None else min_value
    high_value = array.max() if max_value is None else max_value
    span = (high_value - low_value) or 1.0
    cells, cell_rows = VGroup(), []
    for i in range(array.shape[0]):
        row = VGroup()
        for j in range(array.shape[1]):
            fraction = (array[i, j] - low_value) / span
            square = (Square(cell_size).set_stroke(BLACK, 1)
                      .set_fill(_interpolate_stop_color(list(stop_colors), fraction), 1))
            square.move_to([j * cell_size, -i * cell_size, 0])
            if should_show_values:
                number = DecimalNumber(array[i, j], num_decimal_places=decimal_place_count,
                                       font_size=label_font_size * 0.8)
                square = VGroup(square, number.set_color(BLACK if fraction > 0.6 else WHITE).move_to(square))
            row.add(square)
        cell_rows.append(row)
        cells.add(row)
    group = Parts(cells)
    row_label_group, column_label_group = VGroup(), VGroup()
    for i, label in enumerate(row_labels or []):
        row_label_group.add(Text(str(label), font_size=label_font_size).next_to(cell_rows[i][0], LEFT, 0.15))
    for j, label in enumerate(column_labels or []):
        text = Text(str(label), font_size=label_font_size).next_to(cell_rows[0][j], UP, 0.15)
        if text.get_width() > cell_size * 1.1:
            text.rotate(PI / 2, about_point=text.get_center()).next_to(cell_rows[0][j], UP, 0.15)
        column_label_group.add(text)
    group.add(row_label_group, column_label_group)
    group.center()
    group.cells, group.row_labels, group.column_labels = cells, row_label_group, column_label_group
    return group


def get_vector_column(values, color=BLUE, width: float = 0.9, height: float = 0.42,
                      font_size: float = SMALL_FONT_SIZE, decimal_place_count: int = 1, has_brackets: bool = True,
                      shown_entry_count: int | None = None) -> VGroup:
    """A column vector as stacked cells with numbers, optionally cut with a ⋮ after shown_entry_count entries.
    Parts: .entries[i], .brackets."""
    values = list(values)
    if shown_entry_count is None or len(values) <= shown_entry_count:
        shown_values = values
    else:
        shown_values = values[:shown_entry_count]
    entries = VGroup()
    for value in shown_values:
        box = Rectangle(width=width, height=height).set_stroke(color, 1.5).set_fill(color, 0.12)
        number = (DecimalNumber(value, num_decimal_places=decimal_place_count, font_size=font_size)
                  if isinstance(value, (int, float)) else Tex(str(value), font_size=font_size))
        entries.add(VGroup(box, number.move_to(box)))
    entries.arrange(DOWN, buff=0)
    group = Parts(entries)
    if shown_entry_count is not None and len(values) > shown_entry_count:
        group.add(Tex(R"\vdots", font_size=font_size + 8).set_color(color).next_to(entries, DOWN, 0.1))
    group.entries, group.brackets = entries, VGroup()
    if has_brackets:
        top_left, bottom_left = group.get_corner(UL), group.get_corner(DL)
        left = VMobject().set_points_as_corners([
            top_left + 0.15 * LEFT + 0.05 * UP, top_left + 0.25 * LEFT + 0.05 * UP,
            bottom_left + 0.25 * LEFT + 0.05 * DOWN, bottom_left + 0.15 * LEFT + 0.05 * DOWN])
        right = left.copy().flip(UP, about_point=group.get_center())
        group.brackets = VGroup(left, right).set_stroke(GREY_A, 2)
        group.add(group.brackets)
    return group
