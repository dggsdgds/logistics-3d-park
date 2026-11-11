import bpy
import bmesh
import math
import os
import time

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "assets", "container_lod.glb")

L = 12.192
W = 2.438
H = 2.591
HALF_L = L / 2.0
HALF_W = W / 2.0
HALF_H = H / 2.0

BODY = []
HW = []


def log(*args):
    print("LOD:", *args, flush=True)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system = "METRIC"


def mat(name, color, metallic, roughness):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.use_backface_culling = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return m


def box(name, size, loc, material, group=BODY):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    group.append(obj)
    return obj


def cylinder(name, radius, depth, loc, material, vertices=6, group=HW):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.materials.append(material)
    group.append(obj)
    return obj


def finish(obj, thickness=0.0):
    if thickness:
        m = obj.modifiers.new("Shell", "SOLIDIFY")
        m.thickness = thickness
        m.offset = 0.0
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=m.name)

    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


def panel(name, cols, rows, pos, material, group=BODY):
    verts = [pos(i, j) for j in range(rows) for i in range(cols)]
    faces = []
    for j in range(rows - 1):
        for i in range(cols - 1):
            a = j * cols + i
            faces.append((a, a + 1, a + cols + 1, a + cols))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.validate()
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    finish(obj, 0.010)
    group.append(obj)
    return obj


def wave(i, seg=4):
    return [0.0, 1.0, 1.0, 0.0][i % seg]


def build_panels(material):
    # Long sides
    for side in (-1, 1):
        x0 = side * (HALF_W - 0.045)
        y0 = -HALF_L + 0.17
        y1 = HALF_L - 0.17
        z0 = -HALF_H + 0.17
        z1 = HALF_H - 0.17
        ribs = 16
        seg = 4
        cols = ribs * seg + 1

        def pos(i, j, side=side, x0=x0, y0=y0, y1=y1, z0=z0, z1=z1, cols=cols):
            t = i / (cols - 1)
            return (x0 + side * wave(i, seg) * 0.03, y0 + (y1 - y0) * t, z0 + (z1 - z0) * j)

        panel("SideL" if side < 0 else "SideR", cols, 2, pos, material)

    # Front wall
    y0 = -HALF_L + 0.045
    x0 = -HALF_W + 0.17
    x1 = HALF_W - 0.17
    z0 = -HALF_H + 0.17
    z1 = HALF_H - 0.17
    ribs = 4
    seg = 4
    cols = ribs * seg + 1

    def front_pos(i, j):
        t = i / (cols - 1)
        return (x0 + (x1 - x0) * t, y0 - wave(i, seg) * 0.025, z0 + (z1 - z0) * j)

    panel("Front", cols, 2, front_pos, material)

    # Doors
    door_y = HALF_L - 0.045
    for side in (-1, 1):
        dx0 = (-HALF_W + 0.17) if side < 0 else 0.012
        dx1 = -0.012 if side < 0 else (HALF_W - 0.17)
        ribs = 2
        cols = ribs * seg + 1

        def door_pos(i, j, dx0=dx0, dx1=dx1):
            t = i / (cols - 1)
            return (dx0 + (dx1 - dx0) * t, door_y + wave(i, seg) * 0.018, z0 + (z1 - z0) * j)

        panel("DoorL" if side < 0 else "DoorR", cols, 2, door_pos, material)


def build_structure(body_mat, hw_mat):
    for sx in (-1, 1):
        for sy in (-1, 1):
            box("Post", (0.16, 0.16, H - 0.02), (sx * (HALF_W - 0.08), sy * (HALF_L - 0.08), 0), body_mat)

    for sx in (-1, 1):
        for sz in (-1, 1):
            box("SideRail", (0.16, L - 0.16, 0.16), (sx * (HALF_W - 0.08), 0, sz * (HALF_H - 0.08)), body_mat)

    for sy in (-1, 1):
        for sz in (-1, 1):
            box("EndRail", (W - 0.16, 0.16, 0.16), (0, sy * (HALF_L - 0.08), sz * (HALF_H - 0.08)), body_mat)

    box("Roof", (W - 0.24, L - 0.24, 0.08), (0, 0, HALF_H - 0.05), body_mat)

    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                box(
                    "Casting",
                    (0.22, 0.18, 0.14),
                    (sx * (HALF_W - 0.09), sy * (HALF_L - 0.09), sz * (HALF_H - 0.07)),
                    hw_mat,
                    HW,
                )

    for x in [-0.98, -0.70, -0.40, -0.10, 0.10, 0.40, 0.70, 0.98]:
        cylinder("Bar", 0.02, 1.9, (x, HALF_L + 0.03, 0), hw_mat, 6)

    for x in (-1.03, 1.03):
        for z in (-0.9, 0.0, 0.9):
            box("Hinge", (0.075, 0.06, 0.18), (x, HALF_L + 0.02, z), hw_mat, HW)


def join(objs, name):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    obj = bpy.context.active_object
    obj.name = name
    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    return obj


def main():
    start = time.time()
    reset()
    body_mat = mat("ContainerPaint_LOD", (0.82, 0.82, 0.82), 0.8, 0.6)
    hw_mat = mat("ContainerHardware_LOD", (0.035, 0.042, 0.05), 0.85, 0.38)

    build_panels(body_mat)
    build_structure(body_mat, hw_mat)

    body = join(BODY, "ContainerBody")
    hw = join(HW, "ContainerHardware")
    log("body polys", len(body.data.polygons), "hardware polys", len(hw.data.polygons))

    bpy.ops.object.select_all(action="DESELECT")
    body.select_set(True)
    hw.select_set(True)
    bpy.context.view_layer.objects.active = body

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
    log("saved", OUT, os.path.getsize(OUT), "bytes in", round(time.time() - start, 2), "sec")


if __name__ == "__main__":
    main()
