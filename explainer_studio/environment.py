"""The environment outside Python: what `doctor` checks and what `setup` installs.

Everything is installed per user, without a password, and is safe to install again: ffmpeg and ffprobe, TeX with the
packages formulas need, the Noto Sans TC and JetBrains Mono fonts, Natural Earth map data, and on request Blender and
Playwright's Chromium. A program that is already on the computer and good enough is used instead of a second copy.
`doctor` and `setup` share the checks below, so they never disagree about what is missing.
"""

from __future__ import annotations

import gzip
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from . import user_dirs
from .errors import StudioError

ProgressReporter = Callable[[str], None]


@dataclass
class Check:
    name: str
    is_ok: bool
    detail: str
    fix: str = ""
    is_required: bool = True  # False: optional, or only needed for some videos


def get_operating_system() -> str:
    return {"darwin": "macos", "win32": "windows"}.get(sys.platform, "linux")


def get_architecture() -> str:
    return "arm64" if platform.machine().lower() in ("arm64", "aarch64") else "x64"


def _run(command: list[str], timeout_seconds: float = 60, **kwargs) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace",
                              timeout=timeout_seconds, check=False, env=user_dirs.compute_tool_environment(),
                              **kwargs)
    except (OSError, subprocess.TimeoutExpired) as error:
        return subprocess.CompletedProcess(command, 1, "", str(error))


def _run_python(code: str, timeout_seconds: float, cwd: str | None = None) -> subprocess.CompletedProcess:
    """Run code in this CLI's own Python, so a crash or hang in a probe cannot take the command down."""
    return _run([sys.executable, "-c", code], timeout_seconds=timeout_seconds, cwd=cwd)


def _replace_dir(source: Path, target: Path) -> None:
    if target.exists():
        shutil.rmtree(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(target))


def _find_unpacked_root(unpacked_dir_path: Path) -> Path:
    children = [path for path in unpacked_dir_path.iterdir() if not path.name.startswith(".")]
    return children[0] if len(children) == 1 and children[0].is_dir() else unpacked_dir_path


def _download(url: str, target_file_path: Path, report_progress: ProgressReporter, label: str,
              expected_sha256: str | None = None) -> Path:
    from .assets.fetch import download

    return download(url, target_file_path, report_progress, label, timeout_seconds=300,
                    expected_sha256=expected_sha256)


# ManimGL and the GPU ------------------------------------------------------------------------------------------------
GPU_PROBE = """
import json
from importlib.metadata import version
import manimlib  # noqa: F401
import wgpu
adapter = wgpu.gpu.request_adapter_sync(power_preference="high-performance")
adapter.request_device_sync()
print(json.dumps({"manimgl": version("manimgl"), "gpu": adapter.summary, "type": adapter.info["adapter_type"]}))
"""


def _format_gpu_fix() -> str:
    if get_operating_system() == "linux":
        return ("ManimGL draws with WebGPU, which needs a Vulkan or EGL driver. Install Mesa's drivers (Debian/Ubuntu: "
                "`sudo apt install mesa-vulkan-drivers libegl1`; Fedora: `sudo dnf install mesa-vulkan-drivers "
                "mesa-libEGL`); without a GPU, Mesa's lavapipe renders on the CPU. Rendering to files needs no "
                "display, so xvfb is not required")
    if get_operating_system() == "windows":
        return "update the graphics driver (ManimGL draws with WebGPU through Direct3D 12 or Vulkan)"
    return "ManimGL draws with WebGPU through Metal, which needs macOS 11 or later"


def check_manimgl() -> Check:
    # run outside the current folder: ManimGL reads a custom_config.yml from wherever it starts
    probe_result = _run_python(GPU_PROBE, timeout_seconds=180, cwd=tempfile.gettempdir())
    lines = probe_result.stdout.strip().splitlines()
    if probe_result.returncode != 0 or not lines:
        error = (probe_result.stderr.strip().splitlines() or ["no output"])[-1][:300]
        if "manimlib" in error or "No module named" in error:
            return Check("manimgl", False, error, "run the skill's install script again (it reinstalls ManimGL)")
        return Check("manimgl", False, f"no GPU adapter: {error}", _format_gpu_fix())
    probe_output = json.loads(lines[-1])
    detail = f"ManimGL {probe_output['manimgl']}, {probe_output['gpu']}"
    if probe_output.get("type") == "CPU":
        return Check("manimgl", True, detail + " (software rendering: slow)", _format_gpu_fix())
    return Check("manimgl", True, detail)


# ffmpeg -------------------------------------------------------------------------------------------------------------
# Static builds of one pinned release for every platform (github.com/eugeneware/ffmpeg-static). They are run, so each
# file must match the SHA-256 GitHub lists for that release's asset; a new release changes both together.
FFMPEG_RELEASE = "b6.1.1"
FFMPEG_URL = "https://github.com/eugeneware/ffmpeg-static/releases/download/{release}/{tool}-{platform}.gz"
FFMPEG_SHA256_BY_FILE_NAME_MAP = {
    "ffmpeg-darwin-arm64.gz": "8923876afa8db5585022d7860ec7e589af192f441c56793971276d450ed3bbfa",
    "ffmpeg-darwin-x64.gz": "929b375c1182d956c51f7ac25e0b2b0411fb01f6f407aa15c9758efeb4242106",
    "ffmpeg-linux-arm64.gz": "754a678672298bc68156adff58aa7385a592c2b30b1d0ae8750c45c915c4bac0",
    "ffmpeg-linux-x64.gz": "bfe8a8fc511530457b528c48d77b5737527b504a3797a9bc4866aeca69c2dffa",
    "ffmpeg-win32-x64.gz": "8883a3dffbd0a16cf4ef95206ea05283f78908dbfb118f73c83f4951dcc06d77",
    "ffprobe-darwin-arm64.gz": "d986a8ec7b030899fe66a8a288ed809a3543338705a3ce178cfb85869c5d80be",
    "ffprobe-darwin-x64.gz": "d4da574d6e2e197bd259b47d69cf262df9e312af24ad960444f6d806d3d4c186",
    "ffprobe-linux-arm64.gz": "2ab6aba60ee84412dff9188720703376cb4e7aaf7e0b5e43aa8249f2acae5bf8",
    "ffprobe-linux-x64.gz": "25d9b6ccb05e3d9de9e04e31e2506d8dd7f9f0418981965ac6df12e8d3afd067",
    "ffprobe-win32-x64.gz": "f309e6223ad89d2fe54bccd420a7709b66fd27540674e92309578ed491a43c8d",
}


def _resolve_ffmpeg_platform() -> str | None:
    return {("macos", "arm64"): "darwin-arm64", ("macos", "x64"): "darwin-x64", ("linux", "x64"): "linux-x64",
            ("linux", "arm64"): "linux-arm64",
            ("windows", "x64"): "win32-x64"}.get((get_operating_system(), get_architecture()))


def _inspect_ffmpeg_tool(tool: str) -> tuple[str | None, str]:
    """(path, problem); problem is empty when the tool is usable."""
    path = user_dirs.find_tool(tool)
    if path is None:
        return None, "not found"
    version_result = _run([path, "-hide_banner", "-version"], timeout_seconds=30)
    if version_result.returncode != 0:
        return path, f"{path} does not run"
    if tool == "ffmpeg":
        encoder_list = _run([path, "-hide_banner", "-encoders"], timeout_seconds=30).stdout
        missing_encoders = [encoder for encoder in ("libx264", "aac") if f" {encoder} " not in encoder_list]
        if missing_encoders:
            return path, f"{path} lacks the {', '.join(missing_encoders)} encoder(s)"
    return path, ""


def _read_ffmpeg_version(path: str) -> str:
    first_line = _run([path, "-hide_banner", "-version"], timeout_seconds=30).stdout.split("\n")[0]
    match = re.search(r"version (\S+)", first_line)
    return match.group(1) if match else "unknown version"


def check_ffmpeg() -> list[Check]:
    checks = []
    for tool in ("ffmpeg", "ffprobe"):
        path, problem = _inspect_ffmpeg_tool(tool)
        if problem:
            checks.append(Check(tool, False, problem, "run `explainer-studio setup`"))
        else:
            checks.append(Check(tool, True, f"{path} ({_read_ffmpeg_version(path)})"))
    return checks


def ensure_ffmpeg(report_progress: ProgressReporter) -> str:
    path_and_problem_by_tool_map = {tool: _inspect_ffmpeg_tool(tool) for tool in ("ffmpeg", "ffprobe")}
    if not any(problem for _, problem in path_and_problem_by_tool_map.values()):
        return f"ffmpeg: using {path_and_problem_by_tool_map['ffmpeg'][0]}"
    ffmpeg_platform = _resolve_ffmpeg_platform()
    if ffmpeg_platform is None:
        raise StudioError(f"no ffmpeg build for {get_operating_system()} {get_architecture()}",
                          "the static builds cover macOS, Linux (x64, arm64) and Windows x64",
                          "install ffmpeg with the system's package manager")
    ffmpeg_dir_path = user_dirs.get_data_dir_path() / "ffmpeg"
    suffix = ".exe" if get_operating_system() == "windows" else ""
    for tool in ("ffmpeg", "ffprobe"):
        report_progress(f"downloading {tool} {FFMPEG_RELEASE} for {ffmpeg_platform}")
        with tempfile.TemporaryDirectory() as temporary_dir_path:
            ffmpeg_url = FFMPEG_URL.format(release=FFMPEG_RELEASE, tool=tool, platform=ffmpeg_platform)
            archive_file_path = _download(ffmpeg_url, Path(temporary_dir_path) / f"{tool}.gz", report_progress, tool,
                                          FFMPEG_SHA256_BY_FILE_NAME_MAP[f"{tool}-{ffmpeg_platform}.gz"])
            binary_file_path = ffmpeg_dir_path / f"{tool}{suffix}"
            ffmpeg_dir_path.mkdir(parents=True, exist_ok=True)
            partial_file_path = binary_file_path.with_name(binary_file_path.name + ".part")
            with gzip.open(archive_file_path, "rb") as source, partial_file_path.open("wb") as output_file:
                shutil.copyfileobj(source, output_file)
            partial_file_path.chmod(0o755)
            os.replace(partial_file_path, binary_file_path)
    path, problem = _inspect_ffmpeg_tool("ffmpeg")
    if problem:
        raise StudioError("the downloaded ffmpeg does not work", problem, "install ffmpeg with the system's package "
                          "manager, then run `explainer-studio setup` again")
    return f"ffmpeg: installed {path}"


# TeX ----------------------------------------------------------------------------------------------------------------
# tlmgr package -> a file kpsewhich finds when it is installed. The list covers ManimGL's default template and the
# ctex template scene_kit uses for Chinese in formulas.
TEX_FILE_NAME_BY_PACKAGE_MAP = {
    "ctex": "ctex.sty", "xecjk": "xeCJK.sty", "standalone": "standalone.cls", "preview": "preview.sty",
    "doublestroke": "dsfont.sty", "relsize": "relsize.sty", "fundus-calligra": "calligra.sty",
    "wasysym": "wasysym.sty", "wasy": "wasy10.tfm", "physics": "physics.sty", "mathastext": "mathastext.sty",
    "setspace": "setspace.sty", "tipa": "tipa.sty", "rsfs": "rsfs10.tfm", "jknapltx": "mathrsfs.sty",
    "cm-unicode": "cmunrm.otf", "ragged2e": "ragged2e.sty",
    "babel-english": "english.ldf", "microtype": "microtype.sty", "psnfss": "pifont.sty", "xcolor": "xcolor.sty",
    "amsfonts": "amssymb.sty", "fontspec": "fontspec.sty",
}
TEX_PROGRAM_BY_PACKAGE_MAP = {"xetex": "xelatex", "latex-bin": "latex", "dvisvgm": "dvisvgm"}
# fonts only a few formulas use (the calligra font): installed into TinyTeX, but a system TeX without them is still used
TINYTEX_EXTRA_PACKAGES = ("calligra",)
# The daily bundle, neither pinned nor checked against a SHA-256: setup always installs packages with tlmgr, and a
# TinyTeX from an earlier TeX Live year cannot install from CTAN once the next year's TeX Live is out.
TINYTEX_URL = "https://github.com/rstudio/tinytex-releases/releases/download/daily/{bundle}"


def _resolve_tex_packages() -> dict[str, str]:
    # ctex's default font set on Linux is Fandol; macOS and Windows use system fonts
    if get_operating_system() == "linux":
        return {**TEX_FILE_NAME_BY_PACKAGE_MAP, "fandol": "FandolSong-Regular.otf"}
    return TEX_FILE_NAME_BY_PACKAGE_MAP


def inspect_tex() -> tuple[str | None, list[str]]:
    """(the xelatex in use or None, tlmgr packages missing from that TeX)."""
    xelatex = user_dirs.find_tool("xelatex")
    kpsewhich = user_dirs.find_tool("kpsewhich")
    if xelatex is None or kpsewhich is None:
        return None, sorted(_resolve_tex_packages())
    missing_packages = [package for package, program in TEX_PROGRAM_BY_PACKAGE_MAP.items()
                        if user_dirs.find_tool(program) is None]
    tex_file_name_by_package_map = _resolve_tex_packages()
    kpsewhich_lines = _run([kpsewhich, *tex_file_name_by_package_map.values()], timeout_seconds=60).stdout.splitlines()
    found_file_names = {Path(line.strip()).name for line in kpsewhich_lines}
    missing_packages += [package for package, file_name in tex_file_name_by_package_map.items()
                         if file_name not in found_file_names]
    return xelatex, missing_packages


def _check_is_in_tinytex(path: str) -> bool:
    return Path(path).resolve().is_relative_to(user_dirs.get_tinytex_dir_path().resolve())


def check_tex() -> Check:
    xelatex, missing = inspect_tex()
    if xelatex is None:
        return Check("latex", False, "no xelatex found", "run `explainer-studio setup` (it installs TinyTeX)")
    if missing:
        return Check("latex", False, f"{xelatex} lacks {', '.join(missing)}", "run `explainer-studio setup`")
    return Check("latex", True, f"{xelatex} with ctex and the formula packages")


def _resolve_tinytex_bundle_name() -> str:
    if get_operating_system() == "macos":
        return "TinyTeX-1-darwin.tar.xz"
    if get_operating_system() == "windows":
        return "TinyTeX-1-windows.exe"
    return f"TinyTeX-1-linux-{'arm64' if get_architecture() == 'arm64' else 'x86_64'}.tar.xz"


def _find_tlmgr() -> str:
    bin_dir_paths = sorted((user_dirs.get_tinytex_dir_path() / "bin").glob("*"))
    if not bin_dir_paths:
        raise StudioError("TinyTeX has no bin folder", f"looked in {user_dirs.get_tinytex_dir_path()}",
                          "delete that folder and run `explainer-studio setup` again")
    return str(bin_dir_paths[0] / ("tlmgr.bat" if get_operating_system() == "windows" else "tlmgr"))


def install_tinytex(report_progress: ProgressReporter) -> None:
    if get_operating_system() != "windows" and shutil.which("perl") is None:
        raise StudioError("TinyTeX needs Perl", "tlmgr, TeX's package manager, is a Perl program",
                          "install perl with the system's package manager, then run `explainer-studio setup` again")
    tinytex_dir_path = user_dirs.get_tinytex_dir_path()
    bundle_name = _resolve_tinytex_bundle_name()
    report_progress(f"installing TinyTeX into {tinytex_dir_path} (about 100 MB)")
    with tempfile.TemporaryDirectory() as temporary_dir_path:
        archive_file_path = _download(TINYTEX_URL.format(bundle=bundle_name), Path(temporary_dir_path) / bundle_name,
                                      report_progress, "TinyTeX")
        unpacked_dir_path = Path(temporary_dir_path) / "unpacked"
        unpacked_dir_path.mkdir()
        if bundle_name.endswith(".exe"):  # a self-extracting archive that unpacks a TinyTeX folder
            unpack_result = subprocess.run([str(archive_file_path), "-y"], cwd=unpacked_dir_path, capture_output=True,
                                           text=True, encoding="utf-8", errors="replace", check=False)
            if unpack_result.returncode != 0:
                raise StudioError("could not unpack TinyTeX", unpack_result.stderr.strip()[-300:], "run setup again")
        else:
            with tarfile.open(archive_file_path) as archive:
                archive.extractall(unpacked_dir_path, filter="tar")
        _replace_dir(_find_unpacked_root(unpacked_dir_path), tinytex_dir_path)
    tlmgr_path = _find_tlmgr()
    _run([tlmgr_path, "postaction", "install", "script", "xetex"], timeout_seconds=600)
    _run([tlmgr_path, "install", *TINYTEX_EXTRA_PACKAGES], timeout_seconds=600)


def ensure_tex(report_progress: ProgressReporter) -> str:
    xelatex, missing = inspect_tex()
    if xelatex and not missing:
        return f"LaTeX: using {xelatex}"
    if xelatex is None or not _check_is_in_tinytex(xelatex):
        # a system TeX without the packages cannot be extended without a password; TinyTeX goes first on our PATH
        if xelatex:
            report_progress(f"{xelatex} lacks {', '.join(missing)}; installing a user-level TinyTeX instead")
        install_tinytex(report_progress)
        xelatex, missing = inspect_tex()
    if missing:
        report_progress(f"installing TeX packages: {' '.join(missing)}")
        install_result = _run([_find_tlmgr(), "install", *missing], timeout_seconds=1800)
        xelatex, missing = inspect_tex()
        if missing:
            output_tail = (install_result.stdout + install_result.stderr).strip()[-400:]
            raise StudioError("some TeX packages did not install",
                              f"still missing: {', '.join(missing)}; {output_tail}",
                              "run `explainer-studio setup` again (tlmgr retries the download)")
    return f"LaTeX: TinyTeX with ctex and the formula packages at {user_dirs.get_tinytex_dir_path()}"


# Fonts --------------------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class FontFile:
    family: str
    file_name: str
    url: str


NOTO_SANS_TC_BASE_URL = "https://github.com/notofonts/noto-cjk/raw/Sans2.004/Sans/SubsetOTF/TC"
JETBRAINS_MONO_BASE_URL = "https://github.com/JetBrains/JetBrainsMono/raw/v2.304/fonts/ttf"
FONT_FILES = (  # both families are under the SIL Open Font License
    FontFile("Noto Sans TC", "NotoSansTC-Regular.otf", f"{NOTO_SANS_TC_BASE_URL}/NotoSansTC-Regular.otf"),
    FontFile("Noto Sans TC", "NotoSansTC-Bold.otf", f"{NOTO_SANS_TC_BASE_URL}/NotoSansTC-Bold.otf"),
    FontFile("JetBrains Mono", "JetBrainsMono-Regular.ttf", f"{JETBRAINS_MONO_BASE_URL}/JetBrainsMono-Regular.ttf"),
    FontFile("JetBrains Mono", "JetBrainsMono-Bold.ttf", f"{JETBRAINS_MONO_BASE_URL}/JetBrainsMono-Bold.ttf"),
)
FONT_FAMILIES = tuple(dict.fromkeys(font.family for font in FONT_FILES))


def get_user_font_dir_path() -> Path:
    if get_operating_system() == "macos":
        return Path.home() / "Library" / "Fonts"
    if get_operating_system() == "windows":
        local_app_data_dir_path = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
        return local_app_data_dir_path / "Microsoft" / "Windows" / "Fonts"
    return Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share") / "fonts"


def list_visible_font_families() -> set[str] | None:
    """The families ManimGL's text renderer (Pango) sees, or None when it cannot be asked."""
    probe_code = "import json, manimpango; print(json.dumps(sorted(set(manimpango.list_fonts()))))"
    probe_result = _run_python(probe_code, timeout_seconds=60)
    try:
        return set(json.loads(probe_result.stdout.strip().splitlines()[-1]))
    except (ValueError, IndexError):
        return None


def find_missing_font_families() -> list[str]:
    visible_families = list_visible_font_families()
    if visible_families is not None:
        return [family for family in FONT_FAMILIES if family not in visible_families]
    font_dir_path = get_user_font_dir_path()
    return sorted({font.family for font in FONT_FILES if not (font_dir_path / font.file_name).exists()})


def check_fonts() -> Check:
    missing = find_missing_font_families()
    if missing:
        return Check("fonts", False, f"missing {', '.join(missing)}", "run `explainer-studio setup`")
    return Check("fonts", True, ", ".join(FONT_FAMILIES))


def _register_windows_font(path: Path, family: str) -> None:
    """Per-user fonts on Windows need a registry entry to survive sign-out and AddFontResource to work now."""
    import ctypes
    import winreg

    style = "Bold" if "Bold" in path.stem else "Regular"
    kind = "OpenType" if path.suffix.lower() == ".otf" else "TrueType"
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows NT\CurrentVersion\Fonts") as key:
        winreg.SetValueEx(key, f"{family} {style} ({kind})", 0, winreg.REG_SZ, str(path))
    ctypes.windll.gdi32.AddFontResourceW(str(path))
    ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001D, 0, 0, 0x0002, 1000, None)  # WM_FONTCHANGE to all windows


def share_fonts_with_tinytex() -> int:
    """Copy the fonts into TinyTeX's own tree. TeX's font lookup does not search the per-user font folder on Windows
    (and has no system configuration on a bare Linux), so formulas could not use the fonts otherwise."""
    tinytex_dir_path = user_dirs.get_tinytex_dir_path()
    if not tinytex_dir_path.is_dir():
        return 0
    copied_count = 0
    for font in FONT_FILES:
        source_file_path = get_user_font_dir_path() / font.file_name
        font_kind = "opentype" if source_file_path.suffix.lower() == ".otf" else "truetype"
        target_file_path = (tinytex_dir_path / "texmf-dist" / "fonts" / font_kind / "public" / "explainer-studio"
                            / font.file_name)
        if source_file_path.is_file() and not target_file_path.exists():
            target_file_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source_file_path, target_file_path)
            copied_count += 1
    if copied_count:
        for tool in ("mktexlsr", "fc-cache"):
            path = user_dirs.find_tool(tool)
            if path and _check_is_in_tinytex(path):
                _run([path], timeout_seconds=600)
    return copied_count


def ensure_fonts(report_progress: ProgressReporter) -> str:
    missing_families = set(find_missing_font_families())
    font_dir_path = get_user_font_dir_path()
    for font in FONT_FILES:
        if font.family not in missing_families:
            continue
        font_file_path = font_dir_path / font.file_name
        if not font_file_path.exists():
            report_progress(f"downloading {font.file_name}")
            _download(font.url, font_file_path, report_progress, font.file_name)
        if get_operating_system() == "windows":
            _register_windows_font(font_file_path, font.family)
    if missing_families and get_operating_system() == "linux" and shutil.which("fc-cache"):
        _run(["fc-cache", "-f", str(font_dir_path)], timeout_seconds=300)
    shared_note = " (and in TinyTeX)" if share_fonts_with_tinytex() else ""
    if not missing_families:
        return f"fonts: {', '.join(FONT_FAMILIES)} already installed{shared_note}"
    return f"fonts: installed {', '.join(sorted(missing_families))} in {font_dir_path}{shared_note}"


# Map data -----------------------------------------------------------------------------------------------------------
GEO_FILE_NAMES = ("ne_110m_admin_0_countries", "ne_50m_admin_0_countries", "ne_110m_land",
             "ne_50m_rivers_lake_centerlines", "ne_50m_lakes", "ne_50m_populated_places_simple")
GEO_URL = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/v5.1.2/geojson/{name}.geojson"


def find_missing_geo_file_names() -> list[str]:
    geo_dir_path = user_dirs.get_geo_dir_path()
    return [name for name in GEO_FILE_NAMES if not (geo_dir_path / f"{name}.geojson").is_file()]


def check_geo() -> Check:
    missing = find_missing_geo_file_names()
    if missing:
        return Check("map_data", False, f"missing {len(missing)} of {len(GEO_FILE_NAMES)} Natural Earth files",
                     "run `explainer-studio setup`")
    return Check("map_data", True, f"{len(GEO_FILE_NAMES)} Natural Earth files in {user_dirs.get_geo_dir_path()}")


def ensure_geo(report_progress: ProgressReporter) -> str:
    missing = find_missing_geo_file_names()
    for name in missing:
        report_progress(f"downloading {name}.geojson")
        _download(GEO_URL.format(name=name), user_dirs.get_geo_dir_path() / f"{name}.geojson", report_progress, name)
    if not missing:
        return f"map data: {len(GEO_FILE_NAMES)} Natural Earth files already in {user_dirs.get_geo_dir_path()}"
    return f"map data: downloaded {len(missing)} Natural Earth file(s) to {user_dirs.get_geo_dir_path()}"


# The test render ----------------------------------------------------------------------------------------------------
TEST_SCENE = r'''
from manimlib import *


class SetupCheck(Scene):
    def construct(self):
        text = Text("中文字型 Explainer Studio", font="Noto Sans TC", font_size=40)
        formula = Tex(R"e^{i\pi} + 1 = 0")
        chinese = Tex(R"\text{面積} = \pi r^2", template="basic_ctex",
                      additional_preamble=R"\setCJKmainfont{Noto Sans TC}")
        self.play(FadeIn(VGroup(text, formula, chinese).arrange(DOWN, buff=0.5)), run_time=0.5)
        self.wait(0.5)
'''


def render_test_scene(report_progress: ProgressReporter) -> Path:
    """Render a tiny scene with Chinese text and two formulas, proving ManimGL, fonts, TeX and ffmpeg work together.
    Returns a PNG of its last frame."""
    setup_check_dir_path = user_dirs.get_cache_dir_path() / "setup-check"
    shutil.rmtree(setup_check_dir_path, ignore_errors=True)
    setup_check_dir_path.mkdir(parents=True)
    (setup_check_dir_path / "setup_check.py").write_text(TEST_SCENE, encoding="utf-8")
    # an empty cache makes TeX really compile instead of reusing formulas another TeX made earlier
    (setup_check_dir_path / "custom_config.yml").write_text(
        f"directories:\n  cache: {json.dumps(str(setup_check_dir_path / 'cache'))}\n", encoding="utf-8")
    report_progress("rendering a test scene with ManimGL (Chinese text and formulas)")
    render_result = _run([sys.executable, "-m", "manimlib", "setup_check.py", "SetupCheck", "-w", "-l", "--video_dir",
                          str(setup_check_dir_path)], timeout_seconds=900, cwd=setup_check_dir_path)
    video_file_paths = sorted(setup_check_dir_path.rglob("SetupCheck*.mp4"))
    if render_result.returncode != 0 or not video_file_paths:
        output_tail = "\n".join((render_result.stdout + render_result.stderr).strip().splitlines()[-12:])
        raise StudioError("the test render failed", output_tail or "manimgl wrote no video",
                          "fix what the message names (run `explainer-studio doctor`), then run setup again")
    still_file_path = setup_check_dir_path / "setup-check.png"
    _run([user_dirs.find_tool("ffmpeg") or "ffmpeg", "-v", "error", "-y", "-sseof", "-0.1", "-i",
          str(video_file_paths[0]), "-frames:v", "1", str(still_file_path)], timeout_seconds=60)
    return still_file_path if still_file_path.exists() else video_file_paths[0]


# Blender ------------------------------------------------------------------------------------------------------------
BLENDER_BUILD_BY_PLATFORM_MAP = {  # official builds; Blender 5 dropped Intel Macs, so they get the 4.5 LTS
    ("macos", "arm64"): "5.1.2/blender-5.1.2-macos-arm64.dmg",
    ("macos", "x64"): "4.5.14/blender-4.5.14-macos-x64.dmg",
    ("linux", "x64"): "5.1.2/blender-5.1.2-linux-x64.tar.xz",
    ("windows", "x64"): "5.1.2/blender-5.1.2-windows-x64.zip",
    ("windows", "arm64"): "5.1.2/blender-5.1.2-windows-arm64.zip",
}
BLENDER_URL = "https://download.blender.org/release/Blender{series}/{file}"
# from blender.org's blender-<version>.sha256 next to each build; a new build changes both together
BLENDER_SHA256_BY_FILE_NAME_MAP = {
    "blender-5.1.2-macos-arm64.dmg": "f104ffee2ba6aee32328e5c203b7e4608d8a1745f7bbcf2766f3b9777e8fbe17",
    "blender-4.5.14-macos-x64.dmg": "613e73339e97bd113adeeb28d9155beeacf2df7119ee4dbd6bdce234843645f6",
    "blender-5.1.2-linux-x64.tar.xz": "aaccb355f50183979b698bcce7467103a76261b5fa59f4972295842662a285fb",
    "blender-5.1.2-windows-x64.zip": "345bedea7b0acf7cc9666423d8553f9129622aea34ded65c23e8cb70f83f14ff",
    "blender-5.1.2-windows-arm64.zip": "91d39ca72ed4862724eb4398ccfc11913e0650654175efed72023efd7748960e",
}
MIN_BLENDER_VERSION = (4, 2)  # the render script uses the 4.2+ material and import APIs


def _list_blender_candidates() -> list[Path]:
    installed_blender_dir_path = user_dirs.get_data_dir_path() / "blender"
    candidates = [installed_blender_dir_path / "Blender.app" / "Contents" / "MacOS" / "Blender",
                  installed_blender_dir_path / "blender", installed_blender_dir_path / "blender.exe"]
    blender_on_path = shutil.which("blender")
    if blender_on_path:
        candidates.append(Path(blender_on_path))
    if get_operating_system() == "macos":
        for applications_dir_path in (Path("/Applications"), Path.home() / "Applications"):
            candidates.append(applications_dir_path / "Blender.app" / "Contents" / "MacOS" / "Blender")
    if get_operating_system() == "windows":
        for program_dir_path in {os.environ.get("ProgramFiles", r"C:\Program Files"),
                                 os.environ.get("LOCALAPPDATA", "")}:
            if program_dir_path:
                candidates.extend(sorted(Path(program_dir_path).glob("Blender Foundation/Blender*/blender.exe"),
                                         reverse=True))
    return candidates


def find_blender() -> str | None:
    return next((str(path) for path in _list_blender_candidates() if path.is_file()), None)


def read_blender_version(path: str) -> tuple[int, int] | None:
    match = re.search(r"Blender (\d+)\.(\d+)", _run([path, "--version"], timeout_seconds=120).stdout)
    return (int(match.group(1)), int(match.group(2))) if match else None


def check_blender() -> Check:
    path = find_blender()
    if path is None:
        return Check("blender", False, "not installed (only `asset blender render` needs it)",
                     "run `explainer-studio setup blender` (about 1 GB)", is_required=False)
    return Check("blender", True, path, is_required=False)


def ensure_blender(report_progress: ProgressReporter) -> str:
    path = find_blender()
    if path:
        installed_version = read_blender_version(path)
        if installed_version and installed_version >= MIN_BLENDER_VERSION:
            return f"Blender: using {path} ({installed_version[0]}.{installed_version[1]})"
        report_progress(f"{path} is Blender {installed_version or 'of an unknown version'}; 3D renders need "
                        f"{MIN_BLENDER_VERSION[0]}.{MIN_BLENDER_VERSION[1]} or later, so a user-level copy is "
                        "installed")
    build_path = BLENDER_BUILD_BY_PLATFORM_MAP.get((get_operating_system(), get_architecture()))
    if build_path is None:
        raise StudioError(f"no official Blender build for {get_operating_system()} {get_architecture()}",
                          "blender.org publishes none",
                          "install Blender 4.2 or later with the system's package manager so `blender` is on PATH")
    build_version, build_file_name = build_path.split("/")
    url = BLENDER_URL.format(series=".".join(build_version.split(".")[:2]), file=build_file_name)
    blender_dir_path = user_dirs.get_data_dir_path() / "blender"
    with tempfile.TemporaryDirectory() as temporary_dir_path:
        report_progress(f"downloading Blender {build_version} (several hundred MB)")
        archive_file_path = _download(url, Path(temporary_dir_path) / build_file_name, report_progress,
                                      f"Blender {build_version}", BLENDER_SHA256_BY_FILE_NAME_MAP[build_file_name])
        report_progress("unpacking Blender")
        unpacked_dir_path = Path(temporary_dir_path) / "unpacked"
        unpacked_dir_path.mkdir()
        if build_file_name.endswith(".dmg"):
            mount_dir_path = Path(temporary_dir_path) / "mount"
            attach_result = subprocess.run(["hdiutil", "attach", "-nobrowse", "-readonly", "-noautoopen",
                                            "-mountpoint", str(mount_dir_path), str(archive_file_path)],
                                           capture_output=True, text=True, input="Y\n", check=False)
            if attach_result.returncode != 0:
                raise StudioError("could not open the Blender disk image", attach_result.stderr.strip()[-300:],
                                  "run `explainer-studio setup blender` again")
            try:
                subprocess.run(["ditto", str(mount_dir_path / "Blender.app"), str(unpacked_dir_path / "Blender.app")],
                               check=True)
            finally:
                subprocess.run(["hdiutil", "detach", str(mount_dir_path), "-force"], capture_output=True, check=False)
            _replace_dir(unpacked_dir_path, blender_dir_path)
        else:
            if build_file_name.endswith(".zip"):
                with zipfile.ZipFile(archive_file_path) as archive:
                    archive.extractall(unpacked_dir_path)
            else:
                with tarfile.open(archive_file_path) as archive:
                    archive.extractall(unpacked_dir_path, filter="tar")
            _replace_dir(_find_unpacked_root(unpacked_dir_path), blender_dir_path)
    path = find_blender()
    if path is None or read_blender_version(path) is None:
        raise StudioError("the downloaded Blender does not start", f"looked in {blender_dir_path}",
                          "run `explainer-studio setup blender` again")
    return f"Blender: installed {build_version} at {path}"


# Playwright ---------------------------------------------------------------------------------------------------------
CHROMIUM_PROBE = """
from playwright.sync_api import sync_playwright
with sync_playwright() as playwright:
    print(playwright.chromium.executable_path)
    if LAUNCH:
        playwright.chromium.launch().close()
        print("launched")
"""


def _inspect_chromium(should_launch: bool) -> tuple[str | None, str]:
    code = CHROMIUM_PROBE.replace("LAUNCH", "True" if should_launch else "False")
    probe_result = _run_python(code, timeout_seconds=120)
    lines = probe_result.stdout.strip().splitlines()
    path = lines[0] if lines and Path(lines[0]).exists() else None
    problem = ("" if path and (not should_launch or lines[-1] == "launched")
               else (probe_result.stderr.strip()[-400:] or "not found"))
    return path, problem


def check_playwright() -> Check:
    path, _ = _inspect_chromium(should_launch=False)
    if path is None:
        return Check("playwright_chromium", False, "not installed (only `asset playwright record` needs it)",
                     "run `explainer-studio setup playwright` (about 150 MB)", is_required=False)
    return Check("playwright_chromium", True, path, is_required=False)


def ensure_playwright(report_progress: ProgressReporter) -> str:
    path, problem = _inspect_chromium(should_launch=True)
    if path and not problem:
        return f"Playwright Chromium: using {path}"
    report_progress("installing Chromium for Playwright (about 150 MB)")
    install_result = subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=False,
                                    stdout=sys.stderr, stderr=sys.stderr)
    if install_result.returncode != 0:
        raise StudioError("Playwright could not install Chromium", f"exit code {install_result.returncode}",
                          "run `explainer-studio setup playwright` again")
    path, problem = _inspect_chromium(should_launch=True)
    if problem:
        fix = (f"install Chromium's system libraries: `sudo {sys.executable} -m playwright install-deps chromium`"
               if get_operating_system() == "linux" else "run `explainer-studio setup playwright` again")
        raise StudioError("Chromium is installed but does not start", problem, fix)
    return f"Playwright Chromium: installed {path}"


# Narration keys and other checks -----------------------------------------------------------------------------------
def check_narration() -> list[Check]:
    from .credentials import find_api_key
    from .narration_providers import PROVIDER_BY_NAME_MAP

    checks = []
    for provider_name, provider in PROVIDER_BY_NAME_MAP.items():
        if provider.api_key_env is None:
            continue
        api_key = find_api_key(provider_name)
        detail = f"key found ({api_key.source})" if api_key else "no key"
        checks.append(Check(f"narration_key_{provider_name}", api_key is not None, detail,
                            f"only needed for {provider_name} narration: ask the user to run `explainer-studio setup "
                            f"narration {provider_name}` in their own terminal", is_required=False))
    if get_operating_system() == "macos":
        from .narration_providers.macos_say import find_default_voice

        voices = [voice for voice in (find_default_voice("zh-TW"), find_default_voice("en")) if voice]
        checks.append(Check("narration_macos_say", bool(voices), f"free voices: {', '.join(voices) or 'none'}",
                            "add voices in System Settings > Accessibility > Spoken Content", is_required=False))
    return checks


def check_disk() -> Check:
    existing_dir_path = user_dirs.get_data_dir_path()
    while not existing_dir_path.exists():
        existing_dir_path = existing_dir_path.parent
    free_gigabytes = shutil.disk_usage(existing_dir_path).free / 1e9
    return Check("disk_space", free_gigabytes >= 3, f"{free_gigabytes:.0f} GB free",
                 "free some disk space: an episode's renders and the tools take a few GB", is_required=False)


def check_latest_release() -> Check:
    """Whether a newer release is out (asked at most once a day). Never fails doctor: upgrading is for the agent to do
    between episodes."""
    from . import __version__
    from .releases import find_newer_release_version, parse_release_version

    if parse_release_version(__version__) is None:
        return Check("latest_release", True, f"{__version__} is a dev build", is_required=False)
    newer_version = find_newer_release_version(__version__)
    if newer_version is None:
        return Check("latest_release", True, f"no newer release than {__version__} (or GitHub cannot be reached)",
                     is_required=False)
    return Check("latest_release", False, f"{newer_version} is out", "run `explainer-studio upgrade` before starting the next "
                 "episode", is_required=False)


def run_checks() -> list[Check]:
    return [check_manimgl(), *check_ffmpeg(), check_tex(), check_fonts(), check_geo(), check_disk(), *check_narration(),
            check_blender(), check_playwright(), check_latest_release()]
