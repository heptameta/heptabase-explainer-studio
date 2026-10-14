"""3D shots rendered by Blender in the background: STL and other meshes, molecules from SMILES, simple shapes, with
highlights, faded context and an orbiting camera. Writes <name>.mp4 and <name>.labels.json (where each labelled
object is on screen in every frame, for labels drawn in ManimGL)."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import time
from collections.abc import Callable
from pathlib import Path

from ..errors import StudioError
from ..paths import Series
from ..schemas.blender_render_spec import BlenderRenderSpec, MeshObject, MoleculeObject
from .common import choose_output_file_path, find_spec_input, load_spec, run_ffmpeg, sanitize_file_stem

BLENDER_SCRIPT_FILE_PATH = Path(__file__).with_name("blender_script.py")
RESOLUTION_AND_FPS_BY_QUALITY_MAP = {"draft": (640, 360, 24), "final": (1920, 1080, 30)}


def embed_molecule_3d(smiles: str) -> tuple[list, list]:
    """Atoms [symbol, x, y, z] and bonds [a, b, order] of a molecule in 3D (RDKit embedding and force field)."""
    from rdkit import Chem
    from rdkit.Chem import AllChem

    molecule = Chem.MolFromSmiles(smiles)
    if molecule is None:
        raise StudioError(f"RDKit cannot read the SMILES {smiles!r}", "it is not valid SMILES",
                          "fix the smiles field in the spec")
    molecule = Chem.AddHs(molecule)
    if AllChem.EmbedMolecule(molecule, randomSeed=7) != 0:
        raise StudioError(f"no 3D coordinates for {smiles!r}", "RDKit could not embed the molecule",
                          "give atoms and bonds in the spec instead")
    AllChem.MMFFOptimizeMolecule(molecule)
    conformer = molecule.GetConformer()
    atoms = [[atom.GetSymbol(), *(float(coordinate) for coordinate in conformer.GetAtomPosition(atom.GetIdx()))]
             for atom in molecule.GetAtoms()]
    Chem.Kekulize(molecule, clearAromaticFlags=True)
    bonds = [[bond.GetBeginAtomIdx(), bond.GetEndAtomIdx(), int(bond.GetBondTypeAsDouble())]
             for bond in molecule.GetBonds()]
    return atoms, bonds


def compute_blender_script_spec(spec: BlenderRenderSpec, spec_dir_path: Path, series: Series) -> dict:
    """The spec the script inside Blender reads: absolute paths, molecules as atoms and bonds."""
    objects = []
    for spec_object in spec.objects:
        object_fields = spec_object.model_dump(exclude_none=True)
        if isinstance(spec_object, MeshObject):
            object_fields["mesh_file_path"] = str(find_spec_input(spec_object.mesh_file_path, spec_dir_path, series))
        elif isinstance(spec_object, MoleculeObject) and spec_object.smiles:
            object_fields["atoms"], object_fields["bonds"] = embed_molecule_3d(object_fields.pop("smiles"))
        objects.append(object_fields)
    width_pixels, height_pixels, fps = RESOLUTION_AND_FPS_BY_QUALITY_MAP[spec.quality]
    camera = spec.camera.model_dump(exclude_none=True)
    return {"objects": objects, "highlight_color_by_part_map": spec.highlight_color_by_part_map,
            "dimmed_parts": spec.dimmed_parts, "camera": camera, "duration_seconds": spec.duration_seconds, "fps": fps,
            "resolution": [width_pixels, height_pixels], "is_still": spec.is_still,
            "labeled_parts": spec.labeled_parts}


def render(series: Series, spec_path: Path, destination_path: Path | None,
           report_progress: Callable[[str], None]) -> dict[str, Path]:
    from ..environment import find_blender

    blender_path = find_blender()
    if blender_path is None:
        raise StudioError("Blender is not installed", "`asset blender render` runs Blender in the background",
                          "run `explainer-studio setup blender`")
    spec = load_spec(spec_path, BlenderRenderSpec)
    file_stem = sanitize_file_stem(spec.name or spec_path.stem)
    video_file_path = choose_output_file_path(series, "video", f"{file_stem}.mp4", destination_path)
    blender_script_spec = compute_blender_script_spec(spec, spec_path.resolve().parent, series)
    frame_count = 1 if spec.is_still else int(spec.duration_seconds * blender_script_spec["fps"])
    with tempfile.TemporaryDirectory(prefix="explainer-studio-blender-") as temporary_dir_path:
        work_dir_path = Path(temporary_dir_path)
        (work_dir_path / "spec.json").write_text(json.dumps(blender_script_spec), encoding="utf-8")
        report_progress(f"rendering {frame_count} frame(s) with Blender at {blender_script_spec['resolution'][0]}x"
                        f"{blender_script_spec['resolution'][1]}")
        command = [blender_path, "-b", "--factory-startup", "--python-exit-code", "1", "-P",
                   str(BLENDER_SCRIPT_FILE_PATH), "--", str(work_dir_path / "spec.json"), str(work_dir_path)]
        # Blender buffers its output when it is not a terminal, so progress comes from the frames on disk
        log_file_path = work_dir_path / "blender.log"
        with (log_file_path.open("w") as log_handle,
              subprocess.Popen(command, stdout=log_handle, stderr=subprocess.STDOUT) as process):
            next_report_fraction = 0.1
            while process.poll() is None:
                time.sleep(1)
                done_fraction = len(list((work_dir_path / "frames").glob("*.png"))) / frame_count
                if done_fraction >= next_report_fraction and done_fraction < 1:
                    report_progress(f"  {done_fraction:.0%} of the frames")
                    next_report_fraction = done_fraction + 0.1
        log_lines = log_file_path.read_text(errors="replace").splitlines()
        frame_file_paths = sorted((work_dir_path / "frames").glob("*.png"))
        if process.returncode != 0 or not frame_file_paths:
            error_lines = [line for line in log_lines if "Error" in line or "error" in line] or log_lines
            raise StudioError("Blender could not render the spec", "\n".join(error_lines[-12:]),
                              "fix the spec (or the model file) and run again")
        video_file_path.parent.mkdir(parents=True, exist_ok=True)
        run_ffmpeg(["-framerate", str(blender_script_spec["fps"]), "-i", str(work_dir_path / "frames" / "%04d.png"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-movflags", "+faststart",
                    str(video_file_path)],
                   "encode the frames")
        output_file_path_by_kind_map = {"video": video_file_path, "labels": video_file_path.with_suffix(".labels.json")}
        shutil.copyfile(work_dir_path / "labels.json", output_file_path_by_kind_map["labels"])
        if spec.is_still:
            output_file_path_by_kind_map["still"] = video_file_path.with_suffix(".png")
            shutil.copyfile(frame_file_paths[0], output_file_path_by_kind_map["still"])
    return output_file_path_by_kind_map
