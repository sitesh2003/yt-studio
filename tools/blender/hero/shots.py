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
from mathutils import Vector, Quaternion

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
    f = SHOT.get("length_m", c["length_m"]) / span
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


def piece(arm, bone, shape, dims, offset=(0, 0, 0), along=0.5, material=None, name="Part", turn_x=0.0):
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
    o.data.transform(mathutils.Matrix.Translation(offset) @ mathutils.Matrix.Rotation(math.radians(turn_x), 4, "X")
                     @ mathutils.Matrix.Diagonal((*dims, 1)))
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


def skeleton(arm, c, stress_legs=False, stress_group=None):
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
            # each tooth points down (turned first, then placed along the upper jaw's edge)
            skull.append(piece(arm, "Head", "cone", (0.11, 0.11, 0.32, 0.05),
                               (x * 0.62 * (1 - (a - 0.4) * 0.8), -0.32, 0), along=a, material=still,
                               name="tooth", turn_x=90))
    g["SKULL"] = skull
    tail = []
    for k, b in enumerate(("Tail1", "Tail2", "Tail3", "Tail4", "Tail5")):
        sz = 0.24 * (1 - k * 0.15)
        tail += _vertebrae(arm, b, sz, still, "tailvert", spine_h=0.25 * (1 - k * 0.18),
                           chevron=0.25 * (1 - k * 0.2) if k < 4 else 0)
    g["TAIL"] = tail
    g["ARMS"] = sum((_long_bone(arm, b + s, 0.045, still, "arm") for s in sides
                     for b in ("FrontUpLeg", "FrontLowLeg", "FrontFoot")), [])
    if stress_group:                     # e.g. the teeth glow yellow then red under the bite
        hotm = bone_mat(stress=True)
        for o in g.get(stress_group, []):
            if o.name.startswith("tooth"):   # only the teeth, not the whole skull
                o.data.materials.clear()
                o.data.materials.append(hotm)
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
    # the biceps on each little arm (Carpenter & Smith 2001 estimated its strength)
    g["ARM"] = [piece(arm, "FrontUpLeg" + s_, "sph", (0.3, 0.32, _blen(arm, "FrontUpLeg" + s_) * 0.95), (0, 0.05, 0),
                      along=0.5, material=m, name="biceps") for s_, _ in sides]
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



def crumple_lattice(parts, front_axis_sign=1.0):
    """A lattice round a car body; its shape key 'crushed' pushes the front back ~0.65 m and bulges the
    bonnet up, as a crumple zone folds. Returns the lattice's shape key to animate (0 -> 1)."""
    body = [o for o in parts if o.type == "MESH" and "wheel" not in o.name.lower()]
    meshes = [o for o in parts if o.type == "MESH"]     # wheels ride along with the folding front
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(v) for o in body for v in o.bound_box]
    lo = Vector((min(p[0] for p in pts), min(p[1] for p in pts), min(p[2] for p in pts)))
    hi = Vector((max(p[0] for p in pts), max(p[1] for p in pts), max(p[2] for p in pts)))
    ld = bpy.data.lattices.new("Crumple")
    ld.points_u, ld.points_v, ld.points_w = 6, 2, 3
    lat = bpy.data.objects.new("Crumple", ld)
    bpy.context.collection.objects.link(lat)
    lat.location = (lo + hi) / 2
    lat.scale = (hi - lo) * 1.04
    for o in meshes:
        m = o.modifiers.new("Crumple", "LATTICE")
        m.object = lat
    lat.shape_key_add(name="Basis")
    sk = lat.shape_key_add(name="crushed")
    L = (hi - lo).x
    push = 0.65 / L                          # front pushed back 0.65 m, in lattice units
    for i, pt in enumerate(ld.points):
        u = pt.co[0] * front_axis_sign        # -0.5 (back) .. 0.5 (front)
        k = max(0.0, (u - 0.05) / 0.45)       # only the front ~45% folds
        co = sk.data[i].co
        co.x = pt.co[0] - front_axis_sign * push * k
        co.z = pt.co[2] + (0.16 * k if pt.co[2] > 0 else -0.01 * k)    # the bonnet buckles up
    return sk


def key_value(sk, frames_vals):
    for fr, v in frames_vals:
        sk.value = v
        sk.keyframe_insert("value", frame=fr)

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



FILM = os.environ.get("HERO_QUALITY") == "film"     # Cycles on the laptop's graphics card (owner, 21 Nov 2026)


def film_setup():
    """Film look: Cycles path tracing on the RTX card (OptiX, denoised), soft bounced light."""
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        for kind in ("OPTIX", "CUDA"):
            try:
                prefs.compute_device_type = kind
                prefs.get_devices()
                if any(d.type == kind for d in prefs.devices):
                    break
            except Exception:
                continue
        for d in prefs.devices:
            d.use = d.type != "CPU"
        sc.cycles.device = "GPU"
    except Exception as e:
        print("film: no GPU, CPU render", e)
    sc.cycles.samples = 16 if args.preview else 40       # the OptiX denoiser cleans the rest
    try:
        sc.cycles.use_adaptive_sampling = True
        sc.cycles.adaptive_threshold = 0.04
    except Exception:
        pass
    sc.cycles.use_denoising = True
    try:
        sc.cycles.denoiser = "OPTIX"
    except Exception:
        pass
    sc.cycles.max_bounces = 4
    sc.render.use_motion_blur = False      # Cycles blur re-evaluates every frame several times; ~2x slower
    sc.render.film_transparent = False


def film_world(look):
    """Light from a real sky photo (Poly Haven, CC0) for day shots; keeps the painted dusk/sim skies."""
    hdr = os.path.abspath(os.path.join(ASSETS, "hdri", "sky_day.hdr"))
    if look != "day" or not os.path.exists(hdr):
        return
    w = bpy.context.scene.world
    nt = w.node_tree
    nt.nodes.clear()
    out = node(nt, "ShaderNodeOutputWorld", (400, 0))
    bg = node(nt, "ShaderNodeBackground", (200, 0))
    env = nt.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(hdr)
    nt.links.new(env.outputs[0], bg.inputs[0])
    nt.links.new(bg.outputs[0], out.inputs[0])
    bg.inputs["Strength"].default_value = 1.1


def film_creature(mesh):
    """Smooth, rounded characters instead of hard facets."""
    for poly in mesh.data.polygons:
        poly.use_smooth = True
    sub = mesh.modifiers.new("Smooth", "SUBSURF")
    sub.levels, sub.render_levels = 1, 2


def film_camera(cam, tgt):
    cam.data.dof.use_dof = True
    cam.data.dof.focus_object = tgt
    cam.data.dof.aperture_fstop = 2.8


TOON = os.environ.get("HERO_QUALITY") == "toon"     # cartoon look on EEVEE (council, 22 Nov 2026)


def toon_material(base_rgb):
    """Cel shading: light is cut into 3 flat bands (Shader to RGB -> constant ColorRamp) times the base colour,
    plus a soft rim highlight. EEVEE only."""
    m = bpy.data.materials.new("Toon")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = node(nt, "ShaderNodeOutputMaterial", (900, 0))
    dif = node(nt, "ShaderNodeBsdfDiffuse", (-600, 0))
    s2r = nt.nodes.new("ShaderNodeShaderToRGB")
    ramp = node(nt, "ShaderNodeValToRGB", (-200, 0))
    ramp.color_ramp.interpolation = "CONSTANT"
    e = ramp.color_ramp.elements
    e[0].position, e[0].color = 0.0, (0.38, 0.40, 0.55, 1)      # shadow band, a little blue
    e[1].position, e[1].color = 0.65, (1.0, 1.0, 1.0, 1)
    mid = e.new(0.3)
    mid.color = (0.7, 0.7, 0.78, 1)
    mul = nt.nodes.new("ShaderNodeMix")
    mul.data_type = "RGBA"
    mul.blend_type = "MULTIPLY"
    mul.inputs[0].default_value = 1.0
    mul.inputs[6].default_value = (*base_rgb, 1)
    lw = node(nt, "ShaderNodeLayerWeight", (-200, -300))
    lw.inputs["Blend"].default_value = 0.22
    rim = nt.nodes.new("ShaderNodeMath")
    rim.operation = "GREATER_THAN"
    rim.inputs[1].default_value = 0.72
    add = nt.nodes.new("ShaderNodeMix")
    add.data_type = "RGBA"
    add.blend_type = "ADD"
    add.inputs[7].default_value = (0.25, 0.25, 0.25, 1)
    em = node(nt, "ShaderNodeEmission", (700, 0))
    for a_, b_ in ((dif.outputs[0], s2r.inputs[0]), (s2r.outputs["Color"], ramp.inputs[0]),
                   (ramp.outputs[0], mul.inputs[7]), (lw.outputs["Facing"], rim.inputs[0]),
                   (rim.outputs[0], add.inputs[0]), (mul.outputs[2], add.inputs[6]),
                   (add.outputs[2], em.inputs["Color"]), (em.outputs[0], out.inputs[0])):
        nt.links.new(a_, b_)
    return m


def toon_outline(obj, thickness):
    """Ink outline by the inverted-hull trick: a solidified, flipped shell drawn black from behind."""
    ol = bpy.data.materials.get("Outline")
    if ol is None:
        ol = bpy.data.materials.new("Outline")
        ol.use_nodes = True
        ol.use_backface_culling = True
        b = ol.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (0.02, 0.02, 0.03, 1)
        b.inputs["Roughness"].default_value = 1.0
    obj.data.materials.append(ol)
    sol = obj.modifiers.new("Outline", "SOLIDIFY")
    sol.thickness = thickness
    sol.offset = 1.0
    sol.use_flip_normals = True
    sol.material_offset = len(obj.data.materials) - 1


def toonify_scene():
    """Every object (not the ground, road or sky) gets cel shading in its own colour, and an outline."""
    sc = bpy.context.scene
    try:
        sc.eevee.taa_render_samples = 16
    except Exception:
        pass
    sc.render.use_motion_blur = False
    for o in list(sc.objects):
        if o.type != "MESH" or o.name.startswith(("Plane", "Road", "Edge", "Dash", "Mark", "BrakeLine", "WetLane",
                                                     "Text")) or max(o.dimensions) > 300:
            continue
        mats = [m for m in o.data.materials if m]
        if not mats or any(m.name.startswith(("Bone", "Muscle", "Cone", "Socket", "Outline")) for m in mats):
            continue
        new = []
        for m in mats:
            col = (0.6, 0.6, 0.6)
            if m.use_nodes:
                b = m.node_tree.nodes.get("Principled BSDF")
                if b:
                    col = tuple(b.inputs["Base Color"].default_value[:3])
                    if b.inputs["Base Color"].is_linked:      # textured (Kenney colormap): keep its material
                        new.append(m)
                        continue
            # flat toon colour shows the stored (linear) value as it is: lift it the way film light did
            import colorsys
            h_, s_, v_ = colorsys.rgb_to_hsv(*[c_ ** 0.6 for c_ in col])
            col = colorsys.hsv_to_rgb(h_, min(1.0, s_ * 1.7 + 0.08), min(0.95, max(0.35, v_ * 1.25)))   # cartoon: bold
            new.append(toon_material(col))
        o.data.materials.clear()
        for m in new:
            o.data.materials.append(m)
        world = 0.03 * max(1.0, max(o.dimensions) / 4)                 # outline width in metres
        toon_outline(o, world / max(1e-6, o.matrix_world.to_scale()[0]))


TAIL_BONES = ("Tail1", "Tail2", "Tail3", "Tail4", "Tail5")


def _whip_value(t, start, dur):
    """Side of the tail (+1 right ... -1 left) at time t for one whip starting at `start`:
    a slow wind-up, a fast swing across, then a slow settle back to the middle."""
    wind, settle = 0.7, 1.4
    def ease(x):
        x = min(1.0, max(0.0, x))
        return x * x * (3 - 2 * x)
    if t < start - wind:
        return 0.0
    if t < start:
        return 0.55 * ease((t - (start - wind)) / wind)
    if t < start + dur:
        x = (t - start) / dur
        return 0.55 - 1.55 * (x * x * x * (x * (x * 6 - 15) + 10))      # smootherstep: fastest mid-swing
    return -1.0 + ease((t - start - dur) / settle)


def tail_whip(arm, starts, dur, amp_deg, n_frames):
    """Swing the tail sideways (about the world vertical) as a whip: each bone a little later and further
    than the one before it, so the tip moves fastest. Layered on top of the body's own animation."""
    ad = arm.animation_data or arm.animation_data_create()
    act = bpy.data.actions.new("TailWhip")
    ad.action = act
    up_arm = (arm.matrix_world.to_3x3().inverted() @ Vector((0, 0, 1))).normalized()
    weights = (0.10, 0.15, 0.2, 0.25, 0.3)
    lag = dur * 0.10
    for k, nm in enumerate(TAIL_BONES):
        pb = arm.pose.bones[nm]
        pb.rotation_mode = "QUATERNION"
        axis = (pb.bone.matrix_local.to_3x3().inverted() @ up_arm).normalized()
        for fr in range(1, n_frames + 1):
            t = (fr - 1) / FPS
            v = sum(_whip_value(t, st + k * lag, dur) for st in starts)
            pb.rotation_quaternion = Quaternion(axis, math.radians(amp_deg * weights[k] * v))
            pb.keyframe_insert("rotation_quaternion", frame=fr)
    ad.action = None
    tr = ad.nla_tracks.new()
    tr.name = "whip"
    st = tr.strips.new("TailWhip", 1, act)
    try:
        st.action_slot = act.slots[0]
    except Exception:
        pass
    st.blend_type = "COMBINE"
    st.extrapolation = "HOLD"


def tip_speed(arm, n_frames):
    """Fastest speed of the tail tip in the scene (m/s), measured frame to frame: the picture must match the
    number the narration says."""
    sc = bpy.context.scene
    prev, best = None, (0.0, 0)
    for fr in range(1, n_frames + 1):
        sc.frame_set(fr)
        p = arm.matrix_world @ arm.pose.bones["Tail5"].tail
        if prev is not None:
            v = (p - prev).length * FPS
            if v > best[0]:
                best = (v, fr)
        prev = p.copy()
    sc.frame_set(1)
    return best

# ---------------------------------------------------------------- the templates
def build():
    kind = SHOT["kind"]
    c = SPEC["creature"]
    look = SHOT.get("world", {"run_at_camera": "day", "size_tower": "day", "xray_scan": "sim",
                              "stress_run": "sim", "muscle_needed": "sim", "speed_track": "day",
                              "race_pass": "day", "closeup_roar": "dusk", "xray_jaw": "sim",
                              "coprolite": "sim", "crash_compare": "day", "grow": "day",
                              "brake_compare": "day", "vision_cone": "day", "tail_whip": "day", "balance": "day"}[kind])
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
    if FILM and (look in ("day", "dusk") or os.environ.get("HERO_FILM_ALL")):
        # film look where it shows most (outdoor light); the dark x-ray 'computer model' shots stay EEVEE
        film_setup()
        film_world(look)
        film_creature(mesh)
    H = c["height_m"] * SHOT.get("length_m", c["length_m"]) / c["length_m"]
    walk, run = c["walk"], c["run"]
    v_walk = natural_speed(arm, action(walk), c["foot_bone"])
    v_run = natural_speed(arm, action(run), c["foot_bone"])
    print(f"natural speeds: walk {v_walk * 3.6:.1f} km/h, run {v_run * 3.6:.1f} km/h")
    cam, tgt = camera(SHOT.get("lens", 32))
    if FILM and bpy.context.scene.render.engine == "CYCLES":
        film_camera(cam, tgt)
    fwd = Vector((0, -1, 0))                                    # the creature faces -Y
    T = N / FPS

    if SHOT.get("scale_prop"):               # something everyone knows the size of, beside a small animal
        prop, _ = glb(SHOT["scale_prop"]["file"], SHOT["scale_prop"]["length_m"], tuple(SHOT["scale_prop"]["at"]), 0.0)

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
        play(arm, c.get(SHOT.get("anim", "idle"), walk), 1, N, SHOT.get("anim_rate", 1.0))
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

    elif kind == "xray_jaw":
        # close on the head in x-ray: jaw muscles (and optionally the teeth turning red) while it bites
        xray_skin(mesh, H)
        bones = skeleton(arm, c, stress_group="SKULL" if SHOT.get("teeth_stress") else None)
        if SHOT.get("xr_start"):            # already in x-ray on frame 1 (a hook frame must show the subject)
            key_prop([(1, 1.0)], "xr")
        else:
            key_prop([(1, 0.05), (int(N * 0.3), 1.0)], "xr")
        play(arm, c.get(SHOT.get("anim", "roar"), walk), 1, N, SHOT.get("anim_rate", 0.7))
        mus = muscle_groups(arm)
        if SHOT.get("reveal") is not None:
            rv = SHOT["reveal"] or {"bones": [0.3, 1.2], "muscles": [1.3, 2.5]}
            bg = SHOT.get("bone_groups") or c["bone_groups"]
            mg = SHOT.get("muscle_groups") or c["muscle_groups"]
            when = schedule(bg, *rv["bones"])
            for nm in c["bone_groups"]:
                if nm in when:
                    reveal(bones[nm], when[nm])
                elif SHOT.get("bone_groups"):      # bones this shot is not about stay hidden
                    for o in bones[nm]:
                        o.hide_render = True
            when = schedule(mg, *rv["muscles"])
            for nm in c["muscle_groups"]:
                if nm in when:
                    reveal(mus[nm], when[nm])
                else:                       # muscles this shot is not about stay hidden
                    for o in mus[nm]:
                        o.hide_render = True
        if SHOT.get("teeth_stress"):
            key_prop([(1, 0.0), (int(N * 0.25), 0.1), (int(N * 0.75), 1.0), (N, 1.0)], "stress")
        else:
            key_prop([(1, 0.0)], "stress")
        key_path(cam, [(1, Vector((6.5, -8.5, 5.6))), (N, Vector((4.8, -7.6, 5.4)))])
        key_path(tgt, [(1, Vector((0, -4.4, 4.9))), (N, Vector((0, -4.5, 4.9)))])
        smooth_keys(cam)

    elif kind == "coprolite":
        # the fossil poop: a lumpy brown stone on a stand, slowly turning, with bone shards inside
        arm.location = (0, 0, -100)                       # the T. rex is not in this shot
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=5, radius=1.0, location=(0, 0, 1.6))
        rock = bpy.context.object
        rock.scale = (1.6, 0.75, 0.7)
        tex = bpy.data.textures.new("Lumps", "CLOUDS")
        tex.noise_scale = 0.45
        dsp = rock.modifiers.new("D", "DISPLACE")
        dsp.texture, dsp.strength = tex, 0.35
        rm = bpy.data.materials.new("Coprolite")
        rm.use_nodes = True
        rm.surface_render_method = "BLENDED"
        b = rm.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (0.32, 0.2, 0.11, 1)
        b.inputs["Roughness"].default_value = 0.85
        b.inputs["Alpha"].default_value = 1.0
        rock.data.materials.append(rm)
        bpy.ops.object.shade_smooth()
        pivot = bpy.data.objects.new("Pivot", None)
        bpy.context.collection.objects.link(pivot)
        pivot.location = (0, 0, 1.6)
        rock.parent = pivot
        rock.location = (0, 0, 0)
        shard_m = bone_mat(stress=False)
        import random
        rnd = random.Random(7)
        for i in range(38):                              # bone fragments, seen as the stone turns clear
            bpy.ops.mesh.primitive_cube_add(size=1)
            sh = bpy.context.object
            sh.scale = (rnd.uniform(0.05, 0.22), rnd.uniform(0.03, 0.07), rnd.uniform(0.03, 0.06))
            sh.rotation_euler = (rnd.uniform(0, 3), rnd.uniform(0, 3), rnd.uniform(0, 3))
            sh.location = (rnd.uniform(-1.1, 1.1), rnd.uniform(-0.4, 0.4), rnd.uniform(-0.38, 0.38))
            sh.data.materials.append(shard_m)
            sh.parent = pivot
        # the stone turns half see-through partway, showing the bone inside
        mix_in = rm.node_tree.nodes.new("ShaderNodeBsdfTransparent")
        mixs = rm.node_tree.nodes.new("ShaderNodeMixShader")
        outn = [n for n in rm.node_tree.nodes if n.type == "OUTPUT_MATERIAL"][0]
        xr_ = _attr(rm.node_tree, "xr", (-300, -300))
        mul = rm.node_tree.nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        mul.inputs[1].default_value = 0.72
        rm.node_tree.links.new(xr_.outputs["Fac"], mul.inputs[0])
        rm.node_tree.links.new(mul.outputs[0], mixs.inputs[0])
        rm.node_tree.links.new(b.outputs[0], mixs.inputs[1])
        rm.node_tree.links.new(mix_in.outputs[0], mixs.inputs[2])
        rm.node_tree.links.new(mixs.outputs[0], outn.inputs["Surface"])
        key_prop([(1, 0.0), (int(N * 0.35), 0.0), (int(N * 0.6), 1.0)], "xr")
        pivot.rotation_euler = (0, 0, 0)
        pivot.keyframe_insert("rotation_euler", frame=1)
        pivot.rotation_euler = (0, 0, math.radians(150))
        pivot.keyframe_insert("rotation_euler", frame=N)
        bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=1.3, depth=0.6, location=(0, 0, 0.3))
        bpy.context.object.data.materials.append(mat("Stand", (0.05, 0.07, 0.1), 0.4))
        key_path(cam, [(1, Vector((0, -6.5, 2.6))), (N, Vector((0, -5.2, 2.3)))])
        key_path(tgt, [(1, Vector((0, 0, 1.55))), (N, Vector((0, 0, 1.55)))])
        smooth_keys(cam)

    elif kind == "crash_compare":
        # two identical cars hit concrete barriers side by side, in slow motion: the stiff one stops in a
        # blink, the crumpling one folds its front and takes longer to stop. Same speed, same mass.
        arm.location = (0, 0, -100)                      # no creature in this shot
        slow = SHOT.get("slowmo", 4.0)
        v = SHOT.get("kmh", 50) / 3.6 / slow             # on-screen speed
        hit = int(N * SHOT.get("hit_at", 0.45))
        concrete = mat("Concrete", (0.55, 0.55, 0.52), 0.9)
        stripe = mat("Stripe", (0.95, 0.75, 0.1), 0.5)
        lanes = SHOT.get("lanes", ["rigid", "crumple"])
        for k, mode in enumerate(lanes):
            y = (k - (len(lanes) - 1) / 2) * 4.2
            box("Barrier", (1.2, 3.2, 1.6), (0.6, y, 0.8), concrete)
            box("Stripe", (0.05, 3.2, 0.3), (-0.01, y, 1.1), stripe)
            bpy.ops.object.text_add(location=(0.6, y, 1.62))   # name on the barrier top, reading across the screen
            lbl = bpy.context.object
            lbl.data.align_x, lbl.data.align_y = "CENTER", "CENTER"
            lbl.data.body = "STIFF" if mode == "rigid" else "FOLDS"
            lbl.data.size = 0.42
            lbl.data.extrude = 0.01
            lbl.data.materials.append(mat("Lbl" + mode, (1, 1, 1), 0.5, emit=(1.0, 0.25, 0.2) if mode == "rigid"
                                          else (0.3, 0.85, 1.0), emit_strength=2.5))
            car, parts = glb(SPEC["props"]["car"], 4.5, (0, y, 0), math.radians(-90))
            bpy.context.view_layer.update()
            front = max((o.matrix_world @ Vector(c_))[0] for o in parts if o.type == "MESH" for c_ in o.bound_box)
            gap = -front                                  # car origin x so its nose touches x=0
            run_in = v * (hit - 1) / FPS
            if mode == "rigid":
                stop_frames = max(2, int(0.012 * FPS * slow))       # ~0.01 s: a blink
                travel = 0.08
            else:
                stop_frames = max(6, int(0.1 * FPS * slow))         # ~0.1 s spread over the fold
                travel = 0.65
            key_path(car, [(1, Vector((gap - run_in, y, 0))), (hit, Vector((gap, y, 0)))])
            car.location = (gap + travel, y, 0)
            car.keyframe_insert("location", frame=hit + stop_frames)
            for fc in _fcurves(car.animation_data.action):            # decelerate through the stop
                for kp in fc.keyframe_points:
                    if abs(kp.co[0] - (hit + stop_frames)) < 0.5:
                        kp.interpolation = "LINEAR"
                    if abs(kp.co[0] - hit) < 0.5:
                        kp.interpolation = "QUAD"
                        kp.easing = "EASE_OUT"
            if mode == "crumple":
                sk = crumple_lattice(parts)
                key_value(sk, [(1, 0.0), (hit, 0.0), (hit + stop_frames, 1.0)])
            else:                                        # a stiff car barely dents, but jolts
                sk = crumple_lattice(parts)
                key_value(sk, [(1, 0.0), (hit, 0.0), (hit + stop_frames, 0.08)])
        # from nearly straight above: the folding car visibly gets shorter; cars sit low in the frame,
        # under the captions, so graphs and cards have the top
        lift = SHOT.get("frame_lift", 3.0)
        key_path(cam, [(1, Vector((-2.2, -3.5 + lift, 17.0))), (N, Vector((-1.8, -3.0 + lift, 15.5)))])
        key_path(tgt, [(1, Vector((-2.2, lift, 0))), (N, Vector((-1.8, lift, 0)))])
        smooth_keys(cam)

    elif kind == "grow":
        # the growth spurt: the animal grows from SHOT['from_m'] to SHOT['to_m'] long while standing,
        # trees and the road for scale (ages and the kg-a-day counter are drawn by compose.g_grow)
        play(arm, c.get("idle", walk), 1, N, 1.0)
        base = arm.scale.copy()
        k0 = SHOT.get("from_m", 4.0) / SHOT.get("length_m", c["length_m"])
        g0, g1 = int(N * 0.12), int(N * 0.85)
        for fr, k in ((1, k0), (g0, k0), (g1, 1.0)):
            arm.scale = base * k
            arm.keyframe_insert("scale", frame=fr)
        if arm.animation_data and arm.animation_data.action:
            for fc in _fcurves(arm.animation_data.action):
                for kp in fc.keyframe_points:
                    kp.interpolation = "BEZIER"
        arm.location = (-2.6, 0, 0)
        arm.rotation_euler = (0, 0, math.radians(-15))
        key_path(cam, [(1, Vector((17.0, -17.0, 4.0))), (N, Vector((19.0, -19.5, 5.2)))])
        key_path(tgt, [(1, Vector((-2.6, -1.0, 2.0))), (N, Vector((-2.6, -1.0, H * 0.45)))])
        smooth_keys(cam)

    elif kind == "brake_compare":
        # two cars brake hard at the same line, from SHOT['speeds'] km/h, at a dry-road deceleration; from above
        arm.location = (0, 0, -100)
        decel = SHOT.get("decel", 7.0)
        speeds = SHOT.get("speeds", [30, 60])
        white = mat("Mark", (0.95, 0.95, 0.95), 0.5, emit=(1.0, 0.85, 0.1), emit_strength=2.0)   # reads in film light
        red = mat("BrakeLine", (0.9, 0.1, 0.05), 0.5, emit=(1, 0.2, 0.1), emit_strength=1.5)
        skid = mat("Skid", (0.02, 0.02, 0.02), 0.9)
        box("BrakeLine", (9.0, 0.35, 0.03), (0, 0, 0.05), red)
        for m_ in range(5, 30, 5):                       # distance markers every 5 m past the brake line
            box("Mark", (9.0, 0.12, 0.03), (0, m_, 0.05), white)
            bpy.ops.object.text_add(location=(5.7, m_ - 0.6, 0.06))
            t_ = bpy.context.object
            t_.data.body = f"{m_} m"
            t_.data.size = 1.5
            t_.data.materials.append(white)
        lead = SHOT.get("lead_s", 1.0)                   # seconds of driving before the brake line
        brake_at = int(N * SHOT.get("brake_at", 0.3))
        decels = SHOT.get("decels") or [decel] * len(speeds)
        if SHOT.get("wet_lane") is not None:              # the wet lane: dark, glossy road
            wm = bpy.data.materials.new("Wet")
            wm.use_nodes = True
            bw = wm.node_tree.nodes["Principled BSDF"]
            bw.inputs["Base Color"].default_value = (0.015, 0.018, 0.025, 1)
            bw.inputs["Roughness"].default_value = 0.05
            box("WetLane", (4.0, 60, 0.02), (-2.2 + 4.4 * SHOT["wet_lane"], 12, 0.045), wm)
        for k, kmh in enumerate(speeds):
            x = -2.2 + 4.4 * k
            v = kmh / 3.6
            decel = decels[k]
            car, parts = glb(SPEC["props"]["car"], 4.5, (x, 0, 0), 0.0)
            bpy.context.view_layer.update()
            front = max((o.matrix_world @ Vector(c_))[1] for o in parts if o.type == "MESH" for c_ in o.bound_box)
            nose = front                                  # car origin to nose
            t_stop = v / decel
            for fr in range(1, N + 1):
                t = (fr - brake_at) / FPS
                if t < 0:
                    y = v * t
                elif t < t_stop:
                    y = v * t - 0.5 * decel * t * t
                else:
                    y = v * v / (2 * decel)
                car.location = (x, y - nose, 0)
                car.keyframe_insert("location", frame=fr)
            # skid marks grow behind the wheels while it brakes
            for wx in (-0.75, 0.75):
                bpy.ops.mesh.primitive_cube_add(size=1)
                sk = bpy.context.object
                sk.data.transform(mathutils.Matrix.Translation((0, 0.5, 0)))
                sk.location = (x + wx, 0, 0.045)
                sk.data.materials.append(skid)
                for fr in range(1, N + 1, 2):
                    t = (fr - brake_at) / FPS
                    L_ = 0.001 if t <= 0 else (v * min(t, t_stop) - 0.5 * decel * min(t, t_stop) ** 2)
                    sk.scale = (0.25, max(0.001, L_), 0.01)
                    sk.keyframe_insert("scale", frame=fr)
        hi_ = SHOT.get("cam_h", 25.0)
        key_path(cam, [(1, Vector((0.0, -14.0, hi_))), (N, Vector((0.0, -13.0, hi_ - 2)))])
        key_path(tgt, [(1, Vector((0.0, 9.0, 0))), (N, Vector((0.0, 10.0, 0)))])

    elif kind == "vision_cone":
        # where both eyes overlap: a glowing cone forward from the eyes, SHOT['deg'] wide (binocular field)
        play(arm, c.get("idle", walk), 1, N, 1.0)
        deg = SHOT.get("deg", 55)
        L = SHOT.get("cone_len", 9.0)
        cm = bpy.data.materials.new("Cone")
        cm.use_nodes = True
        cm.surface_render_method = "BLENDED"
        nt = cm.node_tree
        nt.nodes.clear()
        o_ = node(nt, "ShaderNodeOutputMaterial", (400, 0))
        em = node(nt, "ShaderNodeEmission", (0, -100))
        em.inputs["Color"].default_value = (1.0, 0.85, 0.15, 1)
        em.inputs["Strength"].default_value = 2.0
        tr = node(nt, "ShaderNodeBsdfTransparent", (0, 100))
        mx = node(nt, "ShaderNodeMixShader", (200, 0))
        mx.inputs[0].default_value = 0.22
        nt.links.new(tr.outputs[0], mx.inputs[1])
        nt.links.new(em.outputs[0], mx.inputs[2])
        nt.links.new(mx.outputs[0], o_.inputs[0])
        r = L * math.tan(math.radians(deg / 2))
        hb = _blen(arm, "Head")
        # apex just in front of the eyes, opening along the snout direction and beyond
        cone = piece(arm, "Head", "cone", (2 * r, 2 * r, L, 0.0), (0, 0.25, L / 2 + hb * 0.3), along=0.0,
                     material=cm, name="vision", turn_x=180)
        g0 = int(N * 0.15)
        for fr, k in ((1, 0.0), (g0, 0.0), (g0 + 12, 1.0)):
            cone.scale = (k, k, k)
            cone.keyframe_insert("scale", frame=fr)
        view = SHOT.get("view", "side")
        if view == "behind":                 # over the shoulder, looking down the cone
            key_path(cam, [(1, Vector((2.2, 3.5, 7.2))), (N, Vector((1.6, 2.0, 6.8)))])
            key_path(tgt, [(1, Vector((0, -10, 4.5))), (N, Vector((0, -11, 4.5)))])
        else:
            key_path(cam, [(1, Vector((19.0, -6.5, 6.5))), (N, Vector((17.5, -7.0, 6.2)))])
            key_path(tgt, [(1, Vector((0, -8.0, 4.4))), (N, Vector((0, -8.2, 4.4)))])
        smooth_keys(cam)

    elif kind == "speed_track":
        rate = SHOT["kmh"] / 3.6 / v_walk
        play(arm, walk, 1, N, rate)
        d = SHOT["kmh"] / 3.6 * T
        x = -2.6
        key_path(arm, [(1, Vector((x, d / 2, 0))), (N, Vector((x, -d / 2, 0)))])
        # the camera rides alongside at a distance that suits the animal's size (cam_dist), so it is in
        # frame from the first frame to the last
        cd_ = SHOT.get("cam_dist", 15.6)
        ch_ = SHOT.get("cam_h", 2.6)
        side = SHOT.get("cam_side", 1)            # 1 = from the side, -1 = slightly behind
        key_path(cam, [(1, Vector((x + cd_, d / 2 + 0.55 * cd_ * side, ch_))),
                       (N, Vector((x + cd_ * 0.97, -d / 2 - 0.2 * cd_ * side, ch_ * 0.95)))])
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

    elif kind == "tail_whip":
        # the 2022 model's whip (Conti et al., Sci Rep): the tail tip at its peak speed, a car beside it at the
        # same speed; the swing is tuned so the measured tip speed in the scene matches the study's figure
        play(arm, c.get(SHOT.get("anim", "idle"), walk), 1, N, SHOT.get("anim_rate", 1.0))
        x0 = SHOT.get("x", -5.0)
        arm.location = (x0, 0, 0)
        if SHOT.get("xray"):               # the "rebuilt in a computer" look: skin see-through, tail bones appear
            xray_skin(mesh, H)
            bones = skeleton(arm, c)
            key_prop([(1, 1.0)], "xr")
            key_prop([(1, 0.0)], "stress")
            keep = SHOT.get("bone_groups", ["TAIL", "SPINE", "HIPS"])
            for nm, objs in bones.items():
                if nm not in keep:
                    for o in objs:
                        o.hide_render = True
            t0, t1 = SHOT.get("bones_s", [0.2, 2.0])
            tail = bones.get("TAIL", [])
            for i, o in enumerate(tail):    # section by section, from the hips to the tip
                reveal([o], int((t0 + (t1 - t0) * i / max(1, len(tail))) * FPS) + 1)
        starts = SHOT.get("whips", [1.0])
        dur = SHOT.get("whip_s", 0.55)
        target = SHOT.get("tip_ms", 33.0)
        amp = 70.0
        for _ in range(4):          # tune the swing to the speed the study found
            for tr in [t for t in arm.animation_data.nla_tracks if t.name == "whip"]:
                arm.animation_data.nla_tracks.remove(tr)
            tail_whip(arm, starts, dur, amp, N)
            v, fr_ = tip_speed(arm, N)
            if v <= 0:
                break
            amp *= target / v
            amp = min(amp, 160.0)
        v, fr_ = tip_speed(arm, N)
        print(f"tail tip peak {v:.1f} m/s ({v * 3.6:.0f} km/h) at frame {fr_}, swing {amp:.0f} deg")
        if SHOT.get("car_kmh"):
            v_c = SHOT["car_kmh"] / 3.6
            car, parts = glb(SPEC["props"]["car"], 4.5, (4.0, 0, 0), math.radians(180))
            meet = fr_ / FPS                      # the car passes the tail tip at the moment of peak speed
            sc_ = bpy.context.scene
            sc_.frame_set(fr_)
            ty = (arm.matrix_world @ arm.pose.bones["Tail5"].tail).y
            sc_.frame_set(1)
            lane = SHOT.get("car_x", 1.5)
            key_path(car, [(1, Vector((lane, ty + v_c * meet, 0))), (N, Vector((lane, ty + v_c * (meet - T), 0)))])
            for p in parts:
                if "wheel" in p.name.lower():
                    p.rotation_mode = "XYZ"
                    p.keyframe_insert("rotation_euler", index=0, frame=1)
                    p.rotation_euler[0] -= v_c * T / 0.35
                    p.keyframe_insert("rotation_euler", index=0, frame=N)
                    for fc in _fcurves(p.animation_data.action):
                        for k in fc.keyframe_points:
                            k.interpolation = "LINEAR"
        cs = SHOT.get("cam_scale", 1.12)        # 1 = the whole animal; smaller = closer on the tail
        key_path(cam, [(1, Vector((x0 + 19 * cs, 4 + 22 * cs, 13 * cs))), (N, Vector((x0 + 17.5 * cs, 4 + 20 * cs, 12 * cs)))])
        key_path(tgt, [(1, Vector((x0 + 1.8, 4.5, 2.2))), (N, Vector((x0 + 1.8, 4.5, 2.2)))])
        smooth_keys(cam)
    elif kind == "balance":
        # a giant see-saw: the animal on one end, family cars dropped on the other until the beam levels at the
        # published mass (SHOT tonnes / car_t tonnes per car); the beam swings like a real damped balance
        M = float(SHOT["tonnes"])
        car_t = SHOT.get("car_t", 1.5)
        n = int(SHOT["cars"])
        pre = int(SHOT.get("start_cars", 0))
        piv_z, half = 5.5, 12.0
        pivot = bpy.data.objects.new("Beam", None)
        bpy.context.collection.objects.link(pivot)
        pivot.location = (0, 0, piv_z)
        steel = mat("Steel", (0.22, 0.24, 0.28), 0.35)
        paint = mat("ScaleYellow", (0.95, 0.68, 0.05), 0.45)
        def on_beam(o, loc):
            o.parent = pivot
            o.matrix_parent_inverse.identity()
            o.location = loc
        on_beam(box("BeamBar", (1.6, 2 * half + 19, 0.9), (0, 0, 0), steel), (0, 3.5, 0))
        on_beam(box("PlatDino", (8.0, 25.0, 0.5), (0, 0, 0), paint), (0, half + 1.0, 0.65))
        on_beam(box("PlatCars", (6.6, 11.0, 0.5), (0, 0, 0), paint), (0, -half, 0.65))
        bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=4.0, radius2=0.6, depth=piv_z, location=(0, 0, piv_z / 2))
        bpy.context.object.data.materials.append(steel)
        arm.parent = pivot
        arm.matrix_parent_inverse.identity()
        arm.location = (0, half - 1.0, 0.9)
        play(arm, c.get(SHOT.get("anim", "idle"), walk), 1, N, 1.0)
        t0, t1 = SHOT.get("drop_s", [0.3, T - 1.2])
        land = []
        for i in range(n):
            layer, idx = divmod(i, 4)            # a tower: 4 cars a layer, so the count reads as layers
            col, row = idx % 2, idx // 2
            loc = Vector(((col - 0.5) * 2.7, -half + (row - 0.5) * 4.95, 0.9 + layer * 1.5))
            car, _ = glb(SPEC["props"]["car"], 4.4, (0, 0, 0), 0.0)
            on_beam(car, loc)
            if i < pre:
                land.append(1)
                continue
            k = i - pre
            f_ = 1 + int((t0 + (t1 - t0) * k / max(1, n - pre - 1)) * FPS)
            land.append(f_)
            up = loc + Vector((0, 0, 70))
            for fr, z in ((1, 70), (max(1, f_ - 9), 70), (max(1, f_ - 8), 14), (f_, 0), (f_ + 3, 0.5), (f_ + 6, 0)):
                car.location = loc + Vector((0, 0, z))
                car.keyframe_insert("location", frame=fr)
            for o in [car] + list(car.children_recursive):     # unseen (and no shadow) until it falls
                for fr, hid in ((1, True), (max(1, f_ - 8), False)):
                    o.hide_render = hid
                    o.keyframe_insert("hide_render", frame=fr)
        # the balance: a damped spring toward the angle the loads ask for
        tilt = math.radians(SHOT.get("max_tilt", 12.0))
        th, w = None, 0.0
        for fr in range(1, N + 1):
            mass = sum(1 for f_ in land if f_ <= fr) * car_t
            target = tilt * math.tanh((mass - M) / (0.18 * M))
            if th is None:
                th = target
            w += (38.0 * (target - th) - 7.5 * w) / FPS
            th += w / FPS
            pivot.rotation_euler = (th, 0, 0)
            pivot.keyframe_insert("rotation_euler", index=0, frame=fr)
        cs = SHOT.get("cam_scale", 1.35)
        cy = SHOT.get("cam_y", 0.0)
        # the beam runs INTO the picture (cars near, the animal far): a vertical frame holds both ends big
        key_path(cam, [(1, Vector((60 * cs, cy - 4 * cs, 17 * cs))), (N, Vector((57 * cs, cy - 3.5 * cs, 16 * cs)))])
        key_path(tgt, [(1, Vector((0, cy + 3.0, 7.5))), (N, Vector((0, cy + 3.0, 7.5)))])
        smooth_keys(cam)
    elif kind == "closeup_roar":
        play(arm, c.get("roar", walk), int(N * 0.12), N, 0.85)
        play(arm, c.get("idle", walk), 1, int(N * 0.12), 1.0, track="idle")
        arm.animation_data.nla_tracks["idle"].strips[0].extrapolation = "NOTHING" if False else "HOLD"
        key_path(cam, [(1, Vector((3.5, -13, 2.0))), (N, Vector((2.2, -9.5, 2.6)))])
        key_path(tgt, [(1, Vector((0, -3.5, H * 0.8))), (N, Vector((0, -3.5, H * 0.85)))])
        smooth_keys(cam)
    if TOON and look != "sim":           # the x-ray "computer model" shots keep their own look
        toonify_scene()
    if SHOT.get("cam"):                 # a shot can set its own camera start/end (relative to the scene)
        for o in (cam, tgt):
            if o.animation_data:
                o.animation_data_clear()
        key_path(cam, [(1, Vector(SHOT["cam"][0])), (N, Vector(SHOT["cam"][1]))])
        key_path(tgt, [(1, Vector(SHOT["tgt"][0])), (N, Vector(SHOT["tgt"][1]))])
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
