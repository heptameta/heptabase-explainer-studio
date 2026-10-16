"""Fixes to the pinned ManimGL, applied once when scene_kit is imported.

- every render process gets a temporary directory of its own (Text writes <tmp>/<hash>.svg and deletes it, so two
  renders of the same text at once used to delete each other's file);
- LaTeX compiles in a private folder per process, never reuses a stale DVI, fails loudly, and caches the SVG by a
  hash of the full TeX source in the user cache directory;
- CJK glyph outlines no longer grow thin spikes;
- images are uploaded with mipmaps, so pictures shrunk far below their resolution do not sparkle;
- text objects remember their size at construction (also through Transform), for the text_too_small check;
- a curve's points are sampled and added all at once (every function graph, every frame of a redrawn one);
- text with ligatures off also has contextual alternates off, so a font such as JetBrains Mono never joins letters
  ("//") into one glyph and indexing the text picks the letters it names.

Each patched upstream function is checked against a hash of its source: a ManimGL upgrade that changes one stops
every render with a clear message instead of silently undoing a fix.

Some of the replacement functions are adapted from ManimGL (https://github.com/3b1b/manim), Copyright (c) 2020-2026
3Blue1Brown LLC, under the MIT License: licenses/ManimGL-LICENSE.txt.
"""

from __future__ import annotations

import atexit
import hashlib
import inspect
import os
import re
import shutil
import subprocess
import tempfile

import numpy as np
from manimlib import MarkupText, StringMobject, Transform, VMobject

from .. import user_dirs

tempfile.tempdir = tempfile.mkdtemp(prefix="explainer-studio-scene-")
atexit.register(shutil.rmtree, tempfile.tempdir, True)

# sha256 of inspect.getsource(original), first 16 hex digits, at ManimGL commit fafa083
_UPSTREAM_SOURCE_HASH_BY_NAME_MAP = {
    "tex_file_writing.full_tex_to_svg": "17aca70fa2339d72",
    "tex_file_writing.latex_to_svg": "221cd3511ff83491",  # not replaced, but the patch relies on it calling the above
    "VMobject.add_cubic_bezier_curve_to": "1cfa7916e62d2150",
    "VMobject.add_points_as_corners": "ccfa318b1b3dbb4f",
    "VMobject.add_line_to": "24ee568035a87acd",  # not replaced, but the patch appends what it would, all at once
    "ParametricCurve.init_points": "dd0c5e0bdcba09e4",
    "CoordinateSystem.get_graph": "3a73394f295174e7",
    "Gpu.texture": "f946a5946aaf17cd",
    "Gpu.sampler": "0b5c1036974964cf",
    "Animation.finish": "feb5415ae31d3f78",  # Transform.finish
    "StringMobject.__init__": "04f93c3bc37f6498",
    "Tex.__init__": "08c4eecb45d66d70",
    "TexTextFromPresetString.__init__": "2d946c424b43592e",
    "Title.__init__": "c16707a6b27f58e4",
    "Brace.__init__": "27bc49a3fb6e3b8e",
    "LineBrace.__init__": "b76a25097bbb349b",
    "MarkupText.__init__": "8c4d146a82f0c0c5",
    "Text.__init__": "6588b32cd8edf646",
    "Code.__init__": "2f92d95179e87175",
    "MarkupText.get_content_prefix_and_suffix": "cf3b3ece51c08b9a",
}


def _require_upstream_source(name: str, function) -> None:
    try:
        source_hash = hashlib.sha256(inspect.getsource(function).encode()).hexdigest()[:16]
    except (OSError, TypeError):
        source_hash = "no source"
    expected_hash = _UPSTREAM_SOURCE_HASH_BY_NAME_MAP[name]
    if source_hash != expected_hash:
        raise RuntimeError(f"ManimGL's {name} is not the version explainer_studio/scene_kit/patches.py was written "
                           f"against (source hash {source_hash}, expected {expected_hash}). Reinstall Explainer Studio "
                           "so the pinned ManimGL is used.")


def _install_safe_latex() -> None:
    """ManimGL compiles every formula in one shared working.tex and silently reuses the previous DVI when a compile
    fails; with renders running in parallel that drew wrong glyphs ("=" rendered as "60")."""
    import manimlib.utils.tex_file_writing as tex_writing

    if tex_writing.full_tex_to_svg.__module__.startswith("manimlib"):
        _require_upstream_source("tex_file_writing.full_tex_to_svg", tex_writing.full_tex_to_svg)
    _require_upstream_source("tex_file_writing.latex_to_svg", tex_writing.latex_to_svg)
    cache_dir_path = user_dirs.get_cache_dir_path() / "latex"
    cache_dir_path.mkdir(parents=True, exist_ok=True)
    work_dir_path = os.path.join(tempfile.gettempdir(), "latex")
    environment = user_dirs.compute_tool_environment()

    def full_tex_to_svg(full_tex: str, compiler: str = "latex", message: str = "") -> str:
        # The template loads tipa, which redefines \| ("Argument of \T3\| has an extra }"); \Vert is the same glyph.
        if "\\begin{document}" in full_tex:
            head, body = full_tex.split("\\begin{document}", 1)
            full_tex = head + "\\begin{document}" + re.sub(r"\\\|", r"\\Vert ", body)
        tex_hash = hashlib.sha256((compiler + "\0" + full_tex).encode("utf-8")).hexdigest()
        cached_svg_file_path = cache_dir_path / f"{tex_hash}.svg"
        if cached_svg_file_path.exists():
            return cached_svg_file_path.read_text(encoding="utf-8")
        os.makedirs(work_dir_path, exist_ok=True)
        tex_path = os.path.join(work_dir_path, "working.tex")
        dvi_path = os.path.splitext(tex_path)[0] + {"latex": ".dvi", "xelatex": ".xdv"}[compiler]
        if os.path.exists(dvi_path):
            os.unlink(dvi_path)
        with open(tex_path, "w", encoding="utf-8") as handle:
            handle.write(full_tex)
        process = subprocess.run(
            [compiler, *(["-no-pdf"] if compiler == "xelatex" else []), "-interaction=batchmode", "-halt-on-error",
             f"-output-directory={work_dir_path}", tex_path], capture_output=True, text=True, env=environment,
            check=False)
        if process.returncode != 0 or not os.path.exists(dvi_path):
            log_path = os.path.splitext(tex_path)[0] + ".log"
            error_message = ""
            if os.path.exists(log_path):
                with open(log_path, encoding="utf-8", errors="ignore") as handle:
                    match = re.search(r"(?<=\n! ).*\n.*\n", handle.read())
                error_message = match.group().strip() if match else ""
            snippet = full_tex.split("\\begin{document}")[-1].replace("\\end{document}", "").strip()[:300]
            raise tex_writing.LatexError(f"{error_message or 'LaTeX compilation failed'} while compiling: {snippet}")
        result = subprocess.run(["dvisvgm", dvi_path, "-n", "-v", "0", "--stdout"], capture_output=True,
                                env=environment, check=False)
        svg = result.stdout.decode("utf-8")
        if not svg.strip():
            raise tex_writing.LatexError("dvisvgm produced no output")
        temporary_file_path = cached_svg_file_path.with_suffix(f".{os.getpid()}.tmp")
        temporary_file_path.write_text(svg, encoding="utf-8")
        temporary_file_path.replace(cached_svg_file_path)
        return svg

    tex_writing.full_tex_to_svg = full_tex_to_svg
    tex_writing.latex_to_svg.cache_clear()


def _install_glyph_repair() -> None:
    """ManimGL turns each cubic of a font outline into one quadratic whose handle is the intersection of the end
    tangents; with nearly parallel tangents it lands far away and draws a spike across glyphs such as 歸, 變, 關.
    When the handle leaves the box of the cubic's control points, use the accurate two-quadratic approximation."""
    import manimlib.mobject.types.vectorized_mobject as vectorized
    from manimlib.utils.bezier import get_quadratic_approximation_of_cubic
    from manimlib.utils.space_ops import find_intersection

    if getattr(VMobject.add_cubic_bezier_curve_to, "_is_glyph_repair_patch", False):
        return
    _require_upstream_source("VMobject.add_cubic_bezier_curve_to", VMobject.add_cubic_bezier_curve_to)

    def add_cubic_bezier_curve_to(self, handle1, handle2, anchor):
        self.throw_error_if_no_points()
        last_point = self.get_last_point()
        control_points = np.array([last_point, handle1, handle2, anchor])
        min_corner, max_corner = control_points.min(axis=0), control_points.max(axis=0)
        padding = 0.1 * np.max(max_corner - min_corner) + 1e-9
        quadratic_points = None
        if self.use_simple_quadratic_approx:
            handle = find_intersection(last_point, handle1 - last_point, anchor, handle2 - anchor)
            if (np.all(np.isfinite(handle)) and np.all(handle >= min_corner - padding)
                    and np.all(handle <= max_corner + padding)):
                quadratic_points = np.array([last_point, handle, anchor])
        if quadratic_points is None:
            quadratic_points = get_quadratic_approximation_of_cubic(last_point, handle1, handle2, anchor)
            if self.consider_points_equal(quadratic_points[3], quadratic_points[4]):
                quadratic_points[3] = vectorized.midpoint(*quadratic_points[2:4])
        if self.consider_points_equal(quadratic_points[1], last_point):
            quadratic_points[1] = vectorized.midpoint(*quadratic_points[1:3])
        self.append_points(quadratic_points[1:])
        return self

    add_cubic_bezier_curve_to._is_glyph_repair_patch = True
    VMobject.add_cubic_bezier_curve_to = add_cubic_bezier_curve_to


def _enable_image_mipmaps() -> None:
    try:
        import wgpu
        from manimlib.renderer import gpu
        from manimlib.renderer.texture import FILTER_MODES, check_texture_filter
        from PIL import Image
    except ImportError:
        return
    if getattr(gpu.Gpu, "_has_mipmap_patch", False):
        return
    _require_upstream_source("Gpu.texture", gpu.Gpu.texture)
    _require_upstream_source("Gpu.sampler", gpu.Gpu.sampler)

    def texture(self, path: str):
        if path not in self.textures:
            image = Image.open(path).convert("RGBA")
            mip_levels = [image]
            while max(mip_levels[-1].size) > 1:
                width, height = mip_levels[-1].size
                mip_levels.append(mip_levels[-1].resize((max(1, width // 2), max(1, height // 2)), Image.LANCZOS))
            uploaded_texture = self.device.create_texture(
                size=(image.width, image.height, 1), format=wgpu.TextureFormat.rgba8unorm,
                usage=wgpu.TextureUsage.TEXTURE_BINDING | wgpu.TextureUsage.COPY_DST, mip_level_count=len(mip_levels))
            for level_index, picture in enumerate(mip_levels):
                self.queue.write_texture({"texture": uploaded_texture, "mip_level": level_index, "origin": (0, 0, 0)},
                                         np.asarray(picture, dtype=np.uint8),
                                         {"offset": 0, "bytes_per_row": 4 * picture.width,
                                          "rows_per_image": picture.height},
                                         (picture.width, picture.height, 1))
            self.textures[path] = uploaded_texture
        return self.textures[path]

    def sampler(self, texture_filter: str = "linear"):
        sampler_key = ("mip", texture_filter)
        if sampler_key not in self.samplers:
            filter_mode = FILTER_MODES[check_texture_filter(texture_filter)]
            self.samplers[sampler_key] = self.device.create_sampler(mag_filter=filter_mode, min_filter=filter_mode,
                                                                    mipmap_filter=filter_mode)
        return self.samplers[sampler_key]

    gpu.Gpu.texture, gpu.Gpu.sampler, gpu.Gpu._has_mipmap_patch = texture, sampler, True


def _record_base_size(cls) -> None:
    """Every text object remembers its size right after construction, before any scaling in the scene."""
    for subclass in [cls, *cls.__subclasses__()]:
        if "__init__" in subclass.__dict__ and not getattr(subclass.__init__, "_is_size_patch", False):
            original_init = subclass.__init__
            is_upstream = subclass.__module__.startswith("manimlib")
            if f"{subclass.__name__}.__init__" in _UPSTREAM_SOURCE_HASH_BY_NAME_MAP and is_upstream:
                _require_upstream_source(f"{subclass.__name__}.__init__", original_init)

            def init(self, *args, _original=original_init, **kwargs):
                _original(self, *args, **kwargs)
                self._base_size = (self.get_width(), self.get_height())

            init._is_size_patch = True
            subclass.__init__ = init
        if subclass is not cls:
            _record_base_size(subclass)


def _carry_size_through_transform() -> None:
    """After a Transform the moving object has the target's shapes, so it takes the target's size record too."""
    if getattr(Transform.finish, "_is_size_patch", False):
        return
    _require_upstream_source("Animation.finish", Transform.finish)
    original_finish = Transform.finish

    def finish(self):
        original_finish(self)
        target = getattr(self, "target_copy", None)
        if target is None:
            return
        for mobject, target_member in zip(self.mobject.get_family(), target.get_family()):
            is_text = isinstance(mobject, StringMobject) or hasattr(mobject, "_base_size")
            if hasattr(target_member, "_base_size") and is_text:
                mobject._base_size = target_member._base_size
                mobject.font_size = getattr(target_member, "font_size", None)
            elif hasattr(mobject, "_base_size") and not isinstance(mobject, StringMobject):
                del mobject._base_size

    finish._is_size_patch = True
    Transform.finish = finish


def _add_corners_at_once() -> None:
    """ParametricCurve (every axes.get_graph) adds its samples one by one through add_line_to, and each call
    reallocates the whole point array: n samples cost n reallocations of a growing array. A bell curve redrawn every
    frame (always_redraw) took 0.37 s a frame, and one scene 450 s to render. Append the same points in one step."""
    if getattr(VMobject.add_points_as_corners, "_is_all_at_once_patch", False):
        return
    _require_upstream_source("VMobject.add_points_as_corners", VMobject.add_points_as_corners)
    _require_upstream_source("VMobject.add_line_to", VMobject.add_line_to)

    def add_points_as_corners(self, points):
        corners = np.array(points if isinstance(points, np.ndarray) else list(points), dtype=float)
        if len(corners) == 0:
            return self
        self.throw_error_if_no_points()
        starts = np.vstack([self.get_last_point()[None, :], corners[:-1]])
        alphas = np.linspace(0, 1, 5 if self.long_lines else 3)[1:]  # as add_line_to
        lines = starts[:, None, :] * (1 - alphas)[None, :, None] + corners[:, None, :] * alphas[None, :, None]
        self.append_points(lines.reshape(-1, corners.shape[1]))
        return self

    add_points_as_corners._is_all_at_once_patch = True
    VMobject.add_points_as_corners = add_points_as_corners


def _evaluate_parametric_function(t_func, ts: np.ndarray) -> np.ndarray:
    """t_func at every t: in one call when it takes an array (checked against single calls at five of them), else one
    by one (a function with an if, math.exp, max ...)."""
    try:
        with np.errstate(all="ignore"):
            points = np.array(t_func(ts), dtype=float)
    except Exception:  # noqa: BLE001 - whatever fails on an array is evaluated one by one, as ManimGL does
        points = None
    if points is not None and points.shape == (len(ts), 3):
        check_indices = np.unique(np.linspace(0, len(ts) - 1, 5).astype(int))
        single_points = [np.array(t_func(ts[i]), dtype=float) for i in check_indices]
        if np.allclose(points[check_indices], single_points, equal_nan=True):
            return points
    return np.array([t_func(t) for t in ts])


def _evaluate_function(function, xs: np.ndarray) -> np.ndarray:
    """function at every x: in one call when it takes an array, else one by one. Either way the conversion to frame
    points, which is what costs, is then done for all of them at once."""
    try:
        with np.errstate(all="ignore"):
            ys = np.array(function(xs), dtype=float)
    except Exception:  # noqa: BLE001 - as in _evaluate_parametric_function
        ys = None
    return ys if ys is not None and ys.shape == xs.shape else np.array([function(x) for x in xs], dtype=float)


def _sample_curves_at_once() -> None:
    """ParametricCurve evaluates its function and converts it to a frame point one t at a time; get_graph's function
    is converted through the axes once per sample. Sample all t at once where the function allows it."""
    from manimlib.mobject.coordinate_systems import CoordinateSystem
    from manimlib.mobject.functions import ParametricCurve

    if getattr(ParametricCurve.init_points, "_is_all_at_once_patch", False):
        return
    _require_upstream_source("ParametricCurve.init_points", ParametricCurve.init_points)
    _require_upstream_source("CoordinateSystem.get_graph", CoordinateSystem.get_graph)

    def init_points(self):
        t_min, t_max, step = self.t_range
        jumps = np.array(self.discontinuities)
        jumps = jumps[(jumps > t_min) & (jumps < t_max)]
        boundary_times = sorted([t_min, t_max, *(jumps - self.epsilon), *(jumps + self.epsilon)])
        for t1, t2 in zip(boundary_times[0::2], boundary_times[1::2], strict=True):
            points = _evaluate_parametric_function(self.t_func, np.array([*np.arange(t1, t2, step), t2]))
            self.start_new_path(points[0])
            self.add_points_as_corners(points[1:])
        if self.use_smoothing:
            self.make_smooth(approx=True)
        if not self.has_points():
            self.set_points(np.array([self.t_func(t_min)]))
        return self

    def get_graph(self, function, x_range=None, bind=False, **kwargs):
        x_range = x_range or self.x_range
        t_range = np.ones(3)
        t_range[:len(x_range)] = x_range
        t_range[2] /= self.num_sampled_graph_points_per_tick  # for functions, the sample frequency

        def parametric_function(t):
            return self.c2p(t, function(t) if np.ndim(t) == 0 else _evaluate_function(function, t))

        graph = ParametricCurve(parametric_function, t_range=tuple(t_range), **kwargs)
        graph.underlying_function = function
        graph.x_range = x_range
        if bind:
            self.bind_graph_to_func(graph, function)
        return graph

    init_points._is_all_at_once_patch = True
    ParametricCurve.init_points, CoordinateSystem.get_graph = init_points, get_graph


# Every OpenType feature that can join or swap letters: with them all off, each character is its own glyph.
NO_JOINED_LETTERS_FONT_FEATURES = "liga=0,dlig=0,clig=0,hlig=0,calt=0"


def _keep_letters_apart() -> None:
    """ManimGL turns ligatures off by default but leaves contextual alternates on, and some fonts join letters through
    them: JetBrains Mono, the video's code font, draws "//" as one glyph, so in "https://..." every letter after it sits
    one place earlier and `text[8:10]` picks the wrong two. Text with ligatures off gets contextual alternates off too,
    unless the scene gives its own font_features."""
    original = MarkupText.get_content_prefix_and_suffix
    if getattr(original, "_is_letters_apart_patch", False):
        return
    _require_upstream_source("MarkupText.get_content_prefix_and_suffix", original)

    def get_content_prefix_and_suffix(self, is_labelled: bool) -> tuple[str, str]:
        if not self.disable_ligatures or "font_features" in self.global_config:
            return original(self, is_labelled)
        given_config = self.global_config
        self.global_config = {**given_config, "font_features": NO_JOINED_LETTERS_FONT_FEATURES}
        try:
            return original(self, is_labelled)
        finally:
            self.global_config = given_config

    get_content_prefix_and_suffix._is_letters_apart_patch = True
    MarkupText.get_content_prefix_and_suffix = get_content_prefix_and_suffix


_install_safe_latex()
_install_glyph_repair()
_enable_image_mipmaps()
_record_base_size(StringMobject)
_carry_size_through_transform()
_add_corners_at_once()
_sample_curves_at_once()
_keep_letters_apart()
