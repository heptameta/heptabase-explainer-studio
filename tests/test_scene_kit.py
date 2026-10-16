"""scene_kit without rendering: the automatic layout checks on synthetic frames (a stand-in scene holds the
mobjects), components whose structure the checks and scene code rely on, and the ManimGL patches."""

from __future__ import annotations

import subprocess
import sys
import textwrap
from types import SimpleNamespace

import pytest


@pytest.fixture(scope="module")
def kit():
    saved_argv = sys.argv
    sys.argv = ["manimgl"]  # ManimGL parses the command line when it is first imported
    try:
        import manimlib

        from explainer_studio import scene_kit
        from explainer_studio.scene_kit import layout_checks
    finally:
        sys.argv = saved_argv
    return SimpleNamespace(manimlib=manimlib, layout_checks=layout_checks, scene_kit=scene_kit)


def run_automatic_checks_on_mobjects(kit, *mobjects):
    frame = kit.manimlib.ScreenRectangle(height=8)
    scene = SimpleNamespace(frame=frame, mobjects=[frame, *mobjects])
    problems, metrics = kit.layout_checks.run_automatic_checks(scene)
    return {check_name for check_name, _ in problems}, problems, metrics


def test_overlapping_text_is_reported_and_separated_text_is_not(kit):
    manimlib = kit.manimlib
    first_text = manimlib.Text("水壩", font_size=48)
    second_text = manimlib.Text("水車", font_size=48).shift(0.1 * manimlib.RIGHT)
    check_names, problems, _ = run_automatic_checks_on_mobjects(kit, first_text, second_text)
    assert "text_overlap" in check_names
    assert any("水壩" in detail and "水車" in detail for _, detail in problems)
    distant_text = manimlib.Text("水車", font_size=48).shift(3 * manimlib.DOWN)
    check_names, _, _ = run_automatic_checks_on_mobjects(kit, first_text, distant_text)
    assert "text_overlap" not in check_names


def test_small_text_unless_decorative_and_text_off_the_frame(kit):
    manimlib = kit.manimlib
    tiny = manimlib.Text("註腳", font_size=48).scale(0.25)
    off_frame_text = manimlib.Text("出界", font_size=48).move_to(7.5 * manimlib.RIGHT)
    check_names, _, metrics = run_automatic_checks_on_mobjects(kit, tiny, off_frame_text)
    assert {"text_too_small", "text_outside_frame"} <= check_names
    assert metrics["min_font_size"] == pytest.approx(12, abs=0.5)
    assert metrics["edge_distance"] < 0
    assert "text_too_small" not in run_automatic_checks_on_mobjects(kit, kit.layout_checks.mark_decorative(tiny))[0]


def test_part_outside_its_container(kit):
    manimlib = kit.manimlib
    cell = manimlib.Circle(radius=2)
    inside, outside = manimlib.Dot(0.5 * manimlib.RIGHT), manimlib.Dot(2.5 * manimlib.RIGHT)
    kit.layout_checks.keep_inside(cell, inside, outside)
    _, problems, _ = run_automatic_checks_on_mobjects(kit, cell, inside, outside)
    assert [check_name for check_name, _ in problems] == ["outside_container"]


@pytest.mark.render  # Tex runs LaTeX
def test_brace_counts_as_a_line_not_as_text(kit):
    manimlib = kit.manimlib
    formula = manimlib.Tex("x^2 + y^2", font_size=72)
    brace = manimlib.Brace(formula, manimlib.UP, buff=0)
    assert "text_overlap" not in run_automatic_checks_on_mobjects(kit, formula, brace)[0]


def test_surfaces_are_checked_like_any_picture(kit):
    manimlib = kit.manimlib
    sphere, title = manimlib.Sphere(radius=1.5), manimlib.Text("球面", font_size=48).to_edge(manimlib.UP)
    wave = manimlib.ParametricSurface(lambda u, v: [u, v, 0.3 * u * v], u_range=(-1, 1), v_range=(-1, 1))
    check_names, _, _ = run_automatic_checks_on_mobjects(kit, sphere, wave.shift(3 * manimlib.RIGHT), title)
    assert check_names == set()


def test_code_panel_has_one_line_per_source_line_whatever_the_glyphs(kit):
    ligatures = "def ready(a: int) -> bool:\n    return a // 2 != 3 and a >= 1"  # JetBrains Mono joins -> // != >=
    accent = "name = 'Jose\u0301'\n    total = a -> b"  # a combining accent: two characters, one glyph
    for code in (ligatures, accent):
        source_lines = code.split("\n")
        panel = kit.scene_kit.get_code_panel(code)
        assert [line.text for line in panel.lines] == [line.strip() for line in source_lines]
        first, second = panel.lines
        assert first.get_bottom()[1] > second.get_top()[1] - 0.1  # in order, one above the other
        assert second.get_left()[0] > first.get_left()[0]  # the indentation is kept
        if code is ligatures:
            glyph_counts = [len("".join(source_line.split())) for source_line in source_lines]
            assert [len(line.submobjects) for line in panel.lines] == glyph_counts


def test_text_in_the_code_font_has_one_glyph_per_letter_so_indexing_picks_the_letters_named(kit):
    address = "https://progress.org"  # JetBrains Mono joins "//" into one glyph through contextual alternates
    text = kit.manimlib.Text(address, font=kit.scene_kit.MONO_FONT)
    assert "calt=0" in text.get_content_prefix_and_suffix(False)[0]
    assert len(text.submobjects) == len(address)  # so text[8:10] is "pr", not "ro"
    own = kit.manimlib.Text(address, font=kit.scene_kit.MONO_FONT, global_config={"font_features": "liga=1"})
    assert "liga=1" in own.get_content_prefix_and_suffix(False)[0]  # a scene's own font_features are kept

def test_expanding_an_inset_keeps_marks_made_before_it(kit):
    manimlib = kit.manimlib
    title = manimlib.Text("能量藏在高低差裡", font_size=48).shift(2 * manimlib.UP)
    document = kit.scene_kit.get_document("論水壩", subtitle="一份手稿", width=2)  # its small print is a prop
    scene = SimpleNamespace(frame=manimlib.ScreenRectangle(height=8), add=lambda *a: None,
                            bring_to_back=lambda *a: None, play=lambda *a, **k: None, remove=lambda *a: None,
                            mobjects=[])
    meta_background, inset = kit.scene_kit.shrink_to_inset(scene, title, document)
    assert title._is_decorative  # a thumbnail while it is small
    kit.scene_kit.expand_from_inset(scene, meta_background, inset)
    assert not title._is_decorative
    assert run_automatic_checks_on_mobjects(kit, title, document)[0] == set()


def assert_same_points_as_manimgl(tmp_path, build_points_code: str) -> None:
    """In a fresh process (this one has the patches already), `build_points_code` (code defining build_points(),
    returning point arrays) gives the same points before and after scene_kit patches ManimGL. Points are float32:
    converting all samples at once may round the last digit differently."""
    script = textwrap.dedent(build_points_code) + textwrap.dedent("""
        before = build_points()
        import explainer_studio.scene_kit
        from manimlib import VMobject
        assert VMobject.add_points_as_corners.__module__ == "explainer_studio.scene_kit.patches"
        after = build_points()
        for i, (before_points, after_points) in enumerate(zip(before, after, strict=True)):
            is_same = (before_points.shape == after_points.shape
                       and np.allclose(before_points, after_points, rtol=0, atol=1e-6))
            assert is_same, (i, before_points.shape, after_points.shape)
        print("ok")
    """)
    result = subprocess.run([sys.executable, "-c", script], cwd=tmp_path, capture_output=True, text=True, timeout=300,
                            check=False)
    assert result.returncode == 0 and "ok" in result.stdout, (result.stdout + result.stderr)[-3000:]


def test_end_credits_list_the_named_files_in_order_or_every_credit_and_refuse_a_file_without_one(kit):
    from explainer_studio.schemas.credits import Credit

    def make_credit(path, title, author, license):
        return Credit(asset_file_path=path, title=title, author=author, license=license, source_url="https://example.org",
                      downloaded_at="2026-10-13T10:00:00+01:00")

    credits = [make_credit("shared/assets/a.png", "A file", "Ann", "CC BY 4.0"),
               make_credit("shared/assets/b.png", "B file", None, "Public domain")]
    resolve = kit.scene_kit.resolve_end_credits_entries
    named_entries = resolve(credits, {"shared/assets/b.png": "Bee", "shared/assets/a.png": ""})
    assert [(entry.name, entry.detail) for entry in named_entries] == [("Bee", "Public domain"),
                                                                       ("A file", "Ann · CC BY 4.0")]
    assert [entry.name for entry in resolve(credits, {})] == ["A file", "B file"]
    with pytest.raises(ValueError):
        resolve(credits, {"shared/assets/c.png": "Sea"})


def test_end_credits_page_lines_up_the_details_and_closes_with_the_icon_beside_its_name(kit):
    entries = [kit.scene_kit.EndCreditsEntry("Portrait of Isaac Newton", "Godfrey Kneller · Public domain"),
               kit.scene_kit.EndCreditsEntry("Euler", "Jakob Emanuel Handmann · Public domain")]
    _heading, body, closing = kit.scene_kit.get_end_credits_page(["A source, chapter 1"], entries)
    rows = body[1]
    assert rows[0].detail_part.get_left()[0] == pytest.approx(rows[1].detail_part.get_left()[0])
    assert rows[0].get_top()[1] > rows[1].get_top()[1]
    caption, (icon, name) = closing
    assert caption.get_bottom()[1] > icon.get_top()[1] and caption.get_x() == pytest.approx(closing[1].get_x())
    assert icon.get_right()[0] < name.get_left()[0] and name["H"].get_y() == pytest.approx(icon.get_y())
    assert body.get_bottom()[1] > caption.get_top()[1]
    assert len(kit.scene_kit.get_end_credits_page([], [])) == 1  # nothing to list: the closing alone


def test_curves_sampled_at_once_have_manimgl_s_points(tmp_path):
    assert_same_points_as_manimgl(tmp_path, """
        import sys

        import numpy as np
        from manimlib import Axes, ParametricCurve, VMobject

        def build_points():
            axes = Axes((-3, 3, 1), (0, 2, 1), width=8, height=4)
            call_dimensions = []

            def bell(x):
                call_dimensions.append(np.ndim(x))
                return np.exp(-x * x)

            point_arrays = [axes.get_graph(bell, x_range=(-3, 3, 0.02)).get_points(),
                            axes.get_graph(np.sin, x_range=(-3, 3, 0.1), discontinuities=[0.0]).get_points(),
                            ParametricCurve(lambda t: np.array([np.cos(t), np.sin(t), 0 * t]).T,
                                            t_range=(0, 6, 0.05)).get_points()]
            corners = VMobject(long_lines=True)
            corners.start_new_path(np.zeros(3))
            corners.add_points_as_corners(np.array([[1.0, 0, 0], [1, 1, 0], [0, 2, 0]]))
            point_arrays.append(corners.get_points())
            if "explainer_studio.scene_kit" in sys.modules:
                assert 1 in call_dimensions  # sampled with one array, not point by point
            return point_arrays
    """)


def test_curves_of_functions_that_cannot_take_an_array_fall_back_to_one_point_at_a_time(tmp_path):
    assert_same_points_as_manimgl(tmp_path, """
        import math
        import numpy as np
        from manimlib import Axes, ParametricCurve

        def build_points():
            axes = Axes((-3, 3, 1), (0, 2, 1), width=8, height=4)
            functions = [lambda x: math.exp(-x * x), lambda x: x if x > 0 else 0.0, lambda x: min(3 * x * x, 2.0)]
            point_arrays = [axes.get_graph(function, x_range=(-3, 3, 0.02)).get_points() for function in functions]
            circle = ParametricCurve(lambda t: np.array([math.cos(t), math.sin(t), 0]), t_range=(0, 6, 0.05))
            point_arrays.append(circle.get_points())
            return point_arrays
    """)
