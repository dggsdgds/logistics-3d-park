import bpy
import bmesh
import math
import os
import time
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "assets", "container.glb")
PREVIEW = os.path.join(HERE, "container_preview.png")
TEX_DIR = os.path.join(HERE, "textures")

L = 12.192
W = 2.438
H = 2.591
HALF_L = L / 2.0
HALF_W = W / 2.0
HALF_H = H / 2.0

BODY_OBJECTS = []
HW_OBJECTS = []


def log(*args):
    print("CONTAINER:", *args, flush=True)


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 24
    scene.cycles.use_denoising = True
    return scene


def make_material(name, color, metallic, roughness):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.use_backface_culling = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def box(name, size, loc, mat, bevel=0.006, group=BODY_OBJECTS):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = (size[0], size[1], size[2])
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)

    if bevel and bevel > 0:
        mod = obj.modifiers.new("EdgeBevel", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        mod.limit_method = "ANGLE"
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)

    group.append(obj)
    return obj


def cylinder(name, radius, depth, loc, mat, rotation=(0.0, 0.0, 0.0), vertices=10, group=HW_OBJECTS):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices,
        radius=radius,
        depth=depth,
        location=loc,
        rotation=rotation,
    )
    obj = bpy.context.active_object
    obj.name = name
    obj.data.materials.append(mat)
    group.append(obj)
    return obj


def finish_mesh(obj, thickness):
    if thickness and thickness > 0:
        mod = obj.modifiers.new("Shell", "SOLIDIFY")
        mod.thickness = thickness
        mod.offset = 0.0
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)

    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()


def panel(name, cols, rows, pos, mat, thickness=0.012, group=BODY_OBJECTS):
    verts = []
    for j in range(rows):
        for i in range(cols):
            verts.append(pos(i, j))

    faces = []
    for j in range(rows - 1):
        for i in range(cols - 1):
            a = j * cols + i
            b = a + 1
            c = a + cols + 1
            d = a + cols
            faces.append((a, b, c, d))

    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.validate()
    mesh.update()

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    finish_mesh(obj, thickness)
    group.append(obj)
    return obj


def wave_profile(i, segments=6):
    phase = i % segments
    return [0.0, 0.5, 1.0, 1.0, 0.5, 0.0][phase]


def build_corrugated_panels(body_mat):
    # Long sides: ribs run vertically, wave along Y.
    for side in (-1, 1):
        x0 = side * (HALF_W - 0.045)
        y0 = -HALF_L + 0.17
        y1 = HALF_L - 0.17
        z0 = -HALF_H + 0.17
        z1 = HALF_H - 0.17
        ribs = 40
        seg = 6
        cols = ribs * seg + 1

        def pos(i, j, side=side, x0=x0, y0=y0, y1=y1, z0=z0, z1=z1, cols=cols, seg=seg):
            t = i / (cols - 1)
            depth = wave_profile(i, seg)
            return (
                x0 + side * depth * 0.028,
                y0 + (y1 - y0) * t,
                z0 + (z1 - z0) * j,
            )

        panel("SideWall_L" if side < 0 else "SideWall_R", cols, 2, pos, body_mat, 0.012)

    # Front (non-door) end wall.
    y0 = -HALF_L + 0.045
    x0 = -HALF_W + 0.17
    x1 = HALF_W - 0.17
    z0 = -HALF_H + 0.17
    z1 = HALF_H - 0.17
    ribs = 8
    seg = 6
    cols = ribs * seg + 1

    def front_pos(i, j):
        t = i / (cols - 1)
        depth = wave_profile(i, seg)
        return (
            x0 + (x1 - x0) * t,
            y0 - depth * 0.025,
            z0 + (z1 - z0) * j,
        )

    panel("FrontWall", cols, 2, front_pos, body_mat, 0.012)

    # Two door leaves, each with shallow corrugation.
    door_z0 = -HALF_H + 0.17
    door_z1 = HALF_H - 0.17
    door_y = HALF_L - 0.045
    door_ribs = 4
    door_cols = door_ribs * seg + 1

    for side in (-1, 1):
        dx0 = -0.012 if side < 0 else 0.012
        dx1 = (-HALF_W + 0.17) if side < 0 else (HALF_W - 0.17)
        if side > 0:
            dx0, dx1 = 0.012, HALF_W - 0.17
        else:
            dx0, dx1 = -HALF_W + 0.17, -0.012

        def door_pos(i, j, dx0=dx0, dx1=dx1):
            t = i / (door_cols - 1)
            depth = wave_profile(i, seg)
            return (
                dx0 + (dx1 - dx0) * t,
                door_y + depth * 0.018,
                door_z0 + (door_z1 - door_z0) * j,
            )

        panel("Door_L" if side < 0 else "Door_R", door_cols, 2, door_pos, body_mat, 0.028)

    # Roof: shallow transverse ribs.
    rx0 = -HALF_W + 0.17
    rx1 = HALF_W - 0.17
    ry0 = -HALF_L + 0.17
    ry1 = HALF_L - 0.17
    roof_ribs = 10
    roof_cols = roof_ribs * seg + 1
    roof_z = HALF_H - 0.04

    def roof_pos(i, j):
        t = i / (roof_cols - 1)
        depth = wave_profile(i, seg)
        return (
            rx0 + (rx1 - rx0) * t,
            ry0 + (ry1 - ry0) * j,
            roof_z + depth * 0.010,
        )

    panel("Roof", roof_cols, 2, roof_pos, body_mat, 0.012)


def build_structure(body_mat, hardware_mat):
    # Corner posts.
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(
                "CornerPost",
                (0.16, 0.16, H - 0.02),
                (sx * (HALF_W - 0.08), sy * (HALF_L - 0.08), 0),
                body_mat,
                0.008,
            )

    # Side rails (top and bottom).
    for sx in (-1, 1):
        for sz in (-1, 1):
            box(
                "SideRail",
                (0.16, L - 0.16, 0.16),
                (sx * (HALF_W - 0.08), 0, sz * (HALF_H - 0.08)),
                body_mat,
                0.008,
            )

    # End rails.
    for sy in (-1, 1):
        for sz in (-1, 1):
            box(
                "EndRail",
                (W - 0.16, 0.16, 0.16),
                (0, sy * (HALF_L - 0.08), sz * (HALF_H - 0.08)),
                body_mat,
                0.008,
            )

    # Floor panel (mostly hidden, closes the box).
    box("Floor", (W - 0.28, L - 0.28, 0.06), (0, 0, -HALF_H + 0.06), body_mat, 0.004)

    # ISO corner castings.
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                box(
                    "CornerCasting",
                    (0.22, 0.18, 0.14),
                    (sx * (HALF_W - 0.09), sy * (HALF_L - 0.09), sz * (HALF_H - 0.07)),
                    hardware_mat,
                    0.01,
                    HW_OBJECTS,
                )

    # Door locking bars, guides, handles and hinges.
    bar_x = [-0.98, -0.70, -0.40, -0.10, 0.10, 0.40, 0.70, 0.98]
    for i, x in enumerate(bar_x):
        cylinder("LockBar", 0.018, 1.92, (x, HALF_L + 0.035, 0), hardware_mat, vertices=10)
        for z in (-0.95, 0.0, 0.95):
            box(
                "BarGuide",
                (0.065, 0.045, 0.09),
                (x, HALF_L + 0.025, z),
                hardware_mat,
                0.004,
                HW_OBJECTS,
            )
        direction = -1.0 if x < 0 else 1.0
        cylinder(
            "DoorHandle",
            0.016,
            0.26,
            (x + direction * 0.11, HALF_L + 0.095, 0.32),
            hardware_mat,
            rotation=(0.0, math.radians(90), 0.0),
            vertices=8,
        )

    for x in (-1.03, 1.03):
        for z in (-0.9, 0.0, 0.9):
            box(
                "DoorHinge",
                (0.075, 0.06, 0.18),
                (x, HALF_L + 0.02, z),
                hardware_mat,
                0.005,
                HW_OBJECTS,
            )

    # Center door gasket.
    box("DoorGasket", (0.018, 0.03, 2.22), (0, HALF_L + 0.005, 0), hardware_mat, 0.002, HW_OBJECTS)

    # Small ventilation panels high on both sides.
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(
                "Vent",
                (0.035, 0.34, 0.2),
                (sx * (HALF_W - 0.02), sy * (HALF_L - 1.2), 0.82),
                hardware_mat,
                0.004,
                HW_OBJECTS,
            )


def join_objects(objs, name):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objs:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    result = bpy.context.active_object
    result.name = name

    bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    return result


def make_body_material():
    mat = bpy.data.materials.new("ContainerPaint")
    mat.use_nodes = True
    mat.use_backface_culling = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    bsdf.inputs["Metallic"].default_value = 0.8
    bsdf.inputs["Roughness"].default_value = 0.6

    texcoord = nodes.new("ShaderNodeTexCoord")
    separate = nodes.new("ShaderNodeSeparateXYZ")
    links.new(texcoord.outputs["Generated"], separate.inputs["Vector"])

    # Grime gathers near the bottom door rail.
    height_ramp = nodes.new("ShaderNodeValToRGB")
    height_ramp.color_ramp.elements[0].position = 0.0
    height_ramp.color_ramp.elements[0].color = (1.0, 1.0, 1.0, 1.0)
    height_ramp.color_ramp.elements[1].position = 0.3
    height_ramp.color_ramp.elements[1].color = (0.0, 0.0, 0.0, 1.0)
    links.new(separate.outputs["Z"], height_ramp.inputs["Fac"])

    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 4.2
    noise.inputs["Detail"].default_value = 8.0
    noise.inputs["Roughness"].default_value = 0.62
    noise.inputs["Distortion"].default_value = 0.15

    grime_ramp = nodes.new("ShaderNodeValToRGB")
    grime_ramp.color_ramp.elements[0].position = 0.42
    grime_ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    grime_ramp.color_ramp.elements[1].position = 0.7
    grime_ramp.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
    links.new(noise.outputs["Fac"], grime_ramp.inputs["Fac"])

    mask_mul = nodes.new("ShaderNodeMath")
    mask_mul.operation = "MULTIPLY"
    links.new(height_ramp.outputs["Color"], mask_mul.inputs[0])
    links.new(grime_ramp.outputs["Color"], mask_mul.inputs[1])

    mask_scale = nodes.new("ShaderNodeMath")
    mask_scale.operation = "MULTIPLY"
    mask_scale.inputs[1].default_value = 0.6
    links.new(mask_mul.outputs[0], mask_scale.inputs[0])

    mix = nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "MIX"
    mix.inputs["Color1"].default_value = (0.82, 0.82, 0.82, 1.0)
    mix.inputs["Color2"].default_value = (0.20, 0.075, 0.032, 1.0)
    links.new(mask_scale.outputs[0], mix.inputs["Fac"])
    links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])

    # Fine paint / steel grain for the baked normal map.
    micro_noise = nodes.new("ShaderNodeTexNoise")
    micro_noise.inputs["Scale"].default_value = 60.0
    micro_noise.inputs["Detail"].default_value = 5.0
    micro_noise.inputs["Roughness"].default_value = 0.55

    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.16
    bump.inputs["Distance"].default_value = 0.006
    links.new(micro_noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

    return mat


def uv_unwrap(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(
        angle_limit=math.radians(66.0),
        island_margin=0.003,
        area_weight=0.0,
        correct_aspect=True,
        scale_to_bounds=False,
    )
    bpy.ops.object.mode_set(mode="OBJECT")
    log("UV maps:", [uv.name for uv in obj.data.uv_layers])


def bake_body_textures(body, mat):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 2
    scene.cycles.use_denoising = False
    scene.render.bake.margin = 8
    scene.render.bake.use_selected_to_active = False
    scene.render.bake.max_ray_distance = 0.0

    os.makedirs(TEX_DIR, exist_ok=True)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")

    bpy.ops.object.select_all(action="DESELECT")
    body.select_set(True)
    bpy.context.view_layer.objects.active = body

    # ---- Base colour -------------------------------------------------
    base_img = bpy.data.images.new("ContainerBaseColor", width=2048, height=2048, alpha=False)
    base_img.colorspace_settings.name = "sRGB"
    base_node = nodes.new("ShaderNodeTexImage")
    base_node.image = base_img
    base_node.select = True
    nodes.active = base_node

    bsdf.inputs["Metallic"].default_value = 0.0
    log("Baking base colour...")
    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"COLOR"}, use_clear=True, margin=8)
    bsdf.inputs["Metallic"].default_value = 0.8

    base_path = os.path.join(TEX_DIR, "container_basecolor.png")
    base_img.filepath_raw = base_path
    base_img.file_format = "PNG"
    base_img.save()
    base_img.pack()
    log("Base colour saved", base_path, os.path.getsize(base_path), "bytes")

    # Replace the procedural colour with the baked map.
    for link in list(bsdf.inputs["Base Color"].links):
        links.remove(link)
    links.new(base_node.outputs["Color"], bsdf.inputs["Base Color"])

    # Material parameters requested for the container steel.
    bsdf.inputs["Metallic"].default_value = 0.8
    bsdf.inputs["Roughness"].default_value = 0.6


def add_preview(scene):
    # Floor.
    floor_mat = make_material("PreviewFloor", (0.12, 0.13, 0.15), 0.0, 0.85)
    bpy.ops.mesh.primitive_plane_add(size=50, location=(0, 0, -HALF_H - 0.01))
    floor = bpy.context.active_object
    floor.name = "PreviewFloor"
    floor.data.materials.append(floor_mat)

    # Camera.
    cam_data = bpy.data.cameras.new("PreviewCamera")
    cam = bpy.data.objects.new("PreviewCamera", cam_data)
    scene.collection.objects.link(cam)
    cam.location = (11.0, 14.5, 7.0)
    direction = Vector((0.0, 0.0, 0.0)) - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = 42
    scene.camera = cam

    # Sun.
    sun_data = bpy.data.lights.new("PreviewSun", "SUN")
    sun_data.energy = 4.0
    sun_data.angle = math.radians(8)
    sun = bpy.data.objects.new("PreviewSun", sun_data)
    scene.collection.objects.link(sun)
    sun.location = (7, 9, 12)
    sun.rotation_euler = (Vector((0, 0, 0)) - sun.location).to_track_quat("-Z", "Y").to_euler()

    # Fill area.
    area_data = bpy.data.lights.new("PreviewFill", "AREA")
    area_data.energy = 450
    area_data.size = 7
    area = bpy.data.objects.new("PreviewFill", area_data)
    scene.collection.objects.link(area)
    area.location = (-6, 6, 8)
    area.rotation_euler = (Vector((0, 0, 0)) - area.location).to_track_quat("-Z", "Y").to_euler()

    # World.
    world = bpy.data.worlds.new("PreviewWorld")
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
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.cycles.samples = 24
    scene.cycles.use_denoising = True

    log("Rendering preview...")
    bpy.ops.render.render(write_still=True)
    log("Preview saved", PREVIEW)


def main():
    start = time.time()
    reset_scene()
    body_mat = make_body_material()
    hardware_mat = make_material("ContainerHardware", (0.035, 0.042, 0.05), 0.85, 0.38)

    build_corrugated_panels(body_mat)
    build_structure(body_mat, hardware_mat)

    body = join_objects(BODY_OBJECTS, "ContainerBody")
    hardware = join_objects(HW_OBJECTS, "ContainerHardware")
    log("Body verts", len(body.data.vertices), "polys", len(body.data.polygons))
    log("Hardware verts", len(hardware.data.vertices), "polys", len(hardware.data.polygons))

    uv_unwrap(body)
    bake_body_textures(body, body_mat)

    add_preview(bpy.context.scene)

    bpy.ops.object.select_all(action="DESELECT")
    body.select_set(True)
    hardware.select_set(True)
    bpy.context.view_layer.objects.active = body

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=OUT,
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_texcoords=True,
        export_normals=True,
        export_materials="EXPORT",
        export_cameras=False,
        export_lights=False,
    )
    log("GLB saved", OUT, os.path.getsize(OUT), "bytes")
    log("DONE in", round(time.time() - start, 2), "sec")


if __name__ == "__main__":
    main()
