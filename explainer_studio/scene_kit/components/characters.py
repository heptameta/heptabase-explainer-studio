"""People for stories: plain geometric figures with poses and expressions, speech and thought bubbles, and crowds.
They stand for a role (a king, a voter, a defendant), not a likeness.

    king = get_person(GOLD_C, hat="crown").shift(3 * LEFT)
    self.play(*say(king, "Taxes double!"))
    self.play(Transform(voter, restyle(voter, expression="angry", pose="arms_up")))
    crowd = get_crowd(24, colors=[BLUE_C, TEAL, GREY_B])
"""

from __future__ import annotations

import random

from manimlib import *

from ..parts import Parts
from ..style import SMALL_FONT_SIZE

__all__ = ["EXPRESSIONS", "POSES", "get_crowd", "get_person", "restyle", "say", "unsay"]

POSES = ("stand", "wave", "point", "arms_up", "think", "shrug")
EXPRESSIONS = ("neutral", "happy", "sad", "surprised", "angry", "thinking", "worried")


def _get_face(head: Circle, expression: str, facing_sign: float) -> VGroup:
    radius = head.get_width() / 2
    center = head.get_center() + facing_sign * radius * 0.18 * RIGHT
    eye_y = center[1] + radius * 0.12
    eyes = VGroup(*[Dot([center[0] + dx * radius, eye_y, 0], radius=radius * 0.09, fill_color=BLACK)
                    for dx in (-0.32, 0.32)])
    mouth_y = center[1] - radius * 0.38
    mouth_width = radius * 0.55
    if expression == "happy":
        mouth = Arc(start_angle=PI + PI / 5, angle=PI - 2 * PI / 5, radius=mouth_width * 0.8)
        mouth.move_to([center[0], mouth_y, 0])
    elif expression in ("sad", "worried"):
        mouth = Arc(start_angle=PI / 5, angle=PI - 2 * PI / 5, radius=mouth_width * 0.8)
        mouth.move_to([center[0], mouth_y - radius * 0.05, 0])
    elif expression == "surprised":
        mouth = Circle(radius=radius * 0.13).move_to([center[0], mouth_y, 0])
    else:
        mouth = Line([center[0] - mouth_width / 2, mouth_y, 0], [center[0] + mouth_width / 2, mouth_y, 0])
        if expression == "thinking":
            mouth.put_start_and_end_on(np.array([center[0] - mouth_width / 2, mouth_y, 0]), np.array([center[0] + mouth_width / 3, mouth_y + radius * 0.06, 0]))
    mouth.set_stroke(BLACK, 3).set_fill(opacity=0)
    face = VGroup(eyes, mouth)
    if expression in ("angry", "worried", "surprised"):
        tilt = {"angry": -0.18, "worried": 0.18, "surprised": 0.0}[expression]
        lift = radius * (0.33 if expression != "surprised" else 0.42)
        for dx, sign in ((-0.32, 1), (0.32, -1)):
            brow_x = center[0] + dx * radius
            brow = Line([brow_x - radius * 0.16, eye_y + lift - sign * tilt * radius, 0], [brow_x + radius * 0.16, eye_y + lift + sign * tilt * radius, 0])
            face.add(brow.set_stroke(BLACK, 3))
    return face


def _get_limb(start, end, color, stroke_width) -> Line:
    return Line(np.array(start, dtype=float), np.array(end, dtype=float)).set_stroke(color, stroke_width)


def get_person(color=BLUE_C, pose: str = "stand", expression: str = "neutral", height: float = 2.2,
               hat: str | None = None, facing: str = "right", skin_color="#F1D3B6") -> VGroup:
    """A simple figure. pose: stand | wave | point | arms_up | think | shrug. expression: neutral | happy | sad |
    surprised | angry | thinking | worried. hat: None | "crown" | "top" | "cap" | "helmet". The body colour is the
    role (keep it constant for one character). Parts: .head, .face, .body, .arms, .legs, .hat."""
    if pose not in POSES:
        raise ValueError(f"pose must be one of {POSES}")
    if expression not in EXPRESSIONS:
        raise ValueError(f"expression must be one of {EXPRESSIONS}")
    size_unit = height / 2.2
    limb_width = 9 * size_unit
    facing_sign = 1 if facing == "right" else -1
    body = RoundedRectangle(width=0.62 * size_unit, height=0.85 * size_unit, corner_radius=0.22 * size_unit).set_fill(color, 1).set_stroke(width=0)
    body.move_to([0, 0.05 * size_unit, 0])
    head = Circle(radius=0.3 * size_unit).set_fill(skin_color, 1).set_stroke(width=0)
    head.next_to(body, UP, buff=0.06 * size_unit)
    left_shoulder = body.get_corner(UL) + [0.08 * size_unit, -0.12 * size_unit, 0]
    right_shoulder = body.get_corner(UR) + [-0.08 * size_unit, -0.12 * size_unit, 0]
    hand_positions = {
        "stand": ((-0.45, -0.75), (0.45, -0.75)),
        "wave": ((-0.45, -0.75), (0.62, 0.55)),
        "point": ((-0.45, -0.75), (0.95, 0.05)),
        "arms_up": ((-0.62, 0.62), (0.62, 0.62)),
        "think": ((-0.45, -0.75), (0.08, 0.62)),
        "shrug": ((-0.62, 0.1), (0.62, 0.1)),
    }[pose]
    left_hand, right_hand = hand_positions
    if facing_sign < 0:   # mirror the pose, not the body
        left_hand, right_hand = (-right_hand[0], right_hand[1]), (-left_hand[0], left_hand[1])
    left_hand_point = body.get_center() + np.array([left_hand[0] * size_unit, left_hand[1] * size_unit, 0])
    right_hand_point = body.get_center() + np.array([right_hand[0] * size_unit, right_hand[1] * size_unit, 0])
    arms = VGroup(_get_limb(left_shoulder, left_hand_point, color, limb_width),
                  _get_limb(right_shoulder, right_hand_point, color, limb_width))
    hip = body.get_bottom() + 0.08 * size_unit * UP
    legs = VGroup(_get_limb(hip + 0.14 * size_unit * LEFT, hip + [-0.2 * size_unit, -0.72 * size_unit, 0], color,
                            limb_width),
                  _get_limb(hip + 0.14 * size_unit * RIGHT, hip + [0.2 * size_unit, -0.72 * size_unit, 0], color,
                            limb_width))
    face = _get_face(head, expression, facing_sign)
    hat_mobject = VGroup()
    top = head.get_top()
    if hat == "crown":
        points = [[-0.26, 0], [-0.26, 0.2], [-0.13, 0.1], [0, 0.25], [0.13, 0.1], [0.26, 0.2], [0.26, 0]]
        hat_mobject = Polygon(*[top + np.array([x * size_unit, y * size_unit - 0.05 * size_unit, 0]) for x, y in points]).set_fill(GOLD, 1).set_stroke(GOLD_E, 1)
    elif hat == "top":
        brim = Rectangle(width=0.7 * size_unit, height=0.06 * size_unit).set_fill(GREY_E, 1).set_stroke(width=0).move_to(top + 0.02 * size_unit * UP)
        crown = Rectangle(width=0.42 * size_unit, height=0.36 * size_unit).set_fill(GREY_E, 1).set_stroke(width=0).next_to(brim, UP, buff=0)
        hat_mobject = VGroup(brim, crown)
    elif hat == "cap":
        hat_mobject = Sector(radius=0.31 * size_unit, angle=PI, start_angle=0).set_fill(color, 1).set_stroke(width=0).move_to(top + 0.04 * size_unit * DOWN, aligned_edge=DOWN)
    elif hat == "helmet":
        hat_mobject = Sector(radius=0.33 * size_unit, angle=PI, start_angle=0).set_fill(GREY_B, 1).set_stroke(GREY_D, 1).move_to(top + 0.1 * size_unit * DOWN, aligned_edge=DOWN)
    person = Parts(legs, arms, body, head, face, hat_mobject)
    person.head, person.face, person.body, person.arms = head, face, body, arms
    person.legs, person.hat = legs, hat_mobject
    person.style = {"color": color, "pose": pose, "expression": expression, "height": height, "hat": hat,
                    "facing": facing, "skin_color": skin_color}
    return person


def restyle(person: VGroup, **changes) -> VGroup:
    """The same character with a new pose / expression / facing, placed where it stands:
    self.play(Transform(p, restyle(p, expression="happy")))."""
    restyled = get_person(**{**person.style, **changes})
    return restyled.move_to(person, aligned_edge=DOWN)


def say(person: VGroup, text: str, is_thought: bool = False, width: float = 3.6, font_size: float = SMALL_FONT_SIZE + 4,
        side=UR) -> list[Animation]:
    """A speech (or thought) bubble above the person; returns the animations and keeps it on person.bubble so
    unsay(person) can remove it."""
    label = Text(text, font_size=font_size).set_color(BLACK)
    if label.get_width() > width:
        label.set_width(width)
    box = RoundedRectangle(width=label.get_width() + 0.5, height=label.get_height() + 0.4, corner_radius=0.2)
    box.set_fill(WHITE, 1).set_stroke(GREY_B, 2)
    anchor = person.head.get_corner(side)
    box.next_to(anchor, side, buff=0.25)
    label.move_to(box)
    if is_thought:
        tail = VGroup(*[Circle(radius=radius).set_fill(WHITE, 1).set_stroke(GREY_B, 2).move_to(interpolate(anchor, box.get_corner(-side), fraction))
                        for radius, fraction in ((0.05, 0.3), (0.09, 0.62))])
    else:
        tip = anchor + 0.08 * (box.get_center() - anchor) / (np.linalg.norm(box.get_center() - anchor) or 1)
        tail_base = box.get_corner(-side) + 0.35 * (box.get_center() - box.get_corner(-side)) / 2
        tail = Polygon(tip, tail_base + 0.18 * RIGHT, tail_base + 0.18 * UP).set_fill(WHITE, 1).set_stroke(GREY_B, 2)
    bubble = VGroup(tail, box, label)
    person.bubble = bubble
    return [FadeIn(bubble, scale=0.9)]


def unsay(person: VGroup) -> list[Animation]:
    bubble = getattr(person, "bubble", None)
    person.bubble = None
    return [FadeOut(bubble)] if bubble is not None else []


def get_crowd(person_count: int, colors: list | None = None, height: float = 1.1, width: float = 10.0,
              row_count: int | None = None, seed: int = 1,
              expressions: tuple = ("neutral", "happy", "thinking", "worried")) -> VGroup:
    """person_count people in staggered rows (back rows smaller). Parts: crowd[i] are the people; recolour a share of
    them to show a proportion (crowd[:k].set_color(...))."""
    random_generator = random.Random(seed)
    row_count = row_count or max(1, round((person_count / 12) ** 0.5 + 0.49))
    max_row_size = -(-person_count // row_count)
    people = []
    for row_index in range(row_count):
        row_size = min(max_row_size, person_count - row_index * max_row_size)
        scale = 1 - 0.12 * (row_count - 1 - row_index)
        for j in range(row_size):
            color = random_generator.choice(colors or [BLUE_C, TEAL, GREY_B, GOLD_C])
            person = get_person(color, expression=random_generator.choice(expressions), height=height * scale)
            x = -width / 2 + width * (j + 0.5 + (0.5 if row_index % 2 else 0)) / (row_size + 0.5)
            person.move_to([x, (row_count - 1 - row_index) * height * 0.55, 0], aligned_edge=DOWN)
            people.append(person)
    return VGroup(*people[::-1]) if row_count > 1 else VGroup(*people)
