import bpy
import math
import os
import time
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "assets", "truck.glb")
PREVIEW = os.path.join(HERE, "truck_preview.png")

OBJECTS = []


def log(*args):
    print("TRUCK:", *args, flush=True)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    return scene


def material(name, color, metallic, roughness, alpha=1.0, transparent=False):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.use_backface_culling = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Alpha"].default_value = alpha
    if transparent:
        try:
            m.blend_method = "BLEND"
        except Exception:
            pass
        try:
            m.surface_render_method = "BLENDED"
        except Exception:
            pass
        m.use_backface_culling = True
    return m


def box(name, size, loc, mat, bevel=0.0):
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
    OBJECTS.append(obj)
    return obj


def wheel(name, x, y, z, tire_mat, rim_mat):
    parts = []
    for radius, depth, material in ((0.42, 0.30, tire_mat), (0.24, 0.315, rim_mat)):
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=18,
            radius=radius,
            depth=depth,
            location=(x, y, z),
            rotation=(0.0, math.radians(90.0), 0.0),
        )
        obj = bpy.context.active_object
        obj.data.materials.append(material)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        parts.append(obj)

    bpy.ops.object.select_all(action="DESELECT")
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    obj = bpy.context.active_object
    obj.name = name
    obj.location = (x, y, z)
    bpy.context.scene.cursor.location = (x, y, z)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    OBJECTS.append(obj)
    return obj


def add_preview(scene):
    floor_mat = material("PreviewFloor", (0.12, 0.13, 0.15), 0.0, 0.9)
    bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, -0.01))
    floor = bpy.context.active_object
    floor.data.materials.append(floor_mat)

    cam_data = bpy.data.cameras.new("TruckPreviewCamera")
    cam = bpy.data.objects.new("TruckPreviewCamera", cam_data)
    scene.collection.objects.link(cam)
    cam.location = (7.5, 9.0, 4.8)
    cam.rotation_euler = (Vector((0.0, 0.0, 1.1)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = 50
    scene.camera = cam

    sun_data = bpy.data.lights.new("TruckSun", "SUN")
    sun_data.energy = 4.0
    sun_data.angle = math.radians(10)
    sun = bpy.data.objects.new("TruckSun", sun_data)
    scene.collection.objects.link(sun)
    sun.location = (6, 8, 10)
    sun.rotation_euler = (Vector((0, 0, 1)) - sun.location).to_track_quat("-Z", "Y").to_euler()

    area_data = bpy.data.lights.new("TruckFill", "AREA")
    area_data.energy = 350
    area_data.size = 6
    area = bpy.data.objects.new("TruckFill", area_data)
    scene.collection.objects.link(area)
    area.location = (-5, 4, 6)
    area.rotation_euler = (Vector((0, 0, 1)) - area.location).to_track_quat("-Z", "Y").to_euler()

    world = bpy.data.worlds.new("TruckWorld")
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (0.018, 0.026, 0.038, 1.0)
    bg.inputs["Strength"].default_value = 1.0
    scene.world = world

    scene.render.resolution_x = 1100
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

    paint = material("TruckPaint", (0.035, 0.16, 0.30), 0.55, 0.35)
    paint_light = material("TruckPaintLight", (0.70, 0.74, 0.78), 0.35, 0.4)
    cargo = material("TruckCargo", (0.72, 0.74, 0.77), 0.2, 0.55)
    cargo_blue = material("TruckCargoStripe", (0.035, 0.16, 0.30), 0.4, 0.45)
    dark = material("TruckDark", (0.018, 0.022, 0.028), 0.55, 0.5)
    glass = material("TruckGlass", (0.035, 0.10, 0.14), 0.0, 0.05, alpha=0.22, transparent=True)
    tire = material("TruckTire", (0.010, 0.011, 0.012), 0.0, 0.85)
    rim = material("TruckRim", (0.42, 0.45, 0.48), 0.75, 0.32)
    headlight = material("TruckHeadlight", (0.9, 0.9, 0.8), 0.1, 0.2)
    headlight.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (1.0, 0.92, 0.72, 1.0)
    headlight.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 3.0
    taillight = material("TruckTaillight", (0.35, 0.02, 0.015), 0.1, 0.35)
    taillight.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (1.0, 0.05, 0.02, 1.0)
    taillight.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 2.0

    # Chassis, cab shell, roof. The upper cab is an open frame so the glass is
    # genuinely see-through from inside and outside.
    box("Chassis", (1.75, 5.35, 0.22), (0, 0, 0.62), dark, 0.02)
    box("CabLower", (1.9, 1.9, 1.0), (0, 1.75, 1.15), paint, 0.03)
    box("CabRearWall", (1.8, 0.08, 0.8), (0, 1.02, 2.05), paint, 0.01)
    box("CabRoof", (1.9, 1.62, 0.10), (0, 1.75, 2.53), paint, 0.02)
    box("CabFrontSill", (1.86, 0.08, 0.12), (0, 2.50, 1.70), paint, 0.01)

    for sx in (-1, 1):
        box("CabSideSill", (0.07, 1.42, 0.12), (sx * 0.93, 1.75, 1.70), paint, 0.01)
        box("CabPillarFront", (0.09, 0.09, 0.78), (sx * 0.91, 2.45, 2.08), paint, 0.01)
        box("CabPillarRear", (0.09, 0.09, 0.78), (sx * 0.91, 1.06, 2.08), paint, 0.01)

    # Glass: windshield, side windows. They sit in the open cab frame.
    box("Windshield", (1.62, 0.025, 0.68), (0, 2.545, 2.08), glass)
    box("SideWindow_L", (0.025, 1.32, 0.62), (-0.932, 1.75, 2.05), glass)
    box("SideWindow_R", (0.025, 1.32, 0.62), (0.932, 1.75, 2.05), glass)

    # Front details.
    box("Grille", (1.42, 0.07, 0.32), (0, 2.665, 1.22), dark)
    box("Bumper", (1.96, 0.18, 0.26), (0, 2.70, 0.58), dark, 0.02)
    box("Headlight_L", (0.34, 0.06, 0.18), (-0.58, 2.67, 0.98), headlight, 0.01)
    box("Headlight_R", (0.34, 0.06, 0.18), (0.58, 2.67, 0.98), headlight, 0.01)
    box("LicensePlate", (0.42, 0.03, 0.16), (0, 2.675, 0.70), paint_light)

    # Mirrors.
    for sx in (-1, 1):
        box("MirrorArm", (0.18, 0.05, 0.05), (sx * 1.03, 2.18, 2.12), dark)
        box("MirrorHead", (0.07, 0.18, 0.26), (sx * 1.14, 2.18, 2.06), dark, 0.01)

    # Cargo box.
    box("CargoBox", (2.0, 3.3, 1.75), (0, -1.10, 1.68), cargo, 0.02)
    box("CargoStripe", (2.015, 3.31, 0.28), (0, -1.10, 0.98), cargo_blue)
    for sx in (-1, 1):
        for y in (-2.4, -1.5, -0.5):
            box("CargoRib", (0.018, 0.07, 1.55), (sx * 1.012, y, 1.68), cargo_blue)
    box("RearDoor_L", (0.95, 0.035, 1.58), (-0.49, -2.765, 1.68), cargo)
    box("RearDoor_R", (0.95, 0.035, 1.58), (0.49, -2.765, 1.68), cargo)
    box("RearSeam", (0.02, 0.045, 1.58), (0, -2.765, 1.68), dark)
    box("RearBumper", (1.96, 0.16, 0.22), (0, -2.79, 0.55), dark, 0.02)
    box("TailLight_L", (0.28, 0.05, 0.16), (-0.72, -2.80, 0.88), taillight)
    box("TailLight_R", (0.28, 0.05, 0.16), (0.72, -2.80, 0.88), taillight)

    # Door handles and hinges for the cab.
    for sx in (-1, 1):
        box("DoorHandle", (0.16, 0.035, 0.05), (sx * 0.96, 1.22, 1.62), dark)
        box("DoorSeam", (0.015, 0.04, 1.35), (sx * 0.955, 0.82, 1.45), dark)

    # Interior dashboard and steering wheel (visible from cab camera).
    box("Dashboard", (1.72, 0.42, 0.17), (0, 2.22, 1.55), dark, 0.02)
    bpy.ops.mesh.primitive_torus_add(
        major_radius=0.18,
        minor_radius=0.025,
        major_segments=16,
        minor_segments=6,
        location=(-0.42, 1.95, 1.56),
        rotation=(math.radians(70), 0, 0),
    )
    steering = bpy.context.active_object
    steering.name = "SteeringWheel"
    steering.data.materials.append(dark)
    OBJECTS.append(steering)

    # Wheels.
    wheel("Wheel_FL", -0.93, 1.72, 0.42, tire, rim)
    wheel("Wheel_FR", 0.93, 1.72, 0.42, tire, rim)
    wheel("Wheel_RL", -0.93, -1.72, 0.42, tire, rim)
    wheel("Wheel_RR", 0.93, -1.72, 0.42, tire, rim)

    # Underbody details.
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=12, radius=0.20, depth=0.95, location=(0.98, -0.65, 0.58), rotation=(math.radians(90), 0, 0)
    )
    tank = bpy.context.active_object
    tank.name = "FuelTank"
    tank.data.materials.append(rim)
    OBJECTS.append(tank)

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
