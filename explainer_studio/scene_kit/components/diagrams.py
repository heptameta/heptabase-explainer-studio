"""Diagrams: flowcharts and architectures laid out automatically, trees, things flowing along edges, sequence
diagrams, data structures (arrays, pointers, linked lists, stacks), thin curved arrows, two versions side by side,
alternatives not chosen, and blocks relabelled or knocked out of a system."""

from __future__ import annotations

import itertools
import math

from manimlib import *

from ..parts import KeyedGroup, Parts
from ..style import LABEL_FONT_SIZE, MONO_FONT, SMALL_FONT_SIZE, choose_local_text
from .emphasis import dim, undim

__all__ = [
    "flow_along",
    "get_alternative",
    "get_array",
    "get_curved_arrow",
    "get_flow_token",
    "get_graph_diagram",
    "get_linked_list",
    "get_pointer",
    "get_sequence_diagram",
    "get_side_by_side",
    "get_stack",
    "get_tree",
    "knock_out",
    "put_back",
    "relabel",
    "run_both",
    "swap_cells",
]


def get_curved_arrow(start, end, angle: float = -PI / 3, color=GREY_B, stroke_width: float = 3,
                     tip_size: float = 0.18) -> VGroup:
    """A thin curved arrow from start to end (points or mobjects): an arc with a small filled tip. ManimGL's
    CurvedArrow fills its whole body when given a fill colour and turns into a blob; this keeps the line a line.
    angle: how far the arc bends (negative bends clockwise). Parts: .arc, .tip."""
    p0 = start.get_center() if isinstance(start, Mobject) else np.array(start, dtype=float)
    p1 = end.get_center() if isinstance(end, Mobject) else np.array(end, dtype=float)
    arc = ArcBetweenPoints(p0, p1, angle=angle).set_stroke(color, stroke_width).set_fill(opacity=0)
    direction = p1 - arc.point_from_proportion(0.96)
    tip = Triangle().set_stroke(width=0).set_fill(color, 1).set_height(tip_size)
    tip.rotate(math.atan2(direction[1], direction[0]) - PI / 2).move_to(p1 - 0.5 * tip_size * direction / (np.linalg.norm(direction) + 1e-9))
    group = Parts(arc, tip)
    group.arc, group.tip = arc, tip
    return group



def _compute_layered_layout(node_ids: list[str], edges: list[tuple],
                            size_by_node_id_map: dict[str, tuple[float, float]], layer_spacing: float,
                            node_spacing: float) -> tuple[dict, dict]:
    """Sugiyama layered layout via grandalf, in its own frame: layers stacked along +y, nodes spread along x.
    Sizes are (along-x, along-y) extents. Returns node centres and edge routes (lists of points, already clipped to
    node borders; long edges bend around intermediate layers)."""
    from grandalf.graphs import Edge, Graph, Vertex
    from grandalf.layouts import SugiyamaLayout
    from grandalf.routing import EdgeViewer

    class _View:
        def __init__(self, w, h):
            self.w, self.h, self.xy = w, h, (0.0, 0.0)

    vertex_by_id_map = {node_id: Vertex(node_id) for node_id in node_ids}
    for node_id, vertex in vertex_by_id_map.items():
        vertex.view = _View(*size_by_node_id_map[node_id])
    grandalf_edges = []
    for source_id, target_id in edges:
        edge = Edge(vertex_by_id_map[source_id], vertex_by_id_map[target_id])
        edge.view = EdgeViewer()
        grandalf_edges.append(edge)
    graph = Graph(list(vertex_by_id_map.values()), grandalf_edges)
    center_by_node_id_map, route_by_edge_map = {}, {}
    offset = 0.0
    for component in graph.C:
        sugiyama_layout = SugiyamaLayout(component)
        sugiyama_layout.xspace, sugiyama_layout.yspace = node_spacing, layer_spacing
        # clipping to node borders happens later
        sugiyama_layout.route_edge = lambda edge, points: edge.view.setpath(list(points))
        roots = [vertex for vertex in component.sV if len(vertex.e_in()) == 0] or None
        sugiyama_layout.init_all(roots=roots)
        sugiyama_layout.draw()
        xs = [vertex.view.xy[0] for vertex in component.sV]
        shift = offset - min(xs) + max(vertex.view.w for vertex in component.sV)
        for vertex in component.sV:
            center_by_node_id_map[vertex.data] = (vertex.view.xy[0] + shift, vertex.view.xy[1])
        for edge in component.sE:
            points = getattr(edge.view, "_pts", None) or [edge.v[0].view.xy, edge.v[1].view.xy]
            route_by_edge_map[(edge.v[0].data, edge.v[1].data)] = [(point[0] + shift, point[1]) for point in points]
        offset = max(point[0] for point in center_by_node_id_map.values()) + node_spacing * 2
    return center_by_node_id_map, route_by_edge_map


def get_graph_diagram(nodes: list, edges: list, direction: str = "LR", font_size: float = LABEL_FONT_SIZE - 4,
                      color_by_node_id_map: dict | None = None, edge_color=GREY_B, max_width: float = 12.5,
                      max_height: float = 6.5, min_node_width: float = 1.6, shape: str = "box",
                      dashed_edges: list[tuple] = ()) -> VGroup:
    """Flowchart / architecture / DAG laid out automatically (layered, like Graphviz dot).
    nodes: ["api", ("db", "資料庫"), ...]; edges: [("api", "db"), ("api", "cache", "讀取"), ...].
    direction: LR, RL, TB or BT. shape: box | round | circle. dashed_edges: the edges [(a, b), ...] drawn dashed.
    Parts: .nodes[id] (VGroup(shape, label)); .edges[(a, b)] (VGroup(line, tip[, label])); .paths[(a, b)] (the edge's
    line itself, so flow_along can move a token along it; it moves with the diagram). Long edges bend around the
    layers in between instead of crossing nodes."""
    color_by_node_id_map = color_by_node_id_map or {}
    node_id_and_label_pairs = [(node, node) if isinstance(node, str) else (node[0], node[1]) for node in nodes]
    node_ids = [node_id for node_id, _ in node_id_and_label_pairs]
    is_horizontal = direction in ("LR", "RL")
    node_by_id_map, size_by_node_id_map = {}, {}
    for node_id, label in node_id_and_label_pairs:
        label_mobject = Text(str(label), font_size=font_size)
        color = color_by_node_id_map.get(node_id, GREY_A)
        if shape == "circle":
            body = Circle(radius=max(label_mobject.get_width(), label_mobject.get_height()) / 2 + 0.25)
        else:
            body = RoundedRectangle(width=max(min_node_width, label_mobject.get_width() + 0.6),
                                    height=label_mobject.get_height() + 0.5,
                                    corner_radius=0.25 if shape == "round" else 0.08)
        body.set_stroke(color, 2).set_fill(interpolate_color(BLACK, color, 0.12), 1)
        node_by_id_map[node_id] = VGroup(body, label_mobject.move_to(body))
        width, height = body.get_width(), body.get_height()
        # grandalf: x across a layer, y along layers
        size_by_node_id_map[node_id] = (height, width) if is_horizontal else (width, height)
    label_by_edge_map = {(edge[0], edge[1]): edge[2] for edge in edges if len(edge) > 2 and edge[2]}
    label_mobject_by_edge_map = {edge: Text(str(label), font_size=font_size - 6).set_color(GREY_A)
                                 for edge, label in label_by_edge_map.items()}
    longest_label = max([label_mobject.get_width() for label_mobject in label_mobject_by_edge_map.values()] + [0.0])
    layer_spacing = (max(1.1, longest_label + 0.7) if is_horizontal else 1.0)
    node_spacing = 0.6 if is_horizontal else 0.5
    center_by_node_id_map, route_by_edge_map = _compute_layered_layout(
        node_ids, [(edge[0], edge[1]) for edge in edges], size_by_node_id_map, layer_spacing, node_spacing)

    def convert_layout_point_to_frame_point(point):
        x, y = point
        return {"LR": np.array([y, -x, 0]), "RL": np.array([-y, -x, 0]),
                "TB": np.array([x, -y, 0]), "BT": np.array([x, y, 0])}[direction]

    for node_id, center in center_by_node_id_map.items():
        node_by_id_map[node_id].move_to(convert_layout_point_to_frame_point(center))
    edge_group_by_edge_map, path_by_edge_map = {}, {}
    all_edges = VGroup()
    for edge in edges:
        key = (edge[0], edge[1])
        points = [convert_layout_point_to_frame_point(point) for point in route_by_edge_map[key]]
        points[0] = _compute_border_point(node_by_id_map[key[0]][0], points[1])
        points[-1] = _compute_border_point(node_by_id_map[key[1]][0], points[-2])
        line = VMobject()
        if len(points) > 2:
            line.set_points_smoothly(points)
        else:
            line.set_points_as_corners(points)
        line.set_stroke(edge_color, 3)
        tip_direction = points[-1] - line.point_from_proportion(0.97)
        if key in set(map(tuple, dashed_edges)):   # a road not taken, a link that is only proposed, an indirect vote
            line = DashedVMobject(line, num_dashes=max(6, int(line.get_arc_length() / 0.18))).set_stroke(edge_color, 3)
        tip = ArrowTip(width=0.2, length=0.2).set_fill(edge_color, 1)
        tip.rotate(math.atan2(tip_direction[1], tip_direction[0]) - tip.get_angle() if hasattr(tip, "get_angle") else math.atan2(tip_direction[1], tip_direction[0]))
        tip.shift(points[-1] - tip.get_tip_point() if hasattr(tip, "get_tip_point") else points[-1] - tip.get_center())
        edge_group = VGroup(line, tip)
        if key in label_mobject_by_edge_map:
            label_mobject = label_mobject_by_edge_map[key]
            midpoint = line.point_from_proportion(0.5)
            label_mobject.move_to(midpoint + 0.24 * _compute_normal(points[0], points[-1]))
            background = BackgroundRectangle(label_mobject, fill_opacity=0.85, buff=0.05)
            edge_group.add(background, label_mobject)
            edge_group.label = label_mobject
        edge_group_by_edge_map[key], path_by_edge_map[key] = edge_group, line
        all_edges.add(edge_group)
    diagram = Parts(all_edges, VGroup(*node_by_id_map.values()))
    diagram.set_max_width(max_width).set_max_height(max_height).center()
    diagram.nodes, diagram.edges = KeyedGroup(node_by_id_map), KeyedGroup(edge_group_by_edge_map)
    diagram.paths = KeyedGroup(path_by_edge_map)
    return diagram


def _compute_border_point(box: VMobject, toward: np.ndarray) -> np.ndarray:
    center = box.get_center()
    direction = toward - center
    if np.linalg.norm(direction[:2]) < 1e-9:
        return center
    half_width, half_height = box.get_width() / 2, box.get_height() / 2
    scale = min(half_width / abs(direction[0]) if abs(direction[0]) > 1e-9 else np.inf,
                half_height / abs(direction[1]) if abs(direction[1]) > 1e-9 else np.inf)
    return center + direction * scale


def _compute_normal(p0, p1):
    direction = (p1 - p0)
    normal = np.array([-direction[1], direction[0], 0])
    return normal / (np.linalg.norm(normal) or 1)


def get_tree(tree, font_size: float = LABEL_FONT_SIZE - 4, level_spacing: float = 1.3, sibling_spacing: float = 0.4,
             node_color=GREY_A, shape: str = "circle", max_width: float = 12.5, max_height: float = 6.5) -> VGroup:
    """Tidy tree drawn top-down. tree = ("root", [child, child, ...]) where a child is a label or the same form.
    Parts: .nodes[path] (path is a tuple of child indices, root = ()), .edges[path] (line from parent to that node),
    .node_by_label_map[label] (first node with that label)."""
    node_by_path_map, edge_by_path_map, node_by_label_map = {}, {}, {}

    def build(subtree, path):
        if isinstance(subtree, (tuple, list)):
            label, children = subtree[0], list(subtree[1]) if len(subtree) > 1 else []
        else:
            label, children = subtree, []
        label_mobject = Text(str(label), font_size=font_size)
        if shape == "circle":
            body = Circle(radius=max(label_mobject.get_width(), label_mobject.get_height()) / 2 + 0.18)
        else:
            body = RoundedRectangle(width=label_mobject.get_width() + 0.5, height=label_mobject.get_height() + 0.4,
                                    corner_radius=0.08)
        body.set_stroke(node_color, 2).set_fill(BLACK, 1)
        node_by_path_map[path] = VGroup(body, label_mobject.move_to(body))
        node_by_label_map.setdefault(str(label), node_by_path_map[path])
        return [build(child, path + (i,)) for i, child in enumerate(children)] or None, path

    build(tree, ())
    # simple tidy layout: leaves get consecutive x slots, parents centre over children
    x_by_path_map, depth_by_path_map = {}, {}
    next_leaf_x = [0.0]

    def place(path, depth):
        children = sorted(node_path for node_path in node_by_path_map
                          if len(node_path) == len(path) + 1 and node_path[:-1] == path)
        depth_by_path_map[path] = depth
        if not children:
            width = node_by_path_map[path].get_width()
            x_by_path_map[path] = next_leaf_x[0] + width / 2
            next_leaf_x[0] += width + sibling_spacing
        else:
            for child in children:
                place(child, depth + 1)
            x_by_path_map[path] = (x_by_path_map[children[0]] + x_by_path_map[children[-1]]) / 2

    place((), 0)
    for path, node in node_by_path_map.items():
        node.move_to([x_by_path_map[path], -depth_by_path_map[path] * level_spacing, 0])
    edge_group = VGroup()
    for path in node_by_path_map:
        if path:
            parent = node_by_path_map[path[:-1]][0]
            child = node_by_path_map[path][0]
            line = Line(parent.get_center(), child.get_center()).set_stroke(GREY_B, 2)
            line.put_start_and_end_on(_compute_circle_border_point(parent, child.get_center()), _compute_circle_border_point(child, parent.get_center()))
            edge_by_path_map[path] = line
            edge_group.add(line)
    group = Parts(edge_group, VGroup(*node_by_path_map.values()))
    group.set_max_width(max_width).set_max_height(max_height).center()
    group.nodes, group.edges = KeyedGroup(node_by_path_map), KeyedGroup(edge_by_path_map)
    group.node_by_label_map = node_by_label_map
    return group


def _compute_circle_border_point(body, toward):
    center = body.get_center()
    direction = toward - center
    distance = np.linalg.norm(direction)
    if distance < 1e-9:
        return center
    radius = min(body.get_width(), body.get_height()) / 2
    return center + direction / distance * radius



def get_flow_token(color=YELLOW, radius: float = 0.09, label: str = "") -> VGroup:
    """A glowing dot (optionally labelled) to send along paths with flow_along."""
    dot = Dot(radius=radius).set_fill(color, 1)
    glow = Dot(radius=radius * 2.2).set_fill(color, 0.25)
    token = VGroup(glow, dot)
    if label:
        token.add(Text(label, font_size=SMALL_FONT_SIZE).set_color(color).next_to(dot, UP, 0.08))
    return token


def flow_along(token: Mobject, paths: list[VMobject], run_time_per_edge: float = 0.9) -> Animation:
    """Move token through a sequence of paths (e.g. [diagram.paths[("user","api")], diagram.paths[("api","db")]])."""
    animations = [MoveAlongPath(token, path, run_time=run_time_per_edge, rate_func=smooth) for path in paths]
    return Succession(*animations)



def get_sequence_diagram(actors: list, messages: list, width: float = 12.0, row_spacing: float = 0.75,
                         font_size: float = LABEL_FONT_SIZE - 6, color_by_actor_id_map: dict | None = None) -> VGroup:
    """Sequence diagram. actors: ["browser", ("api", "API"), ...]; messages: [("browser", "api", "POST /clip"), ...]
    (from == to draws a self-call). Parts: .actors[id], .lifelines[id], .messages[i] (VGroup(arrow, label)).
    Reveal messages one by one to walk through a protocol."""
    color_by_actor_id_map = color_by_actor_id_map or {}
    actor_id_and_label_pairs = [(actor, actor) if isinstance(actor, str) else (actor[0], actor[1]) for actor in actors]
    actor_count = len(actor_id_and_label_pairs)
    actor_xs = np.linspace(-width / 2, width / 2, actor_count) if actor_count > 1 else [0]
    head_by_actor_id_map, lifeline_by_actor_id_map = {}, {}
    total_height = (len(messages) + 1) * row_spacing
    group = Parts()
    for (actor_id, label), x in zip(actor_id_and_label_pairs, actor_xs):
        label_mobject = Text(str(label), font_size=font_size)
        color = color_by_actor_id_map.get(actor_id, GREY_A)
        box = RoundedRectangle(width=max(1.6, label_mobject.get_width() + 0.5), height=label_mobject.get_height() + 0.45, corner_radius=0.08)
        box.set_stroke(color, 2).set_fill(interpolate_color(BLACK, color, 0.12), 1).move_to([x, 0, 0])
        head_by_actor_id_map[actor_id] = VGroup(box, label_mobject.move_to(box))
        lifeline = DashedLine(box.get_bottom(), box.get_bottom() + total_height * DOWN, dash_length=0.08)
        lifeline.set_stroke(GREY_D, 1.5)
        lifeline_by_actor_id_map[actor_id] = lifeline
        group.add(lifeline, head_by_actor_id_map[actor_id])
    message_mobjects = VGroup()
    for index, (sender_id, receiver_id, text) in enumerate(messages):
        y = head_by_actor_id_map[actor_id_and_label_pairs[0][0]].get_bottom()[1] - (index + 1) * row_spacing
        sender_x = head_by_actor_id_map[sender_id].get_center()[0]
        receiver_x = head_by_actor_id_map[receiver_id].get_center()[0]
        label_mobject = Text(str(text), font_size=font_size - 4).set_color(GREY_A)
        if sender_id == receiver_id:
            path = VMobject().set_points_as_corners([[sender_x, y + 0.15, 0], [sender_x + 0.7, y + 0.15, 0],
                                                     [sender_x + 0.7, y - 0.15, 0], [sender_x + 0.08, y - 0.15, 0]])
            tip = ArrowTip().scale(0.5).rotate(PI).move_to([sender_x + 0.12, y - 0.15, 0]).set_fill(GREY_B)
            arrow = VGroup(path.set_stroke(GREY_B, 2.5), tip)
            label_mobject.next_to([sender_x + 0.7, y, 0], RIGHT, 0.12)
        else:
            arrow = Arrow([sender_x, y, 0], [receiver_x, y, 0], buff=0.05, stroke_width=3,
                          max_tip_length_to_length_ratio=0.08).set_color(GREY_B)
            label_mobject.next_to(arrow, UP, 0.06)
        message = VGroup(arrow, label_mobject)
        message_mobjects.add(message)
    group.add(message_mobjects)
    group.set_max_width(width + 1).center()
    group.actors, group.lifelines = KeyedGroup(head_by_actor_id_map), KeyedGroup(lifeline_by_actor_id_map)
    group.messages = VGroup(*message_mobjects)
    return group



def get_array(values: list, cell_size: float = 0.75, color=BLUE_C, font_size: float = LABEL_FONT_SIZE - 4,
              should_show_indices: bool = True) -> VGroup:
    """Array as a row of boxes. Parts: .cells[i] (VGroup(box, value)), .indices[i].
    Swap two cells with swap_cells(array, i, j)."""
    cells, index_labels = VGroup(), VGroup()
    for i, value in enumerate(values):
        box = Square(cell_size).set_stroke(color, 2).set_fill(color, 0.1)
        value_text = Text(str(value), font_size=font_size)
        cells.add(VGroup(box, value_text.move_to(box)))
    cells.arrange(RIGHT, buff=0)
    if should_show_indices:
        for i, cell in enumerate(cells):
            index_labels.add(Text(str(i), font=MONO_FONT, font_size=font_size * 0.6).set_color(GREY_C)
                             .next_to(cell, DOWN, 0.1))
    group = Parts(cells, index_labels).center()
    group.cells, group.indices = cells, index_labels
    return group


def swap_cells(array: VGroup, i: int, j: int) -> list[Animation]:
    """Arc the values of cells i and j into each other's boxes (boxes stay; the value objects move)."""
    value_i, value_j = array.cells[i][1], array.cells[j][1]
    center_i, center_j = array.cells[i][0].get_center(), array.cells[j][0].get_center()
    animations = [value_i.animate(path_arc=PI / 2).move_to(center_j),
                  value_j.animate(path_arc=PI / 2).move_to(center_i)]
    cell_i, cell_j = array.cells[i], array.cells[j]
    cell_i.set_submobjects([cell_i[0], value_j])
    cell_j.set_submobjects([cell_j[0], value_i])
    return animations


def get_pointer(target: Mobject, label: str = "", color=YELLOW, direction=UP) -> VGroup:
    """An arrow pointing at target from `direction`, with an optional label (e.g. 'i', 'head')."""
    start = target.get_edge_center(direction) + 0.9 * direction
    arrow = Arrow(start, target.get_edge_center(direction), buff=0.05, stroke_width=3).set_color(color)
    group = VGroup(arrow)
    if label:
        group.add(Text(label, font=MONO_FONT, font_size=SMALL_FONT_SIZE + 2).set_color(color).next_to(arrow.get_start(), direction, 0.08))
    return group


def get_linked_list(values: list, color=TEAL, font_size: float = LABEL_FONT_SIZE - 4,
                    node_spacing: float = 0.6) -> VGroup:
    """Singly linked list: boxes with value | next-pointer cells joined by arrows. Parts: .nodes[i], .links[i]."""
    nodes, links = VGroup(), VGroup()
    for value in values:
        value_box = Square(0.75).set_stroke(color, 2).set_fill(color, 0.1)
        pointer_box = Rectangle(width=0.35, height=0.75).set_stroke(color, 2).next_to(value_box, RIGHT, buff=0)
        value_text = Text(str(value), font_size=font_size).move_to(value_box)
        nodes.add(VGroup(value_box, pointer_box, value_text, Dot(radius=0.05).set_fill(color, 1).move_to(pointer_box)))
    nodes.arrange(RIGHT, buff=node_spacing)
    for left_node, right_node in itertools.pairwise(nodes):
        links.add(Arrow(left_node[3].get_center(), right_node[0].get_left(), buff=0.05, stroke_width=3)
                  .set_color(GREY_B))
    group = Parts(links, nodes).center()
    group.nodes, group.links = nodes, links
    return group


def get_stack(values: list, color=GOLD_C, font_size: float = LABEL_FONT_SIZE - 4, width: float = 2.2) -> VGroup:
    """Vertical stack, top element last in `values`. Parts: .elements[i]."""
    elements = VGroup()
    for value in values:
        box = Rectangle(width=width, height=0.6).set_stroke(color, 2).set_fill(color, 0.1)
        elements.add(VGroup(box, Text(str(value), font_size=font_size).move_to(box)))
    elements.arrange(UP, buff=0)
    walls = VGroup(Line(elements.get_corner(DL) + 0.1 * LEFT, elements.get_corner(UL) + 0.1 * LEFT + 0.8 * UP),
                   Line(elements.get_corner(DL) + 0.1 * LEFT, elements.get_corner(DR) + 0.1 * RIGHT),
                   Line(elements.get_corner(DR) + 0.1 * RIGHT, elements.get_corner(UR) + 0.1 * RIGHT + 0.8 * UP)).set_stroke(GREY_B, 2)
    group = Parts(walls, elements).center()
    group.elements = elements
    return group



def get_side_by_side(left: Mobject, right: Mobject, labels: tuple[str, str] = ("", ""), spacing: float = 0.8,
                     max_width: float | None = None, font_size: float = SMALL_FONT_SIZE + 2) -> VGroup:
    """Two versions of a toy side by side under their labels, a thin divider between, scaled together to fit the
    frame (the old method and the new one, the claim and its rival). Send the same input through both
    at once with run_both. Parts: .left, .right, .labels, .divider."""
    max_width = max_width if max_width is not None else FRAME_WIDTH - 1.0
    pair = VGroup(left, right).arrange(RIGHT, buff=spacing, aligned_edge=UP)
    if pair.get_width() > max_width:
        pair.set_width(max_width)
    divider = Line(UP, DOWN).set_height(pair.get_height() + 0.4).set_stroke(GREY_D, 1.5)
    divider.move_to((left.get_right() + right.get_left()) / 2).set_y(pair.get_y())
    labels = (labels[0] or choose_local_text("舊的", "before"), labels[1] or choose_local_text("新的", "after"))
    tags = VGroup(*(Text(label, font_size=font_size).set_color(GREY_B) for label in labels))
    tags[0].next_to(left, UP, buff=0.3)
    tags[1].next_to(right, UP, buff=0.3)
    tags.set_y(max(tags[0].get_y(), tags[1].get_y()))
    board = Parts(pair, divider, tags)
    board.left, board.right, board.labels, board.divider = left, right, tags, divider
    return board


def run_both(left_token: Mobject, left_paths: list[VMobject], right_token: Mobject, right_paths: list[VMobject],
             run_time: float = 3.0) -> Animation:
    """The same input through both versions of a get_side_by_side at the same time: each token walks its own paths
    and both arrive together, however many steps each version has, so the viewer sees where they part."""
    return AnimationGroup(flow_along(left_token, left_paths, run_time / max(len(left_paths), 1)),
                          flow_along(right_token, right_paths, run_time / max(len(right_paths), 1)))



def get_alternative(part: Mobject, label: str, direction=RIGHT, buff: float = 0.35, color=GREY_B,
                    font_size: float = SMALL_FONT_SIZE) -> VGroup:
    """The option not chosen for one part of a designed system: a dashed outline the
    size of the part beside it, with what the option was ("每州一票"). Draw the whole system faint first (dim), make a
    part solid at its fork (undim), and put its alternative beside it. Parts: .outline, .label."""
    outline = DashedVMobject(SurroundingRectangle(part, buff=0.05), num_dashes=40).set_stroke(color, 2)
    outline.next_to(part, direction, buff=buff)
    label_text = (Text(label, font_size=font_size).set_color(color).set_max_width(outline.get_width() - 0.2)
                  .move_to(outline))
    alternative = Parts(outline, label_text)
    alternative.outline, alternative.label = outline, label_text
    return alternative



def relabel(node: VGroup, text: str, color=WHITE, font_size: float | None = None) -> Animation:
    """The animation that swaps the label of a get_graph_diagram node (diagram.nodes[id]): a cell that showed its
    plain question until the block was built now shows the block's name. A dimmed node is undimmed in an earlier
    play first (undim restores the old label)."""
    shape, old_label = node[0], node[1]
    resolved_font_size = font_size or LABEL_FONT_SIZE - 4
    new_label = Text(text, font_size=resolved_font_size).set_color(color)
    old_text = getattr(old_label, "text", "")
    if old_text and font_size is None:   # the diagram may have been scaled to fit: match its letter size
        new_label.scale(old_label.get_height() / max(Text(old_text, font_size=resolved_font_size).get_height(), 1e-6))
    new_label.set_max_width(shape.get_width() - 0.2).move_to(shape)
    node.set_submobjects([shape, new_label, *node.submobjects[2:]])
    return FadeTransform(old_label, new_label)


def _list_node_edges(diagram: VGroup, node_id) -> list[Mobject]:
    return [edge for key, edge in diagram.edges.items() if node_id in key]


def knock_out(diagram: VGroup, node_id, color=RED) -> list[Animation]:
    """Animations that take one block out of a get_graph_diagram to show who suffers without it: the block and its
    edges dim, a cross goes over it (the node's .cross). Send the token along the failure route by hand; put the
    block back with put_back."""
    node = diagram.nodes[node_id]
    cross = VGroup(Line(UL, DR), Line(UR, DL)).set_stroke(color, 5)
    cross.set_height(0.6 * node.get_height()).move_to(node)
    node.add(cross)
    node.cross = cross
    return [*dim(node[0], node[1], *_list_node_edges(diagram, node_id)), FadeIn(cross, scale=1.3)]


def put_back(diagram: VGroup, node_id) -> list[Animation]:
    """Animations that undo knock_out: the block and its edges come back as they were and the cross fades away."""
    node = diagram.nodes[node_id]
    # the cross stays in the node, invisible: fading out a part of a group would bring it back with the group
    return [*undim(node[0], node[1], *_list_node_edges(diagram, node_id)),
            node.cross.animate.set_stroke(opacity=0).scale(1.3)]


