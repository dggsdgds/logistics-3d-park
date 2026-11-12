import bpy
import math
import os
import time
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "assets", "forklift.glb")
PREVIEW = os.path.join(HERE, "forklift_preview.png")
OBJECTS = []


def log(*args):
    print("FORKLIFT:", *args, flush=True)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    return scene


def material(name, color, metallic=0.0, roughness=0.5):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.use_backface_culling = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return m


def box(name, size, loc, mat, bevel=0.0, parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    if bevel > 0:
        mod = obj.modifiers.new("Bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
    if parent is not None:
        obj.parent = parent
        obj.matrix_parent_inverse = parent.matrix_world.inverted()
    OBJECTS.append(obj)
    return obj


def cylinder(name, radius, depth, loc, mat, rotation=(0, 0, 0), vertices=16, parent=None):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices, radius=radius, depth=depth, location=loc, rotation=rotation
    )
    obj = bpy.context.active_object
    obj.name = name
    obj.data.materials.append(mat)
    if parent is not None:
        obj.parent = parent
        obj.matrix_parent_inverse = parent.matrix_world.inverted()
    OBJECTS.append(obj)
    return obj


def add_preview(scene):
    floor_mat = material("PreviewFloor", (0.12, 0.13, 0.15), 0.0, 0.9)
    bpy.ops.mesh.primitive_plane_add(size=18, location=(0, 0, -0.01))
    floor = bpy.context.active_object
    floor.data.materials.append(floor_mat)

    cam_data = bpy.data.cameras.new("ForkliftCamera")
    cam = bpy.data.objects.new("ForkliftCamera", cam_data)
    scene.collection.objects.link(cam)
    cam.location = (4.2, 4.6, 3.2)
    cam.rotation_euler = (Vector((0.0, 0.2, 0.9)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = 55
    scene.camera = cam

    sun_data = bpy.data.lights.new("ForkliftSun", "SUN")
    sun_data.energy = 4.0
    sun_data.angle = math.radians(10)
    sun = bpy.data.objects.new("ForkliftSun", sun_data)
    scene.collection.objects.link(sun)
    sun.location = (5, 6, 8)
    sun.rotation_euler = (Vector((0, 0, 0)) - sun.location).to_track_quat("-Z", "Y").to_euler()

    fill_data = bpy.data.lights.new("ForkliftFill", "AREA")
    fill_data.energy = 220
    fill_data.size = 5
    fill = bpy.data.objects.new("ForkliftFill", fill_data)
    scene.collection.objects.link(fill)
    fill.location = (-3, 2, 5)
    fill.rotation_euler = (Vector((0, 0, 1)) - fill.location).to_track_quat("-Z", "Y").to_euler()

    world = bpy.data.worlds.new("ForkliftWorld")
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (0.018, 0.026, 0.038, 1.0)
    bg.inputs["Strength"].default_value = 1.0
    scene.world = world

    scene.render.resolution_x = 1000
    scene.render.resolution_y = 700
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = PREVIEW
    scene.cycles.samples = 24
    scene.cycles.use_denoising = True
    scene.view_settings.look = "AgX - Medium High Contrast"

    log("Rendering preview...")
    bpy.ops.render.render(write_still=True)
    log("Preview saved", PREVIEW)


def main():
    start = time.time()
    scene = reset()

    yellow = material("ForkliftYellow", (0.86, 0.52, 0.03), 0.25, 0.38)
    black = material("ForkliftBlack", (0.025, 0.03, 0.035), 0.35, 0.55)
    dark = material("ForkliftDark", (0.08, 0.09, 0.1), 0.5, 0.45)
    steel = material("ForkliftSteel", (0.55, 0.6, 0.65), 0.8, 0.3)
    seat_mat = material("ForkliftSeat", (0.05, 0.12, 0.2), 0.0, 0.8)
    glass = material("ForkliftGlass", (0.06, 0.18, 0.25), 0.1, 0.08)
    glass.blend_method = "BLEND"
    glass.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = 0.3
    light = material("ForkliftLight", (1.0, 0.85, 0.55), 0.0, 0.3)
    light.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (1.0, 0.8, 0.4, 1.0)
    light.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 2.0

    # Forklift faces +Y in Blender, which becomes -Z in glTF.
    box("ForkliftChassis", (1.15, 2.0, 0.45), (0, 0, 0.55), yellow, 0.04)
    box("ForkliftHood", (1.1, 0.75, 0.55), (0, 0.55, 0.95), yellow, 0.05)
    box("ForkliftCounterweight", (1.28, 0.55, 0.82), (0, -0.95, 0.78), yellow, 0.04)
    box("ForkliftBumper", (1.3, 0.12, 0.22), (0, -1.24, 0.38), black)
    box("ForkliftSeatBase", (0.62, 0.58, 0.32), (0, 0.0, 1.02), black)
    box("ForkliftSeatBack", (0.62, 0.16, 0.62), (0, -0.3, 1.42), seat_mat)
    box("ForkliftSeatCushion", (0.62, 0.52, 0.14), (0, 0.0, 1.2), seat_mat)

    # Overhead guard.
    for sx in (-0.56, 0.56):
        for sy in (-0.55, 0.55):
            box("ForkliftGuardPost", (0.075, 0.075, 1.05), (sx, sy, 1.78), dark)
    box("ForkliftGuardRoof", (1.28, 1.35, 0.08), (0, 0, 2.3), dark)
    for sx in (-0.56, 0.56):
        box("ForkliftGuardSide", (0.05, 1.2, 0.05), (sx, 0, 2.22), dark)

    # Mast: two rails and cross braces at the front (+Y).
    for sx in (-0.42, 0.42):
        box("ForkliftMastRail", (0.13, 0.13, 2.45), (sx, 1.02, 1.4), black, 0.01)
    box("ForkliftMastTop", (1.0, 0.12, 0.13), (0, 1.02, 2.6), black)
    box("ForkliftMastMid", (0.95, 0.08, 0.1), (0, 1.02, 1.85), black)
    box("ForkliftMastBottom", (1.0, 0.12, 0.12), (0, 1.02, 0.22), black)
    cylinder("ForkliftMastCylinder", 0.06, 1.6, (0, 1.0, 1.35), steel, vertices=10)

    # Fork carriage is a separate node so the web app can lift it.
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 1.05, 0.27))
    carriage = bpy.context.active_object
    carriage.name = "ForkliftForks"
    OBJECTS.append(carriage)
    box("ForkliftBackplate", (0.92, 0.1, 0.72), (0, 1.05, 0.64), steel, 0.01, parent=carriage)
    for sx in (-0.3, 0.3):
        box("ForkliftFork", (0.15, 1.15, 0.07), (sx, 1.68, 0.09), steel, parent=carriage)
        box("ForkliftForkTip", (0.15, 0.16, 0.07), (sx, 2.27, 0.09), steel, parent=carriage)
    for sx in (-0.36, 0.36):
        box("ForkliftCarriageRail", (0.08, 0.08, 0.9), (sx, 1.04, 0.62), dark, parent=carriage)

    # Wheels.
    for sx in (-0.66, 0.66):
        for sy in (-0.62, 0.64):
            cylinder(
                "ForkliftWheel", 0.34, 0.26, (sx, sy, 0.36), black,
                rotation=(0, math.pi / 2, 0), vertices=16
            )
            cylinder(
                "ForkliftHub", 0.16, 0.28, (sx, sy, 0.36), steel,
                rotation=(0, math.pi / 2, 0), vertices=12
            )

    # Front lights and a small steering wheel.
    for sx in (-0.42, 0.42):
        box("ForkliftHeadlight", (0.18, 0.06, 0.12), (sx, 0.92, 0.88), light)
    cylinder("ForkliftSteering", 0.16, 0.05, (0, 0.2, 1.26), dark, rotation=(math.radians(70), 0, 0), vertices=16)

    # A small propane tank on the rear.
    cylinder("ForkliftTank", 0.22, 0.8, (0, -1.36, 0.8), steel, rotation=(0, math.pi / 2, 0), vertices=14)

    # Visibility: keep the forks above the floor.
    carriage.location.z = 0.27

    add_preview(scene)

    bpy.ops.object.select_all(action="DESELECT")
    for obj in OBJECTS:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = OBJECTS[0]

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=OUT,
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_texcoords=False,
        export_normals=True,
        export_materials="EXPORT",
        export_cameras=False,
        export_lights=False,
    )
    log("GLB saved", OUT, os.path.getsize(OUT), "bytes")
    log("DONE in", round(time.time() - start, 2), "sec")


if __name__ == "__main__":
    main()
