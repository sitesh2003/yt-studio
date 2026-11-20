"""Reusable 3D shot templates for hero Shorts (20 Nov 2026).

Runs inside Blender:  blender -b --disable-autoexec --python shots.py -- --spec SPEC.json --shot N --out DIR
                      [--start F --end F] [--preview]
Each shot is built from scratch from open (CC0) models, so any shot, or any frame range of a shot, can
render on its own machine: the laptop, a GitHub runner, or Kaggle. World units are metres; scene 30 fps.

Templates (the "kind" of a shot in the spec): run_at_camera, size_tower, xray_scan, stress_run,
muscle_needed, speed_track, race_pass, closeup_roar. A creature is any rigged FBX/GLB with named
actions; its real length (m) and a planted-foot bone are in the spec, and its natural speed is MEASURED
from the foot, so feet never slide whatever the playback rate.
"""
import argparse
import json
import math
import os
import sys

import bpy
import mathutils
from mathutils import Vector

FPS = 30
A = argparse.ArgumentParser()
A.add_argument("--spec")
A.add_argument("--shot", type=int)
A.add_argument("--out")
A.add_argument("--start", type=int, default=0)
A.add_argument("--end", type=int, default=-1)
A.add_argument("--preview", action="store_true")
args = A.parse_args(sys.argv[sys.argv.index("--") + 1:])
SPEC = json.load(open(args.spec, encoding="utf-8"))
ASSETS = SPEC["assets_dir"]
SHOT = SPEC["shots"][args.shot]
N = int(round(SHOT["seconds"] * FPS))


# ---------------------------------------------------------------- scene, world, light
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.fps = FPS
    sc.render.resolution_x, sc.render.resolution_y = (540, 960) if args.preview else (1080, 1920)
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    try:
        sc.view_settings.view_transform = "AgX"
        sc.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        pass
    ee = sc.eevee
    for k, v in (("taa_render_samples", 16 if args.preview else 48), ("use_shadows", True),
                 ("shadow_ray_count", 2), ("use_raytracing", False)):
        try:
            setattr(ee, k, v)
        except Exception:
            pass
    sc.render.use_motion_blur = not args.preview and not os.environ.get("HERO_NO_BLUR")
    try:
        sc.render.motion_blur_shutter = 0.35
    except Exception:
        pass
    sc.frame_start, sc.frame_end = 1, N
    sc["xr"] = 0.0
    sc["stress"] = 0.0
    sc["bulk"] = 0.0
    return sc


def node(nt, kind, loc=(0, 0), **inputs):
    n = nt.nodes.new(kind)
    n.location = loc
    for k, v in inputs.items():
        n.inputs[k].default_value = v
    return n


def world(kind):
    w = bpy.data.worlds.new("W")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = node(nt, "ShaderNodeOutputWorld", (600, 0))
    bg = node(nt, "ShaderNodeBackground", (400, 0))
    tc = node(nt, "ShaderNodeTexCoord", (-400, 0))
    sep = node(nt, "ShaderNodeSeparateXYZ", (-200, 0))
    ramp = node(nt, "ShaderNodeValToRGB", (0, 0))
    mr = node(nt, "ShaderNodeMapRange", (-100, -150))
    mr.inputs["From Min"].default_value = -1.0
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], ramp.inputs[0])
    nt.links.new(ramp.outputs[0], bg.inputs[0])
    nt.links.new(bg.outputs[0], out.inputs[0])
    els = ramp.color_ramp.elements
    pal = {"day": [(0.0, (0.55, 0.62, 0.55, 1)), (0.5, (0.86, 0.90, 0.95, 1)), (0.62, (0.42, 0.62, 0.92, 1)),
                   (1.0, (0.12, 0.30, 0.75, 1))],
           "dusk": [(0.0, (0.15, 0.08, 0.12, 1)), (0.5, (1.0, 0.55, 0.25, 1)), (0.58, (0.85, 0.35, 0.40, 1)),
                    (1.0, (0.12, 0.08, 0.30, 1))],
           "sim": [(0.0, (0.004, 0.008, 0.02, 1)), (0.5, (0.02, 0.05, 0.10, 1)), (1.0, (0.0, 0.01, 0.03, 1))]}[kind]
    els[0].position, els[0].color = pal[0]
    els[1].position, els[1].color = pal[-1]
    for p, c in pal[1:-1]:
        e = els.new(p)
        e.color = c
    bg.inputs["Strength"].default_value = {"day": 1.0, "dusk": 0.9, "sim": 1.0}[kind]


def sun(strength, rot, color=(1, 0.96, 0.9)):
    d = bpy.data.lights.new("Sun", "SUN")
    d.energy = strength
    d.color = color
    d.angle = math.radians(3)
    o = bpy.data.objects.new("Sun", d)
    bpy.context.collection.objects.link(o)
    o.rotation_euler = [math.radians(a) for a in rot]
    return o


def area(loc, rot, energy, color, size=8):
    d = bpy.data.lights.new("Area", "AREA")
    d.energy, d.color, d.size = energy, color, size
    o = bpy.data.objects.new("Area", d)
    bpy.context.collection.objects.link(o)
    o.location, o.rotation_euler = loc, [math.radians(a) for a in rot]
    return o


def mat(name, color, rough=0.6, emit=None, emit_strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = emit_strength
    return m


def box(name, size, loc, material):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = size
    o.data.materials.append(material)
    return o


def ground(kind):
    bpy.ops.mesh.primitive_plane_add(size=1200, location=(0, 0, 0))
    g = bpy.context.object
    if kind == "sim":
        m = bpy.data.materials.new("Grid")
        m.use_nodes = True
        nt = m.node_tree
        nt.nodes.clear()
        out = node(nt, "ShaderNodeOutputMaterial", (900, 0))
        tc = node(nt, "ShaderNodeTexCoord", (-700, 0))
        sc_ = node(nt, "ShaderNodeVectorMath", (-500, 0))
        sc_.operation = "SCALE"
        sc_.inputs["Scale"].default_value = 0.5            # a line every 2 m
        fr = node(nt, "ShaderNodeVectorMath", (-300, 0))
        fr.operation = "FRACTION"
        sub = node(nt, "ShaderNodeVectorMath", (-100, 0))
        sub.operation = "SUBTRACT"
        sub.inputs[1].default_value = (0.5, 0.5, 0.5)
        ab = node(nt, "ShaderNodeVectorMath", (100, 0))
        ab.operation = "ABSOLUTE"
        sep = node(nt, "ShaderNodeSeparateXYZ", (250, 0))
        mx = node(nt, "ShaderNodeMath", (400, 0))
        mx.operation = "MAXIMUM"
        gt = node(nt, "ShaderNodeMath", (550, 0))
        gt.operation = "GREATER_THAN"
        gt.inputs[1].default_value = 0.485
        em = node(nt, "ShaderNodeEmission", (550, -200))
        em.inputs["Color"].default_value = (0.1, 0.8, 1.0, 1)
        em.inputs["Strength"].default_value = 1.6
        dark = node(nt, "ShaderNodeBsdfPrincipled", (550, 250))
        dark.inputs["Base Color"].default_value = (0.01, 0.02, 0.04, 1)
        dark.inputs["Roughness"].default_value = 0.35
        mix = node(nt, "ShaderNodeMixShader", (750, 0))
        for a_, b_ in ((tc.outputs["Object"], sc_.inputs[0]), (sc_.outputs[0], fr.inputs[0]),
                       (fr.outputs[0], sub.inputs[0]), (sub.outputs[0], ab.inputs[0]), (ab.outputs[0], sep.inputs[0]),
                       (sep.outputs["X"], mx.inputs[0]), (sep.outputs["Y"], mx.inputs[1]), (mx.outputs[0], gt.inputs[0]),
                       (gt.outputs[0], mix.inputs[0]), (dark.outputs[0], mix.inputs[1]), (em.outputs[0], mix.inputs[2]),
                       (mix.outputs[0], out.inputs[0])):
            nt.links.new(a_, b_)
        g.data.materials.append(m)
        return g
    g.data.materials.append(mat("Grass", (0.20, 0.42, 0.14), 0.9))
    if kind == "road":
        asphalt = mat("Asphalt", (0.05, 0.05, 0.055), 0.8)
        white = mat("Line", (0.9, 0.9, 0.85), 0.5)
        box("Road", (11, 1200, 0.04), (0, 0, 0.02), asphalt)
        for x in (-5.2, 5.2):
            box("Edge", (0.18, 1200, 0.045), (x, 0, 0.025), white)
        d = box("Dash", (0.18, 3, 0.045), (0, -600, 0.025), white)
        ar = d.modifiers.new("A", "ARRAY")
        ar.count = 200
        ar.use_relative_offset = False
        ar.use_constant_offset = True
        ar.constant_offset_displace = (0, 6, 0)
        # trees and posts every so often, so speed reads against something
        trunk = mat("Trunk", (0.25, 0.15, 0.08))
        leaf = mat("Leaf", (0.12, 0.35, 0.10), 0.8)
        for i in range(-60, 60):
            for side in (-1, 1):
                x = side * ((10 if side < 0 else 15) + (i * 37 % 7))
                y = i * 9.0 + (i * 13 % 5)
                bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.25, depth=2.4, location=(x, y, 1.2))
                bpy.context.object.data.materials.append(trunk)
                bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1.6 + (i % 3) * 0.3,
                                                      location=(x, y, 3.4))
                bpy.context.object.data.materials.append(leaf)
    return g


# ---------------------------------------------------------------- creatures and props
def creature():
    c = SPEC["creature"]
    bpy.ops.import_scene.fbx(filepath=os.path.join(ASSETS, c["file"]))
    arm = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"][0]
    # the pack's actions also key the armature OBJECT (location/rotation/scale x3): drop those channels,
    # or every frame undoes our sizing and placement
    for act in bpy.data.actions:
        _strip_object_channels(act)
    if arm.animation_data:
        arm.animation_data.action = None
    mesh = [o for o in bpy.context.scene.objects if o.type == "MESH" and o.parent == arm][0]
    bpy.context.view_layer.update()
    bb = [mesh.matrix_world @ Vector(v) for v in mesh.bound_box]
    span = max(v[1] for v in bb) - min(v[1] for v in bb)
    f = c["length_m"] / span
    arm.scale = [s * f for s in arm.scale]
    arm.location = (0, 0, 0)
    for m in mesh.data.materials:      # flat game look, a little sheen
        b = m.node_tree.nodes.get("Principled BSDF") if m.use_nodes else None
        if b:
            b.inputs["Roughness"].default_value = 0.55
            b.inputs["Alpha"].default_value = 1.0      # the FBX import sets alpha 0 (invisible)
    bpy.context.view_layer.update()
    return arm, mesh, f


def _strip_object_channels(act):
    obj_paths = ("location", "rotation_euler", "rotation_quaternion", "scale")
    try:
        bags = [act]
        _ = act.fcurves
    except Exception:
        bags = [cb for layer in act.layers for st in layer.strips for cb in st.channelbags]
    for bag in bags:
        for fc in [fc for fc in bag.fcurves if fc.data_path in obj_paths]:
            bag.fcurves.remove(fc)


def action(name):
    return [a for a in bpy.data.actions if a.name.endswith(name)][0]


def natural_speed(arm, act, foot):
    """Metres per second the creature covers when the action plays at its own rate: the speed of the
    planted foot sliding backwards under the body (foot on the ground = within 3 cm of its lowest)."""
    sc = bpy.context.scene
    arm.animation_data_create()
    arm.animation_data.action = act
    try:
        arm.animation_data.action_slot = act.slots[0]
    except Exception:
        pass
    f0, f1 = [int(x) for x in act.frame_range]
    pts = []
    for fr in range(f0, f1 + 1):
        sc.frame_set(fr)
        p = arm.matrix_world @ arm.pose.bones[foot].head
        pts.append((p.y, p.z))
    zmin = min(z for _, z in pts)
    v = [abs(pts[i + 1][0] - pts[i][0]) for i in range(len(pts) - 1)
         if pts[i][1] < zmin + 0.03 and pts[i + 1][1] < zmin + 0.03]
    arm.animation_data.action = None
    sc.frame_set(1)
    return (sum(v) / len(v)) * 24.0 if v else 0.0          # the pack's actions are 24 fps


def play(arm, act_name, frame0, frame1, rate=1.0, track="base", blend="REPLACE"):
    """Loop an action from frame0 to frame1 at `rate` x its natural speed (scene is 30 fps, actions 24)."""
    act = action(act_name)
    ad = arm.animation_data or arm.animation_data_create()
    tr = ad.nla_tracks.new()
    tr.name = track
    a0, a1 = act.frame_range
    length = a1 - a0
    s = tr.strips.new(act_name, int(frame0), act)
    try:
        s.action_slot = act.slots[0]
    except Exception:
        pass
    s.scale = (FPS / 24.0) / rate
    s.repeat = max(1.0, (frame1 - frame0) / (length * s.scale))
    s.blend_type = blend
    s.extrapolation = "HOLD"
    return s


def key_path(obj, frames_locs):
    for fr, loc in frames_locs:
        obj.location = loc
        obj.keyframe_insert("location", frame=fr)
    if obj.animation_data and obj.animation_data.action:
        for fc in _fcurves(obj.animation_data.action):
            for k in fc.keyframe_points:
                k.interpolation = "LINEAR"


def _fcurves(act):
    try:
        return list(act.fcurves)
    except Exception:          # slotted actions (Blender 4.4+): curves live in layers/strips/channelbags
        out = []
        for layer in act.layers:
            for st in layer.strips:
                for cb in st.channelbags:
                    out += list(cb.fcurves)
        return out


def key_prop(frames_vals, prop):
    sc = bpy.context.scene
    for fr, v in frames_vals:
        sc[prop] = v
        sc.keyframe_insert(f'["{prop}"]', frame=fr)


def glb(file, length_m=None, loc=(0, 0, 0), rot_z=0.0):
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(ASSETS, file))
    new = [o for o in bpy.context.scene.objects if o not in before]
    root = bpy.data.objects.new("Prop", None)
    bpy.context.collection.objects.link(root)
    for o in new:
        if o.parent is None:
            o.parent = root
    bpy.context.view_layer.update()
    if length_m:
        pts = [o.matrix_world @ Vector(v) for o in new if o.type == "MESH" for v in o.bound_box]
        span = max(max(p[0] for p in pts) - min(p[0] for p in pts), max(p[1] for p in pts) - min(p[1] for p in pts))
        root.scale = [length_m / span] * 3
    root.location = loc
    root.rotation_euler = (0, 0, rot_z)
    return root, new


# ---------------------------------------------------------------- x-ray, bones, muscle
def _attr(nt, name, loc):
    a = nt.nodes.new("ShaderNodeAttribute")
    a.attribute_type = "VIEW_LAYER"
    a.attribute_name = name
    a.location = loc
    return a


def xray_skin(mesh, height):
    """Each skin material gets a scan line: below scene['xr'] x height the skin turns to a glassy blue
    shell; a bright line marks the scan front."""
    for m in mesh.data.materials:
        m.surface_render_method = "BLENDED"
        try:
            m.use_transparency_overlap = False
        except Exception:
            pass
        nt = m.node_tree
        out = [n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"][0]
        src = out.inputs["Surface"].links[0].from_socket
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        xr = _attr(nt, "xr", (-600, -400))
        th = nt.nodes.new("ShaderNodeMath")
        th.operation = "MULTIPLY"
        th.inputs[1].default_value = height * 1.15
        nt.links.new(xr.outputs["Fac"], th.inputs[0])
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(geo.outputs["Position"], sep.inputs[0])
        below = nt.nodes.new("ShaderNodeMath")
        below.operation = "LESS_THAN"
        nt.links.new(sep.outputs["Z"], below.inputs[0])
        nt.links.new(th.outputs[0], below.inputs[1])
        lw = nt.nodes.new("ShaderNodeLayerWeight")
        lw.inputs["Blend"].default_value = 0.35
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Color"].default_value = (0.25, 0.75, 1.0, 1)
        em.inputs["Strength"].default_value = 3.0
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        glass = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(lw.outputs["Facing"], glass.inputs[0])
        nt.links.new(tr.outputs[0], glass.inputs[1])
        nt.links.new(em.outputs[0], glass.inputs[2])
        # scan front: |z - th| < 0.06
        d = nt.nodes.new("ShaderNodeMath")
        d.operation = "SUBTRACT"
        nt.links.new(sep.outputs["Z"], d.inputs[0])
        nt.links.new(th.outputs[0], d.inputs[1])
        ad = nt.nodes.new("ShaderNodeMath")
        ad.operation = "ABSOLUTE"
        nt.links.new(d.outputs[0], ad.inputs[0])
        near = nt.nodes.new("ShaderNodeMath")
        near.operation = "LESS_THAN"
        near.inputs[1].default_value = 0.06
        nt.links.new(ad.outputs[0], near.inputs[0])
        line = nt.nodes.new("ShaderNodeEmission")
        line.inputs["Color"].default_value = (0.6, 1.0, 1.0, 1)
        line.inputs["Strength"].default_value = 12.0
        mix = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(below.outputs[0], mix.inputs[0])
        nt.links.new(src, mix.inputs[1])
        nt.links.new(glass.outputs[0], mix.inputs[2])
        mix2 = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(near.outputs[0], mix2.inputs[0])
        nt.links.new(mix.outputs[0], mix2.inputs[1])
        nt.links.new(line.outputs[0], mix2.inputs[2])
        nt.links.new(mix2.outputs[0], out.inputs["Surface"])


def bone_mat(stress=True):
    """Bones glow ivory-cyan; with stress=True they turn yellow then red as scene['stress'] rises."""
    m = bpy.data.materials.new("Bone" if stress else "BoneStill")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = node(nt, "ShaderNodeOutputMaterial", (600, 0))
    st = _attr(nt, "stress", (-400, 0))
    ramp = node(nt, "ShaderNodeValToRGB", (-150, 0))
    e = ramp.color_ramp.elements
    e[0].color = (0.85, 0.97, 1.0, 1)
    e[1].position, e[1].color = 1.0, (1.0, 0.05, 0.02, 1)
    mid = e.new(0.55)
    mid.color = (1.0, 0.75, 0.1, 1)
    em = node(nt, "ShaderNodeEmission", (200, 0))
    em.inputs["Strength"].default_value = 4.0
    if stress:
        nt.links.new(st.outputs["Fac"], ramp.inputs[0])
    nt.links.new(ramp.outputs[0], em.inputs["Color"])
    nt.links.new(em.outputs[0], out.inputs[0])
    return m


def muscle_mat():
    m = bpy.data.materials.new("Muscle")
    m.use_nodes = True
    m.surface_render_method = "BLENDED"
    nt = m.node_tree
    nt.nodes.clear()
    out = node(nt, "ShaderNodeOutputMaterial", (600, 0))
    lw = node(nt, "ShaderNodeLayerWeight", (-300, 0))
    lw.inputs["Blend"].default_value = 0.5
    em = node(nt, "ShaderNodeEmission", (0, -150))
    em.inputs["Color"].default_value = (1.0, 0.12, 0.18, 1)
    em.inputs["Strength"].default_value = 3.2
    tr = node(nt, "ShaderNodeBsdfTransparent", (0, 100))
    mix = node(nt, "ShaderNodeMixShader", (300, 0))
    add = node(nt, "ShaderNodeMath", (-100, 200))
    add.operation = "ADD"
    add.inputs[1].default_value = 0.6
    nt.links.new(lw.outputs["Facing"], add.inputs[0])
    nt.links.new(add.outputs[0], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0])
    return m


def _frame(axis):
    """Local z along the bone, local y as close to world-up as possible (forward for upright bones)."""
    ref = Vector((0, 0, 1)) if abs(axis.z) < 0.9 else Vector((0, -1, 0))
    x = ref.cross(axis).normalized()
    y = axis.cross(x).normalized()
    return mathutils.Matrix((x, y, axis)).transposed().to_4x4()


def attach(arm, bone_name, obj, along=0.5):
    """Put obj along a bone (0 = head, 1 = tail) in rest pose and parent it to that bone."""
    arm.data.pose_position = "REST"
    bpy.context.view_layer.update()
    pb = arm.pose.bones[bone_name]
    h = arm.matrix_world @ pb.head
    t = arm.matrix_world @ pb.tail
    mid = h.lerp(t, along)
    rot = _frame((t - h).normalized())
    mw = mathutils.Matrix.Translation(mid) @ rot @ mathutils.Matrix.Diagonal((*obj.scale, 1))
    obj.parent = arm
    obj.parent_type = "BONE"
    obj.parent_bone = bone_name
    bpy.context.view_layer.update()
    obj.matrix_world = mw
    arm.data.pose_position = "POSE"
    bpy.context.view_layer.update()
    return (t - h).length


def _blen(arm, name):
    pb = arm.pose.bones[name]
    return (pb.tail - pb.head).length * arm.matrix_world.to_scale()[0]


def piece(arm, bone, shape, dims, offset=(0, 0, 0), along=0.5, material=None, name="Part"):
    """One anatomical piece: a primitive sized dims (x lateral, y up, z along the bone), moved by offset
    in the bone's own frame, parented to the bone. Object scale stays 1, so a reveal can grow it from 0."""
    if shape == "cyl":
        bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.5, depth=1)
    elif shape == "box":
        bpy.ops.mesh.primitive_cube_add(size=1)
    elif shape == "cone":           # wide end at the bone's head, narrow toward its tail
        bpy.ops.mesh.primitive_cone_add(vertices=14, radius1=0.5, radius2=0.5 * dims[3], depth=1)
        dims = dims[:3]
    elif shape == "ring":
        bpy.ops.mesh.primitive_torus_add(major_radius=0.5, minor_radius=0.5 * dims[2], major_segments=28,
                                         minor_segments=8)
        dims = (dims[0], dims[1], 1.0)
    else:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=12, radius=0.5)
    o = bpy.context.object
    o.name = name
    o.data.transform(mathutils.Matrix.Translation(offset) @ mathutils.Matrix.Diagonal((*dims, 1)))
    if shape == "box":
        bev = o.modifiers.new("B", "BEVEL")
        bev.width, bev.segments = min(dims) * 0.25, 2
    if material:
        o.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    attach(arm, bone, o, along)
    return o


def _long_bone(arm, bone, r, mat_, nm):
    L = _blen(arm, bone)
    out = [piece(arm, bone, "cyl", (2 * r, 2 * r, L * 0.9), material=mat_, name=nm)]
    for end in (0.05, 0.95):             # knobbly joint ends, like a real long bone
        out.append(piece(arm, bone, "sph", (3.2 * r, 3.2 * r, 3.2 * r), along=end, material=mat_, name=nm + "_end"))
    return out


def _vertebrae(arm, bone, size, mat_, nm, spine_h=0.0, chevron=0.0):
    L = _blen(arm, bone)
    n = max(2, round(L / 0.3))
    out = []
    for i in range(n):
        a = (i + 0.5) / n
        out.append(piece(arm, bone, "box", (size, size, L / n * 0.72), along=a, material=mat_, name=nm))
        if spine_h:
            out.append(piece(arm, bone, "box", (size * 0.3, spine_h, L / n * 0.45),
                             (0, size * 0.5 + spine_h * 0.5, 0), along=a, material=mat_, name=nm + "_spine"))
        if chevron:
            out.append(piece(arm, bone, "box", (size * 0.25, chevron, L / n * 0.35),
                             (0, -size * 0.5 - chevron * 0.5, 0), along=a, material=mat_, name=nm + "_chevron"))
    return out


def skeleton(arm, c, stress_legs=False):
    """The whole skeleton as named groups, in the order the spec reveals them (bone by bone)."""
    still = bone_mat(stress=False)
    hot = bone_mat(stress=True) if stress_legs else still
    sides = (".L", ".R")
    g = {}
    g["FEET"] = sum((_long_bone(arm, "BackFoot" + s, 0.09, hot, "foot") for s in sides), [])
    g["SHINS"] = sum((_long_bone(arm, "BackLowLeg" + s, 0.10, hot, "shin") for s in sides), [])
    g["THIGHS"] = sum((_long_bone(arm, "BackUpLeg" + s, 0.13, hot, "femur") for s in sides), [])
    hips = [piece(arm, "BackLeg" + s, "cyl", (0.16, 0.16, _blen(arm, "BackLeg" + s) * 0.9), material=still,
                  name="socket") for s in sides]
    for x in (-0.3, 0.3):                # ilium plates, and the pubis that ends in a "boot"
        hips.append(piece(arm, "Hips", "box", (0.12, 0.75, 1.3), (x, 0.2, 0), material=still, name="ilium"))
    hips.append(piece(arm, "Hips", "box", (0.3, 1.5, 0.22), (0, -0.85, 0.15), material=still, name="pubis"))
    hips.append(piece(arm, "Hips", "box", (0.32, 0.18, 0.7), (0, -1.6, 0.0), material=still, name="pubic_boot"))
    g["HIPS"] = hips
    g["SPINE"] = sum((_vertebrae(arm, b, 0.24, still, "vert", spine_h=0.34)
                      for b in ("Back", "Hips", "Torso", "Shoulders")), [])
    ribs = []
    for b, n, r0, r1 in (("Torso", 5, 1.5, 1.25), ("Shoulders", 2, 1.1, 0.9)):
        for i in range(n):
            r = r0 + (r1 - r0) * i / max(1, n - 1)
            ribs.append(piece(arm, b, "ring", (r * 0.8, r, 0.06), (0, -r * 0.5, 0), along=(i + 0.5) / n,
                              material=still, name="rib"))
    g["RIBS"] = ribs
    g["NECK"] = _vertebrae(arm, "Neck", 0.2, still, "neck", spine_h=0.15)
    L = _blen(arm, "Head")
    dark = mat("Socket", (0.01, 0.02, 0.04), 0.5)
    skull = [piece(arm, "Head", "cone", (0.8, 0.95, L * 0.95, 0.38), (0, 0.1, 0), material=still, name="skull"),
             piece(arm, "Head", "cone", (0.62, 0.26, L * 0.9, 0.35), (0, -0.4, 0.04), material=still, name="jaw")]
    for x in (-0.33, 0.33):              # eye sockets, and the big openings behind them
        skull.append(piece(arm, "Head", "sph", (0.16, 0.2, 0.22), (x, 0.28, 0), along=0.28, material=dark, name="orbit"))
        skull.append(piece(arm, "Head", "sph", (0.12, 0.26, 0.3), (x * 1.05, 0.05, 0), along=0.12, material=dark,
                           name="fenestra"))
        for k in range(7):               # teeth along the upper jaw, pointing down
            a = 0.4 + k * 0.085
            skull.append(piece(arm, "Head", "cone", (0.07, 0.07, 0.2, 0.05), (x * 0.62 * (1 - (a - 0.4) * 0.8), -0.22, 0),
                               along=a, material=still, name="tooth"))
    for o in skull:
        if o.name.startswith("tooth"):   # turn each tooth to point down instead of along the bone
            o.data.transform(mathutils.Matrix.Rotation(math.radians(90), 4, "X"))
    g["SKULL"] = skull
    tail = []
    for k, b in enumerate(("Tail1", "Tail2", "Tail3", "Tail4", "Tail5")):
        sz = 0.24 * (1 - k * 0.15)
        tail += _vertebrae(arm, b, sz, still, "tailvert", spine_h=0.25 * (1 - k * 0.18),
                           chevron=0.25 * (1 - k * 0.2) if k < 4 else 0)
    g["TAIL"] = tail
    g["ARMS"] = sum((_long_bone(arm, b + s, 0.045, still, "arm") for s in sides
                     for b in ("FrontUpLeg", "FrontLowLeg", "FrontFoot")), [])
    return g


def muscle_groups(arm):
    """Real T. rex muscles as named groups, in the order the spec reveals them (muscle by muscle)."""
    m = muscle_mat()
    sides = ((".L", 1), (".R", -1))
    g = {}
    g["THIGH"] = [piece(arm, "BackUpLeg" + s, "sph", (0.9, 1.0, _blen(arm, "BackUpLeg" + s) * 0.85), along=0.42,
                        material=m, name="thigh") for s, _ in sides]
    g["CALF"] = [piece(arm, "BackLowLeg" + s, "sph", (0.45, 0.5, _blen(arm, "BackLowLeg" + s) * 0.8),
                       (0, -0.12, 0), along=0.35, material=m, name="calf") for s, _ in sides]
    # M. caudofemoralis longus: from the tail to the thigh bone, the big muscle that pulled each leg back
    g["TAIL-TO-THIGH"] = [piece(arm, "Tail1", "sph", (0.55, 0.65, _blen(arm, "Tail1") * 1.6), (k * 0.3, -0.35, 0),
                                along=0.45, material=m, name="caudofemoralis") for _, k in sides]
    g["NECK"] = [piece(arm, "Neck", "sph", (0.8, 0.9, _blen(arm, "Neck") * 1.4), (0, 0.05, 0), material=m,
                       name="neck_m")]
    g["JAW"] = [piece(arm, "Head", "sph", (0.55, 0.5, 0.6), (0, 0.15, 0), along=0.12, material=m, name="jaw_m")]
    return g


def reveal(objs, f):
    """Grow from nothing at frame f, with a little overshoot."""
    for o in objs:
        for fr, k in ((1, 0.0), (max(1, f - 1), 0.0), (f + 3, 1.18), (f + 6, 1.0)):
            o.scale = (k, k, k)
            o.keyframe_insert("scale", frame=fr)


def schedule(names, t0, t1):
    """Frame each named group appears at, evenly from t0 to t1 seconds into the shot (compose.py uses the same)."""
    n = len(names)
    return {nm: int(round((t0 + (t1 - t0) * i / max(1, n)) * FPS)) + 1 for i, nm in enumerate(names)}


# ---------------------------------------------------------------- camera
def camera(lens=32):
    cd = bpy.data.cameras.new("Cam")
    cd.lens = lens
    cd.clip_end = 3000
    cam = bpy.data.objects.new("Cam", cd)
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    tgt = bpy.data.objects.new("Target", None)
    bpy.context.collection.objects.link(tgt)
    c = cam.constraints.new("TRACK_TO")
    c.target = tgt
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"
    return cam, tgt


def smooth_keys(obj):
    if obj.animation_data and obj.animation_data.action:
        for fc in _fcurves(obj.animation_data.action):
            for k in fc.keyframe_points:
                k.interpolation = "BEZIER"
                k.easing = "EASE_IN_OUT"


# ---------------------------------------------------------------- the templates
def build():
    kind = SHOT["kind"]
    c = SPEC["creature"]
    look = SHOT.get("world", {"run_at_camera": "day", "size_tower": "day", "xray_scan": "sim",
                              "stress_run": "sim", "muscle_needed": "sim", "speed_track": "day",
                              "race_pass": "day", "closeup_roar": "dusk"}[kind])
    world(look)
    ground("sim" if look == "sim" else "road")
    if look == "day":
        sun(4.5, (50, 0, 35))
    elif look == "dusk":
        sun(3.0, (78, 0, -60), (1.0, 0.6, 0.35))
        area((8, -14, 6), (70, 0, 30), 2500, (1.0, 0.5, 0.3), 10)
    else:
        sun(0.6, (55, 0, 20), (0.6, 0.8, 1.0))
        area((-10, 6, 8), (60, 0, -120), 3000, (0.2, 0.6, 1.0), 12)
        area((10, -6, 6), (60, 0, 60), 1500, (1.0, 0.4, 0.6), 10)
    arm, mesh, f = creature()
    H = c["height_m"]
    walk, run = c["walk"], c["run"]
    v_walk = natural_speed(arm, action(walk), c["foot_bone"])
    v_run = natural_speed(arm, action(run), c["foot_bone"])
    print(f"natural speeds: walk {v_walk * 3.6:.1f} km/h, run {v_run * 3.6:.1f} km/h")
    cam, tgt = camera(SHOT.get("lens", 32))
    fwd = Vector((0, -1, 0))                                    # the creature faces -Y
    T = N / FPS

    if kind == "run_at_camera":
        hold = int(SHOT.get("freeze_s", 0.5) * FPS)
        stop = N - hold
        play(arm, run, 1, stop, 1.0)
        d = v_run * (stop / FPS)
        key_path(arm, [(1, Vector((0, d * 0.5, 0))), (stop, Vector((0, -d * 0.5, 0)))])
        # camera backs away slower than the runner, so it closes in; it stops dead on the freeze
        key_path(cam, [(1, Vector((1.8, d * 0.5 - 15, 0.8))), (stop, Vector((1.2, -d * 0.5 - 7.5, 0.6)))])
        key_path(tgt, [(1, Vector((0, d * 0.5, H * 0.6))), (stop, Vector((0, -d * 0.5, H * 0.62)))])
        for ad in (arm.animation_data,):
            ad.nla_tracks[0].strips[0].frame_end_ui = stop if hasattr(ad.nla_tracks[0].strips[0], "frame_end_ui") else stop

    elif kind == "size_tower":
        play(arm, c.get("idle", walk), 1, N, 1.0)
        arm.location = (0, 0, 0)
        arm.rotation_euler = (0, 0, math.radians(-25))
        cars = SHOT.get("cars", 6)
        step = max(4, int((N * 0.75) / cars))
        for i in range(cars):
            root, _ = glb(SPEC["props"]["car"], 4.5, (-10, 2, 0), math.radians(90 + (i % 2) * 8))
            z = i * 1.45
            f0 = 1 + i * step
            key_path(root, [(1, Vector((-10, 2, 60))), (f0, Vector((-10, 2, z + 14))),
                            (f0 + 6, Vector((-10, 2, z))), (f0 + 9, Vector((-10, 2, z + 0.25))),
                            (f0 + 12, Vector((-10, 2, z)))])
        key_path(cam, [(1, Vector((11, -22, 3.5))), (N, Vector((10, -19, 4.5)))])
        key_path(tgt, [(1, Vector((-4.5, 1, 4.2))), (N, Vector((-4.5, 1, 4.8)))])
        smooth_keys(cam)

    elif kind in ("xray_scan", "stress_run", "muscle_needed"):
        xray_skin(mesh, H)
        bones = skeleton(arm, c, stress_legs=(kind == "stress_run"))
        rate = 1.0
        if kind == "stress_run":
            play(arm, run, 1, N, 1.0)
            speed = v_run
            key_prop([(1, 1.0)], "xr")
            key_prop([(1, 0.05), (int(N * 0.7), 1.0), (N, 1.0)], "stress")
        else:
            play(arm, walk, 1, N, rate)
            speed = v_walk * rate
            if kind == "xray_scan":
                rv = SHOT["reveal"]
                key_prop([(1, 0.05), (int(rv["bones"][0] * FPS) + 1, 1.0)], "xr")
                when = schedule(c["bone_groups"], *rv["bones"])
                for nm in c["bone_groups"]:
                    reveal(bones[nm], when[nm])
                mus = muscle_groups(arm)
                when = schedule(c["muscle_groups"], *rv["muscles"])
                for nm in c["muscle_groups"]:
                    reveal(mus[nm], when[nm])
            else:
                key_prop([(1, 1.0)], "xr")
                mus = muscle_groups(arm)
                g0, g1, g2, g3 = (int(N * p) for p in (0.08, 0.35, 0.68, 0.88))
                big = SHOT.get("muscle_scale", 2.6)
                for o in mus["THIGH"]:      # the muscle a fast runner would need, then what it had
                    for fr, k in ((1, 1.0), (g0, 1.0), (g1, big), (g2, big), (g3, 1.0)):
                        o.scale = (k, k * 0.95, 1 + (k - 1) * 0.35)
                        o.keyframe_insert("scale", frame=fr)
            key_prop([(1, 0.0)], "stress")
        d = speed * T
        key_path(arm, [(1, Vector((0, d / 2, 0))), (N, Vector((0, -d / 2, 0)))])
        if kind == "stress_run":       # close on the legs, the camera running alongside
            key_path(cam, [(1, Vector((14, d / 2 - 3, 2.6))), (N, Vector((12, -d / 2 - 2, 2.4)))])
            key_path(tgt, [(1, Vector((0, d / 2, 2.0))), (N, Vector((0, -d / 2, 2.0)))])
        else:
            key_path(cam, [(1, Vector((19, d / 2 - 4, 4.5))), (N, Vector((15, -d / 2 - 6, 3.5)))])
            key_path(tgt, [(1, Vector((0, d / 2, H * 0.45))), (N, Vector((0, -d / 2, H * 0.4)))])

    elif kind == "speed_track":
        rate = SHOT["kmh"] / 3.6 / v_walk
        play(arm, walk, 1, N, rate)
        d = SHOT["kmh"] / 3.6 * T
        x = -2.6
        key_path(arm, [(1, Vector((x, d / 2, 0))), (N, Vector((x, -d / 2, 0)))])
        key_path(cam, [(1, Vector((13, d / 2 + 9, 2.6))), (N, Vector((12.5, -d / 2 - 3, 2.4)))])
        key_path(tgt, [(1, Vector((x, d / 2, H * 0.45))), (N, Vector((x, -d / 2, H * 0.45)))])

    elif kind == "race_pass":
        rate = SHOT["kmh"] / 3.6 / v_walk
        play(arm, walk, 1, N, rate)
        v_t = SHOT["kmh"] / 3.6
        v_c = SHOT["car_kmh"] / 3.6
        dt, dc = v_t * T, v_c * T
        x = -2.6
        key_path(arm, [(1, Vector((x, 0, 0))), (N, Vector((x, -dt, 0)))])
        car, parts = glb(SPEC["props"]["car"], 4.5, (2.6, 0, 0), math.radians(180))
        start = SHOT.get("car_behind_m", 22)
        key_path(car, [(1, Vector((2.6, start, 0))), (N, Vector((2.6, start - dc, 0)))])
        for p in parts:                 # spin the wheels at road speed
            if "wheel" in p.name.lower():
                r = 0.35
                p.rotation_mode = "XYZ"
                ax = 0
                p.keyframe_insert("rotation_euler", index=ax, frame=1)
                p.rotation_euler[ax] -= dc / r
                p.keyframe_insert("rotation_euler", index=ax, frame=N)
                for fc in _fcurves(p.animation_data.action):
                    for k in fc.keyframe_points:
                        k.interpolation = "LINEAR"
        # camera rides with the T. rex, front-left, so the car comes past and pulls away down the road
        key_path(cam, [(1, Vector((11, -16, 2.6))), (N, Vector((11, -16 - dt, 2.6)))])
        key_path(tgt, [(1, Vector((0, -3, 2.4))), (N, Vector((0, -6 - dt * 1.4, 2.2)))])

    elif kind == "closeup_roar":
        play(arm, c.get("roar", walk), int(N * 0.12), N, 0.85)
        play(arm, c.get("idle", walk), 1, int(N * 0.12), 1.0, track="idle")
        arm.animation_data.nla_tracks["idle"].strips[0].extrapolation = "NOTHING" if False else "HOLD"
        key_path(cam, [(1, Vector((3.5, -13, 2.0))), (N, Vector((2.2, -9.5, 2.6)))])
        key_path(tgt, [(1, Vector((0, -3.5, H * 0.8))), (N, Vector((0, -3.5, H * 0.85)))])
        smooth_keys(cam)
    return arm


def render():
    sc = bpy.context.scene
    os.makedirs(args.out, exist_ok=True)
    f0 = max(1, args.start or 1)
    f1 = N if args.end < 0 else min(N, args.end)
    for fr in range(f0, f1 + 1):
        p = os.path.join(args.out, f"{fr:05d}.png")
        if os.path.exists(p):
            continue                    # resumable
        sc.frame_set(fr)
        sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
    print(f"rendered shot {args.shot} frames {f0}-{f1} of {N}")


reset()
build()
if os.environ.get("HERO_SAVE_BLEND"):
    bpy.ops.wm.save_as_mainfile(filepath=os.environ["HERO_SAVE_BLEND"])
render()
