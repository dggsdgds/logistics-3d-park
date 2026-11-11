import bpy
import math
import os
import time
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "assets", "gas_station.glb")
PREVIEW = os.path.join(HERE, "gas_station_preview.png")
OBJECTS = []


def log(*args):
    print("STATION:", *args, flush=True)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    return scene


def material(name, color, metallic, roughness):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.use_backface_culling = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return m


def emissive(name, color, strength=3.0):
    m = material(name, color, 0.0, 0.3)
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Emission Color"].default_value = (*color, 1.0)
    bsdf.inputs["Emission Strength"].default_value = strength
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


def cylinder(name, radius, depth, loc, mat, rotation=(0, 0, 0), vertices=12):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices, radius=radius, depth=depth, location=loc, rotation=rotation
    )
    obj = bpy.context.active_object
    obj.name = name
    obj.data.materials.append(mat)
    OBJECTS.append(obj)
    return obj


def add_preview(scene):
    floor_mat = material("PreviewFloor", (0.12, 0.13, 0.15), 0.0, 0.9)
    bpy.ops.mesh.primitive_plane_add(size=45, location=(0, 0, -0.01))
    floor = bpy.context.active_object
    floor.data.materials.append(floor_mat)

    cam_data = bpy.data.cameras.new("StationCamera")
    cam = bpy.data.objects.new("StationCamera", cam_data)
    scene.collection.objects.link(cam)
    cam.location = (15.0, 16.0, 9.0)
    cam.rotation_euler = (Vector((0.0, 0.0, 3.0)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = 45
    scene.camera = cam

    sun_data = bpy.data.lights.new("StationSun", "SUN")
    sun_data.energy = 4.0
    sun_data.angle = math.radians(10)
    sun = bpy.data.objects.new("StationSun", sun_data)
    scene.collection.objects.link(sun)
    sun.location = (7, 8, 12)
    sun.rotation_euler = (Vector((0, 0, 0)) - sun.location).to_track_quat("-Z", "Y").to_euler()

    area_data = bpy.data.lights.new("StationFill", "AREA")
    area_data.energy = 500
    area_data.size = 8
    area = bpy.data.objects.new("StationFill", area_data)
    scene.collection.objects.link(area)
    area.location = (-6, 6, 8)
    area.rotation_euler = (Vector((0, 0, 0)) - area.location).to_track_quat("-Z", "Y").to_euler()

    world = bpy.data.worlds.new("StationWorld")
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

    concrete = material("StationConcrete", (0.24, 0.26, 0.28), 0.0, 0.85)
    red = material("StationRed", (0.48, 0.045, 0.03), 0.35, 0.45)
    yellow = material("StationYellow", (0.85, 0.52, 0.03), 0.2, 0.4)
    white = material("StationWhite", (0.78, 0.80, 0.82), 0.2, 0.5)
    dark = material("StationDark", (0.025, 0.03, 0.035), 0.4, 0.55)
    glass = material("StationGlass", (0.06, 0.18, 0.25), 0.1, 0.08)
    glass.blend_method = "BLEND"
    glass.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = 0.35
    light = emissive("StationLight", (1.0, 0.92, 0.72), 3.0)

    # Pad and canopy.
    box("Pad", (17, 11, 0.18), (0, 0, 0.09), concrete)
    box("CanopyRoof", (12.5, 6.2, 0.35), (0, 0, 5.0), white, 0.04)
    box("CanopyFascia", (12.7, 0.5, 0.7), (0, -2.85, 4.95), red, 0.03)
    box("CanopyFascia2", (12.7, 0.5, 0.7), (0, 2.85, 4.95), red, 0.03)
    box("CanopyStripe", (12.4, 6.25, 0.12), (0, 0, 5.18), yellow)
    for x in (-5.2, 5.2):
        for y in (-2.4, 2.4):
            box("Column", (0.38, 0.38, 4.8), (x, y, 2.58), white, 0.02)
            box("ColumnBase", (0.7, 0.7, 0.35), (x, y, 0.32), red)

    # Ceiling light strips.
    for x in (-3.5, 0, 3.5):
        box("CeilingLight", (2.1, 0.25, 0.06), (x, 0, 4.80), light)

    # Pump islands and pumps.
    for x in (-2.5, 2.5):
        box("PumpIsland", (2.2, 0.75, 0.22), (x, 0, 0.2), concrete)
        box("PumpBody", (0.72, 0.55, 1.75), (x, -0.15, 1.1), white, 0.03)
        box("PumpTop", (0.8, 0.62, 0.18), (x, -0.15, 2.06), red)
        box("PumpScreen", (0.45, 0.03, 0.32), (x, 0.135, 1.42), dark)
        box("PumpScreenGlow", (0.37, 0.01, 0.22), (x, 0.152, 1.42), emissive("PumpScreen", (0.2, 0.8, 0.5), 2.0))
        box("PumpHose", (0.06, 0.06, 1.2), (x + 0.44, -0.05, 1.15), dark)
        box("PumpNozzle", (0.16, 0.1, 0.22), (x + 0.48, -0.05, 1.75), dark)

    # Small shop behind the canopy.
    box("Shop", (4.2, 3.0, 2.8), (0, -5.3, 1.4), white, 0.03)
    box("ShopRoof", (4.5, 3.3, 0.18), (0, -5.3, 2.9), red)
    box("ShopWindow", (3.1, 0.04, 1.35), (0, -3.78, 1.55), glass)
    box("ShopDoor", (0.8, 0.05, 1.9), (1.35, -3.77, 1.0), dark)
    box("ShopSign", (3.2, 0.06, 0.65), (0, -3.75, 2.55), red)
    box("ShopSignText", (2.7, 0.02, 0.35), (0, -3.71, 2.55), yellow)

    # Tall price sign, visible from the yard.
    cylinder("SignPole", 0.18, 7.0, (-6.8, -4.0, 3.5), dark, vertices=10)
    box("PriceSign", (2.5, 0.22, 2.4), (-6.8, -4.0, 7.4), red, 0.03)
    box("PriceSignBand", (2.3, 0.06, 0.55), (-6.8, -3.87, 8.0), yellow)
    box("PriceSignText", (1.4, 0.03, 0.45), (-6.8, -3.84, 7.45), white)

    # A few bollards at the entrance.
    for x in (-7.4, 7.4):
        for y in (-4.2, 4.2):
            cylinder("Bollard", 0.16, 0.9, (x, y, 0.45), yellow, vertices=10)

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
