"""Runs inside Blender (4.2 or later): render a 3D shot from a JSON spec written by `asset blender render`.

    blender -b --factory-startup -P blender_script.py -- spec.json output_dir_path

Spec (paths absolute, molecules already expanded to atoms and bonds):
  objects: [{"type": "mesh", "mesh_file_path": "/abs/heart.stl", "name": "heart", "color": "#C0392B",
             "rotation_degrees": [90, 0, 0]},
            {"type": "molecule", "name": "ethanol", "atoms": [["C", x, y, z], ...], "bonds": [[i, j, order], ...]},
            {"type": "primitive", "shape": "sphere|cube|cylinder|cone|torus", "name": "sun", "size": 1.0,
             "location": [x, y, z], "color": "#FFCC00"}]
  highlight_color_by_part_map: {"<object name>" or "<object name>/<part name>": "#FFFF00"}
      glow on what the narration is about
  dimmed_parts: ["<object name>", ...]
      drawn faded, as context
  camera: {"elevation_degrees": 20, "orbit_degrees": 360, "start_degrees": 0, "distance": null,
           "focal_length_millimeters": 50}
  duration_seconds, fps, resolution: [w, h], is_still, labeled_parts: ["<object name>", ...]
Writes output_dir_path/frames/####.png and output_dir_path/labels.json: {"fps", "frame_count",
"screen_positions_by_part_map"}, with each labeled part's center on screen in every frame as [x, y, depth], x and y
from 0 to 1 measured from the bottom-left.
This file imports bpy, so only Blender's own Python can run it.
"""

import json
import math
import sys
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

COLOR_AND_RADIUS_BY_ELEMENT_MAP = {"H": ("#FFFFFF", 0.25), "C": ("#8C8C8C", 0.38), "N": ("#3355FF", 0.36),
                                   "O": ("#FF3333", 0.35), "S": ("#FFDD33", 0.45), "P": ("#FF9900", 0.45),
                                   "F": ("#33DD33", 0.33), "Cl": ("#33DD33", 0.42), "Br": ("#992222", 0.46),
                                   "I": ("#9933AA", 0.5)}
DIMMED_ALPHA = 0.18


def convert_hex_to_linear_rgba(value, alpha=1.0):
    value = value.lstrip("#")
    r, g, b = (int(value[i:i + 2], 16) / 255 for i in (0, 2, 4))

    def convert_srgb_channel_to_linear(channel):
        return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4

    return (convert_srgb_channel_to_linear(r), convert_srgb_channel_to_linear(g), convert_srgb_channel_to_linear(b),
            alpha)


def create_material(name, color, emission=None, alpha=1.0):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = convert_hex_to_linear_rgba(color)
    bsdf.inputs["Roughness"].default_value = 0.45
    if emission:
        bsdf.inputs["Emission Color"].default_value = convert_hex_to_linear_rgba(emission)
        bsdf.inputs["Emission Strength"].default_value = 1.2
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
        if hasattr(material, "surface_render_method"):
            material.surface_render_method = "BLENDED"
    return material


def assign_material(blender_object, material):
    if blender_object.data is not None and hasattr(blender_object.data, "materials"):
        blender_object.data.materials.clear()
        blender_object.data.materials.append(material)


def import_mesh(path):
    objects_before = set(bpy.data.objects)
    suffix = Path(path).suffix.lower()
    importer_by_suffix_map = {".glb": lambda: bpy.ops.import_scene.gltf(filepath=path),
                              ".gltf": lambda: bpy.ops.import_scene.gltf(filepath=path),
                              ".obj": lambda: bpy.ops.wm.obj_import(filepath=path),
                              ".stl": lambda: bpy.ops.wm.stl_import(filepath=path),
                              ".ply": lambda: bpy.ops.wm.ply_import(filepath=path),
                              ".fbx": lambda: bpy.ops.import_scene.fbx(filepath=path)}
    if suffix not in importer_by_suffix_map:
        raise SystemExit(f"unsupported 3D format {suffix}")
    importer_by_suffix_map[suffix]()
    new_objects = [blender_object for blender_object in bpy.data.objects
                   if blender_object not in objects_before and blender_object.type == "MESH"]
    # scanned and printed models have no smooth normals: smooth by angle so they read as organic
    for blender_object in new_objects:
        bpy.ops.object.select_all(action="DESELECT")
        blender_object.select_set(True)
        bpy.context.view_layer.objects.active = blender_object
        try:
            bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
        except (AttributeError, RuntimeError):
            bpy.ops.object.shade_smooth()
    return new_objects


def add_primitive(object_spec, name, highlight_color, alpha):
    shape = object_spec.get("shape", "sphere")
    location = object_spec.get("location", (0, 0, 0))
    size = object_spec.get("size", 1.0)
    if shape == "torus":  # an orbit or a ring: size is the ring radius, the tube stays thin
        bpy.ops.mesh.primitive_torus_add(location=location, major_radius=size,
                                         minor_radius=object_spec.get("thickness", 0.02 * size),
                                         major_segments=128, minor_segments=16)
        blender_object = bpy.context.active_object
    else:
        adder_by_shape_map = {"sphere": bpy.ops.mesh.primitive_uv_sphere_add, "cube": bpy.ops.mesh.primitive_cube_add,
                              "cylinder": bpy.ops.mesh.primitive_cylinder_add, "cone": bpy.ops.mesh.primitive_cone_add}
        if shape not in adder_by_shape_map:
            raise SystemExit(f"unknown primitive shape {shape}")
        adder_by_shape_map[shape](location=location)
        blender_object = bpy.context.active_object
        blender_object.scale = [size] * 3
    if shape == "sphere":
        bpy.ops.object.shade_smooth()
    assign_material(blender_object, create_material(name, object_spec.get("color", "#BBBBBB"), highlight_color, alpha))
    return [blender_object]


def add_molecule(object_spec, name, highlight_color, alpha):
    atoms, bonds = object_spec["atoms"], object_spec.get("bonds", [])
    made_objects, material_by_element_map = [], {}
    for element, x, y, z in atoms:
        color, radius = COLOR_AND_RADIUS_BY_ELEMENT_MAP.get(element, ("#CC66CC", 0.4))
        bpy.ops.mesh.primitive_uv_sphere_add(radius=radius * object_spec.get("atom_scale", 1.0), location=(x, y, z),
                                             segments=32, ring_count=16)
        blender_object = bpy.context.active_object
        bpy.ops.object.shade_smooth()
        if element not in material_by_element_map:
            material_by_element_map[element] = create_material(f"{name}_{element}", color, highlight_color, alpha)
        assign_material(blender_object, material_by_element_map[element])
        made_objects.append(blender_object)
    bond_material = create_material(f"{name}_bond", "#BBBBBB", highlight_color, alpha)
    for i, j, order in bonds:
        begin_position, end_position = Vector(atoms[i][1:]), Vector(atoms[j][1:])
        direction = end_position - begin_position
        offsets = [0.0] if order == 1 else [-0.09, 0.09] if order == 2 else [-0.13, 0.0, 0.13]
        for offset in offsets:
            perpendicular = direction.cross(Vector((0, 0, 1)))
            if perpendicular.length < 1e-6:
                perpendicular = direction.cross(Vector((0, 1, 0)))
            perpendicular.normalize()
            middle = (begin_position + end_position) / 2 + perpendicular * offset
            bpy.ops.mesh.primitive_cylinder_add(radius=0.07, depth=direction.length, location=middle, vertices=24)
            cylinder = bpy.context.active_object
            cylinder.rotation_mode = "QUATERNION"
            cylinder.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(direction)
            bpy.ops.object.shade_smooth()
            assign_material(cylinder, bond_material)
            made_objects.append(cylinder)
    return made_objects


def add_spec_objects(spec):
    objects_by_name_map = {}
    highlight_color_by_part_map = spec.get("highlight_color_by_part_map", {})
    dimmed_parts = spec.get("dimmed_parts", [])
    for index, object_spec in enumerate(spec.get("objects", [])):
        name = object_spec.get("name") or f"obj{index}"
        highlight_color = highlight_color_by_part_map.get(name)
        alpha = DIMMED_ALPHA if name in dimmed_parts else 1.0
        if object_spec["type"] == "mesh":
            made_objects = import_mesh(object_spec["mesh_file_path"])
            if object_spec.get("rotation_degrees"):  # about x, y, z: files disagree about which way is up
                rx, ry, rz = (math.radians(degrees) for degrees in object_spec["rotation_degrees"])
                for blender_object in made_objects:
                    if blender_object.parent is None:
                        rotation = blender_object.rotation_euler
                        blender_object.rotation_euler = (rotation[0] + rx, rotation[1] + ry, rotation[2] + rz)
                bpy.context.view_layer.update()
            if object_spec.get("color") or highlight_color or alpha < 1:
                shared_material = create_material(name, object_spec.get("color", "#BBBBBB"), highlight_color, alpha)
                for blender_object in made_objects:
                    assign_material(blender_object, shared_material)
            # parts inside the file keep their own names, so highlight_color_by_part_map can target
            # "heart/left_ventricle"
            for blender_object in made_objects:
                part_name = f"{name}/{blender_object.name}"
                if highlight_color_by_part_map.get(part_name) or part_name in dimmed_parts:
                    part_material = create_material(part_name, object_spec.get("color", "#BBBBBB"),
                                                    highlight_color_by_part_map.get(part_name),
                                                    DIMMED_ALPHA if part_name in dimmed_parts else 1.0)
                    assign_material(blender_object, part_material)
                objects_by_name_map[part_name] = [blender_object]
        elif object_spec["type"] == "primitive":
            made_objects = add_primitive(object_spec, name, highlight_color, alpha)
        elif object_spec["type"] == "molecule":
            made_objects = add_molecule(object_spec, name, highlight_color, alpha)
        else:
            raise SystemExit(f"unknown object type {object_spec['type']}")
        objects_by_name_map[name] = made_objects
    return objects_by_name_map


def measure_bounds(objects):
    points = [blender_object.matrix_world @ Vector(corner)
              for blender_object in objects for corner in blender_object.bound_box]
    low = Vector((min(point.x for point in points), min(point.y for point in points), min(point.z for point in points)))
    high = Vector((max(point.x for point in points), max(point.y for point in points),
                   max(point.z for point in points)))
    return low, high


def find_eevee_engine():
    """EEVEE is BLENDER_EEVEE_NEXT in Blender 4.2 to 4.5 and BLENDER_EEVEE again from 5.0."""
    engine_ids = {enum_item.identifier for enum_item in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items}
    return "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engine_ids else "BLENDER_EEVEE"


def main():
    arguments = sys.argv[sys.argv.index("--") + 1:]
    spec = json.loads(Path(arguments[0]).read_text(encoding="utf-8"))
    output_dir_path = Path(arguments[1])
    (output_dir_path / "frames").mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    objects_by_name_map = add_spec_objects(spec)
    all_objects = list({id(blender_object): blender_object
                        for objects in objects_by_name_map.values() for blender_object in objects}.values())
    if not all_objects:
        raise SystemExit("the spec has no objects")
    low, high = measure_bounds(all_objects)
    # models come in any unit (an STL in millimetres is hundreds of units wide): bring the subject to radius 3
    scale_factor = 3.0 / max((high - low).length / 2, 1e-6)
    holder = bpy.data.objects.new("holder", None)
    scene.collection.objects.link(holder)
    holder.location = (low + high) / 2
    bpy.context.view_layer.update()
    for blender_object in all_objects:
        if blender_object.parent is None:
            blender_object.parent = holder
            blender_object.matrix_parent_inverse = holder.matrix_world.inverted()
    holder.location = (0, 0, 0)
    holder.scale = (scale_factor, scale_factor, scale_factor)
    bpy.context.view_layer.update()
    low, high = measure_bounds(all_objects)
    center = (low + high) / 2
    extent = high - low
    radius = max(max(extent.x, extent.y, extent.z) / 2 * 1.12, 1e-3)  # the longest side: flat things stay big

    # a camera orbiting the centre; the lights ride on the same rig so the subject stays lit as it turns
    camera_spec = spec.get("camera", {})
    focal_length_millimeters = camera_spec.get("focal_length_millimeters", 50)
    width_pixels, height_pixels = spec.get("resolution", [1280, 720])
    half_fov_radians = math.atan(18 / focal_length_millimeters * min(1.0, height_pixels / width_pixels))
    distance = camera_spec.get("distance") or radius / math.sin(half_fov_radians) * 1.02
    rig = bpy.data.objects.new("rig", None)
    scene.collection.objects.link(rig)
    rig.location = center
    camera_data = bpy.data.cameras.new("camera")
    camera_data.lens = focal_length_millimeters
    camera_data.clip_start, camera_data.clip_end = 0.01, 1000.0
    camera = bpy.data.objects.new("camera", camera_data)
    scene.collection.objects.link(camera)
    camera.parent = rig
    elevation_radians = math.radians(camera_spec.get("elevation_degrees", 20))
    camera.location = (0, -distance * math.cos(elevation_radians), distance * math.sin(elevation_radians))
    track = camera.constraints.new("TRACK_TO")
    track.target = rig
    track.track_axis, track.up_axis = "TRACK_NEGATIVE_Z", "UP_Y"
    scene.camera = camera
    for name, energy, position in (("key", 900, (-1.2, -1.4, 1.6)), ("fill", 300, (1.6, -1.0, 0.6)),
                                   ("rim", 700, (0.2, 1.6, 1.4))):
        light_data = bpy.data.lights.new(name, "AREA")
        light_data.energy = energy * (distance / 6) ** 2
        light_data.size = distance * 0.6
        light = bpy.data.objects.new(name, light_data)
        scene.collection.objects.link(light)
        light.parent = rig
        light.location = [coordinate * distance for coordinate in position]
        aim = light.constraints.new("TRACK_TO")
        aim.target = rig
        aim.track_axis, aim.up_axis = "TRACK_NEGATIVE_Z", "UP_Y"

    fps = spec.get("fps", 30)
    frame_count = 1 if spec.get("is_still") else max(1, int(spec.get("duration_seconds", 6) * fps))
    scene.render.fps = fps
    scene.frame_start, scene.frame_end = 1, frame_count
    start_radians = math.radians(camera_spec.get("start_degrees", 0))
    sweep_radians = math.radians(camera_spec.get("orbit_degrees", 0 if spec.get("is_still") else 360))
    # a full turn moves at constant speed so it loops; a partial one eases in and out
    is_linear = abs(sweep_radians) >= math.pi * 1.9
    bpy.context.preferences.edit.keyframe_new_interpolation_type = "LINEAR" if is_linear else "BEZIER"
    rig.rotation_mode = "XYZ"
    rig.rotation_euler = (0, 0, start_radians)
    rig.keyframe_insert("rotation_euler", frame=1)
    if frame_count > 1:
        rig.rotation_euler = (0, 0, start_radians + sweep_radians)
        rig.keyframe_insert("rotation_euler", frame=frame_count)

    scene.render.engine = find_eevee_engine()
    scene.render.resolution_x, scene.render.resolution_y = width_pixels, height_pixels
    scene.render.resolution_percentage = 100
    world = bpy.data.worlds.new("world")
    scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes["Background"]
    background.inputs[0].default_value = (0, 0, 0, 1)
    background.inputs[1].default_value = 0.0
    scene.view_settings.view_transform = "Standard"
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.filepath = str(output_dir_path / "frames" / "####")

    screen_positions_by_part_map = {}
    for name in spec.get("labeled_parts", []):
        objects = objects_by_name_map.get(name, [])
        if not objects:
            continue
        track_points = []
        for frame in range(1, frame_count + 1):
            scene.frame_set(frame)
            low, high = measure_bounds(objects)
            point = world_to_camera_view(scene, camera, (low + high) / 2)
            track_points.append([round(point.x, 4), round(point.y, 4), round(point.z, 3)])
        screen_positions_by_part_map[name] = track_points
    labels = {"fps": fps, "frame_count": frame_count, "screen_positions_by_part_map": screen_positions_by_part_map}
    (output_dir_path / "labels.json").write_text(json.dumps(labels), encoding="utf-8")
    scene.frame_set(1)
    bpy.ops.render.render(animation=True)


main()
