"""The spec `asset blender render <spec>` reads (YAML or JSON), written by the agent.

    name: heart_turn                  # optional: the output name (default: the spec file's name)
    objects:
      - {type: mesh, mesh_file_path: shared/assets/3d/heart.stl, name: heart, color: "#C0392B",
         rotation_degrees: [90, 0, 0]}
      - {type: molecule, name: ethanol, smiles: CCO}
      - {type: primitive, shape: sphere, name: sun, size: 1.0, location: [0, 0, 0], color: "#FFCC00"}
    highlight_color_by_part_map: {heart: "#FFFF00"}  # glow; a part inside a mesh file is "heart/<part name>"
    dimmed_parts: [sun]               # drawn faded, as context
    camera: {elevation_degrees: 20, orbit_degrees: 360, start_degrees: 0, focal_length_millimeters: 50}
    duration_seconds: 6
    is_still: false
    labeled_parts: [heart]            # screen positions per frame go to <name>.labels.json
    quality: final                    # final 1920x1080 at 30 fps, draft 640x360 at 24 fps

Mesh paths are relative to the spec's folder or to production/.
"""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator

Color = Annotated[str, Field(pattern=r"^#[0-9A-Fa-f]{6}$")]
Vector3 = Annotated[list[float], Field(min_length=3, max_length=3)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class MeshObject(StrictModel):
    type: Literal["mesh"]
    mesh_file_path: str  # .stl, .obj, .ply, .glb, .gltf or .fbx
    name: str | None = None
    color: Color | None = None
    rotation_degrees: Vector3 | None = None  # about x, y, z


class MoleculeObject(StrictModel):
    type: Literal["molecule"]
    name: str | None = None
    smiles: str | None = None
    atoms: list[tuple[str, float, float, float]] | None = None
    bonds: list[tuple[int, int, int]] = []
    atom_scale: float = Field(default=1.0, gt=0)

    @model_validator(mode="after")
    def smiles_or_atoms(self) -> MoleculeObject:
        if (self.smiles is None) == (self.atoms is None):
            raise ValueError("give a molecule either smiles or atoms (with bonds)")
        return self


class PrimitiveObject(StrictModel):
    type: Literal["primitive"]
    shape: Literal["sphere", "cube", "cylinder", "cone", "torus"] = "sphere"
    name: str | None = None
    size: float = Field(default=1.0, gt=0)
    thickness: float | None = Field(default=None, gt=0)  # torus tube radius
    location: Vector3 = [0.0, 0.0, 0.0]
    color: Color | None = None


class Camera(StrictModel):
    elevation_degrees: float = 20
    orbit_degrees: float | None = None  # default: a full turn, or none for a still
    start_degrees: float = 0
    distance: float | None = Field(default=None, gt=0)  # default: the whole subject fits
    focal_length_millimeters: float = Field(default=50, gt=0)


SceneObject = Annotated[Union[MeshObject, MoleculeObject, PrimitiveObject], Field(discriminator="type")]  # noqa: UP007


class BlenderRenderSpec(StrictModel):
    name: str | None = None
    objects: list[SceneObject] = Field(min_length=1)
    highlight_color_by_part_map: dict[str, Color] = {}
    dimmed_parts: list[str] = []
    camera: Camera = Camera()
    duration_seconds: float = Field(default=6, gt=0, le=60)
    is_still: bool = False
    labeled_parts: list[str] = []
    quality: Literal["draft", "final"] = "final"
