"""Micro-world shots for hero Shorts (25 Nov 2026): the inside-the-body look (glowing organic proteins, shallow focus,
drifting molecules, dark ground) from tools/blender/lookdev/micro_world.py, as reusable shot templates.

    blender -b --disable-autoexec --python micro.py -- --spec SPEC.json --shot N --out DIR [--start F --end F] [--preview]

Same contract as shots.py (one PNG per frame, resumable, any frame range on its own), so compose.py, the frame checks
and the archive work unchanged. Everything is procedural; no downloaded assets.

The first set (chilli, Caterina et al. 1997): a nerve-ending membrane (two leaflets of lipid heads) holding TRPV1
channels (four subunits round a pore, each with its big inner domain). Heat or capsaicin opens the pore and ions
pour into the nerve. Scale is stylised for the camera (1 unit ~ 1 nm); the structure (tetramer, pore, a vanilloid
pocket between subunits inside the membrane) follows the published picture.

Kinds: chilli_macro, membrane_dive, heat_open, capsaicin_open, nerve_pulse, channel_orbit, capsaicin_leave,
pull_back, cold_tease.
"""
import argparse
import json
import math
import os
import random
import sys

import bpy
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
SHOT = SPEC["shots"][args.shot]
N = int(round(SHOT.get("render_seconds", SHOT["seconds"]) * FPS))
KIND = SHOT["kind"]
NE = min(N, int(round(SHOT.get("event_seconds", SHOT["seconds"]) * FPS)))   # timed events use this length
random.seed(7 + args.shot)

bpy.ops.wm.read_factory_settings(use_empty=True)
SC = bpy.context.scene
SC.render.fps = FPS
SC.frame_start, SC.frame_end = 1, N
SC.render.resolution_x, SC.render.resolution_y = 1080, 1920
SC.render.resolution_percentage = 50 if args.preview else 100
ENG = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
SC.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in ENG else "BLENDER_EEVEE"
SC.eevee.taa_render_samples = 12 if args.preview else 32
SC.view_settings.view_transform = "Standard"
_looks = [i.identifier for i in SC.view_settings.bl_rna.properties["look"].enum_items]
SC.view_settings.look = "AgX - Punchy" if "AgX - Punchy" in _looks else "None"


def F(frac):
    """A fraction of the shot -> a frame number."""
    return max(1, int(round(1 + frac * (NE - 1))))


# ---------------------------------------------------------------- materials and shapes
def world(rgb, strength=1.0):
    w = bpy.data.worlds.new("W")
    SC.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (*rgb, 1)
    bg.inputs["Strength"].default_value = strength
    return bg


def organic(name, base, emit, emit_str, sss=0.6, noise=6.0, rough=0.35):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1)
    b.inputs["Roughness"].default_value = rough
    for k in ("Subsurface Weight", "Subsurface"):
        if k in b.inputs:
            b.inputs[k].default_value = sss
            break
    if "Subsurface Radius" in b.inputs:
        b.inputs["Subsurface Radius"].default_value = (1.0, 0.5, 0.3)
    if "Coat Weight" in b.inputs:
        b.inputs["Coat Weight"].default_value = 0.4
    tex = nt.nodes.new("ShaderNodeTexNoise")
    tex.inputs["Scale"].default_value = noise
    tex.inputs["Detail"].default_value = 6
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.45
    ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
    ramp.color_ramp.elements[1].color = (*emit, 1)
    nt.links.new(tex.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = emit_str
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.35
    n2 = nt.nodes.new("ShaderNodeTexNoise")
    n2.inputs["Scale"].default_value = noise * 3
    nt.links.new(n2.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def glow(name, rgb, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Emission Color"].default_value = (*rgb, 1)
    b.inputs["Emission Strength"].default_value = strength
    return m


def emis_input(m):
    return m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]


def key_input(inp, frames_vals):
    for fr, v in frames_vals:
        inp.default_value = v
        inp.keyframe_insert("default_value", frame=fr)


def lumpy(obj, strength=0.12, scale=2.5):
    t = bpy.data.textures.new(obj.name + "N", "CLOUDS")
    t.noise_scale = 1.0 / scale
    md = obj.modifiers.new("Lumps", "DISPLACE")
    md.texture = t
    md.strength = strength
    md.mid_level = 0.5


def blob(name, radius, loc, scale, material, lump=0.15, lump_scale=3.0, subdiv=4, parent=None):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdiv, radius=radius, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    if lump:
        lumpy(o, lump, lump_scale)
    o.data.materials.append(material)
    for p in o.data.polygons:
        p.use_smooth = True
    if parent:
        o.parent = parent
    return o


def empty(name, loc=(0, 0, 0)):
    e = bpy.data.objects.new(name, None)
    SC.collection.objects.link(e)
    e.location = loc
    return e


def area_light(loc, look_at, energy, rgb, size=8):
    ld = bpy.data.lights.new("L", "AREA")
    ld.energy, ld.color, ld.size = energy, rgb, size
    lo = bpy.data.objects.new("L", ld)
    SC.collection.objects.link(lo)
    lo.location = loc
    lo.rotation_euler = (Vector(look_at) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return lo


def bloom(strength=0.9, threshold=0.5):
    try:
        ng = bpy.data.node_groups.new("Comp", "CompositorNodeTree")
        ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
        SC.compositing_node_group = ng
        rl = ng.nodes.new("CompositorNodeRLayers")
        out = ng.nodes.new("NodeGroupOutput")
        gl = ng.nodes.new("CompositorNodeGlare")
        for k, v in (("Type", "Bloom"), ("Quality", "High")):
            if k in gl.inputs:
                gl.inputs[k].default_value = v
        for k, v in (("Threshold", threshold), ("Strength", strength), ("Size", 0.7)):
            if k in gl.inputs:
                gl.inputs[k].default_value = v
        if hasattr(gl, "glare_type"):
            gl.glare_type = "BLOOM"
        ng.links.new(rl.outputs["Image"], gl.inputs["Image"])
        ng.links.new(gl.outputs["Image"], out.inputs[0])
    except Exception as ex:
        print("bloom skipped:", ex)


def camera(lens=35, fstop=1.2, shift_y=0.0):
    cd = bpy.data.cameras.new("C")
    cd.lens = lens
    cd.shift_y = shift_y
    cd.clip_start, cd.clip_end = 0.05, 500
    cam = bpy.data.objects.new("Cam", cd)
    SC.collection.objects.link(cam)
    SC.camera = cam
    tgt = empty("Tgt")
    c = cam.constraints.new("TRACK_TO")
    c.target = tgt
    c.track_axis, c.up_axis = "TRACK_NEGATIVE_Z", "UP_Y"
    cd.dof.use_dof = True
    cd.dof.focus_object = tgt
    cd.dof.aperture_fstop = fstop
    return cam, tgt


def key_loc(obj, frames_locs):
    for fr, loc in frames_locs:
        obj.location = loc
        obj.keyframe_insert("location", frame=fr)


def smooth(obj):
    """Ease in and out on every key (Bezier auto-clamped)."""
    ad = obj.animation_data
    if not ad or not ad.action:
        return
    for fc in _fcurves(ad.action):
        for kp in fc.keyframe_points:
            kp.interpolation = "BEZIER"
            kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"


def linear(obj):
    ad = obj.animation_data
    if not ad or not ad.action:
        return
    for fc in _fcurves(ad.action):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"


def _fcurves(act):
    if hasattr(act, "fcurves") and len(getattr(act, "fcurves", [])):
        return list(act.fcurves)
    out = []
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            for cb in strip.channelbags:
                out.extend(cb.fcurves)
    return out


# ---------------------------------------------------------------- the membrane world
TM_LEAF = 1.9            # lipid head height of each leaflet (membrane ~4 nm)
CUT_Y = -3.6            # the membrane is shown cut open along this line, in front of the hero channel
CHANNELS = [(0, 0), (11, -0.4), (-11, -0.2), (6, 9), (-7, 10), (2, 18), (14, 14), (-15, 15), (21, 5), (-21, 6),
            (8, 26), (-6, 27)]
R_CLOSED, R_OPEN, TILT_OPEN = 1.5, 2.05, 0.14


def _instancer(name, pts, src, lo=0.85, hi=1.15):
    me = bpy.data.meshes.new(name + "Pts")
    me.from_pydata(pts, [], [])
    ob = bpy.data.objects.new(name, me)
    SC.collection.objects.link(ob)
    ng = bpy.data.node_groups.new(name + "GN", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    gi = ng.nodes.new("NodeGroupInput")
    go = ng.nodes.new("NodeGroupOutput")
    inst = ng.nodes.new("GeometryNodeInstanceOnPoints")
    oi = ng.nodes.new("GeometryNodeObjectInfo")
    oi.inputs["Object"].default_value = src
    oi.transform_space = "ORIGINAL"
    rnd = ng.nodes.new("FunctionNodeRandomValue")
    rnd.data_type = "FLOAT"
    rnd.inputs[2].default_value = lo
    rnd.inputs[3].default_value = hi
    ng.links.new(gi.outputs[0], inst.inputs["Points"])
    ng.links.new(oi.outputs["Geometry"], inst.inputs["Instance"])
    ng.links.new(rnd.outputs[1], inst.inputs["Scale"])
    ng.links.new(inst.outputs[0], go.inputs[0])
    ob.modifiers.new("GN", "NODES").node_group = ng
    return ob


def _src(name, material, make):
    make()
    o = bpy.context.object
    o.name = name
    o.location = (0, 0, -500)
    o.data.materials.append(material)
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def lipids(extent=46, spacing=0.74, hole=3.4):
    """Two leaflets of lipid heads, cut open along CUT_Y so the membrane's cross-section shows: on the cut face
    each lipid's two oily tails reach into the middle (the classic textbook cut-away)."""
    head = organic("LipidHead", (0.05, 0.40, 0.42), (0.10, 0.85, 0.75), 0.35, noise=5)
    tailm = organic("LipidTail", (0.75, 0.62, 0.30), (0.9, 0.7, 0.3), 0.6, sss=0.8, noise=4)
    hsrc = _src("LipidSrc", head, lambda: bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.34))
    lumpy(hsrc, 0.04, 6)

    def tails(sign):
        def make():
            parts = []
            for dx in (-0.12, 0.12):
                bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.07, depth=1.45,
                                                    location=(dx, 0, -sign * 0.78))
                parts.append(bpy.context.object)
            bpy.ops.object.select_all(action="DESELECT")
            for o in parts:
                o.select_set(True)
            bpy.context.view_layer.objects.active = parts[0]
            bpy.ops.object.join()
        return make
    tdown = _src("TailDown", tailm, tails(1))
    tup = _src("TailUp", tailm, tails(-1))
    heads, t_top, t_bot = [], [], []
    n = int(extent / spacing)
    for z in (TM_LEAF, -TM_LEAF):
        for i in range(-n, n + 1):
            for j in range(-n, n + 1):
                x = i * spacing + (spacing / 2 if j % 2 else 0) + random.uniform(-0.08, 0.08)
                y = CUT_Y + 0.35 + j * spacing * 0.87 + random.uniform(-0.05, 0.05)
                if y < CUT_Y or x * x + y * y > extent * extent:
                    continue
                if any((x - cx) ** 2 + (y - cy) ** 2 < hole * hole for cx, cy in CHANNELS):
                    continue
                p = (x, y, z + random.uniform(-0.08, 0.08))
                heads.append(p)
                if y < CUT_Y + 1.0:
                    (t_top if z > 0 else t_bot).append(p)
    _instancer("Lipids", heads, hsrc)
    _instancer("TailsTop", t_top, tdown, 0.95, 1.05)
    _instancer("TailsBot", t_bot, tup, 0.95, 1.05)
    # the oily middle behind the cut face: a dark amber slab
    core = glow("Core", (0.10, 0.06, 0.02), 0.35)
    depth_y = extent - CUT_Y
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, CUT_Y + 0.9 + depth_y / 2, 0))
    slab = bpy.context.object
    slab.scale = (2 * extent, depth_y, 2 * TM_LEAF - 0.6)
    slab.data.materials.append(core)
    for cx, cy in CHANNELS:
        bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=hole - 0.2, depth=8, location=(cx, cy, 0))
        cut = bpy.context.object
        b = slab.modifiers.new("cut", "BOOLEAN")
        b.object = cut
        b.operation = "DIFFERENCE"
        cut.hide_render = True
        cut.hide_viewport = True


class Channel:
    """TRPV1: four subunits round a central pore, each a membrane part (S1-S6) and a big inner (ankyrin) domain."""

    def __init__(self, x, y, mat_tm, mat_in, gate_rgb=(1.0, 0.45, 0.12), name="TRPV1"):
        self.c = Vector((x, y, 0))
        self.subs = []
        self.r0 = R_CLOSED
        for k in range(4):
            a = k * math.pi / 2 + math.pi / 4
            e = empty(f"{name}_sub{k}", (x + self.r0 * math.cos(a), y + self.r0 * math.sin(a), 0))
            e.rotation_euler = (0, 0, a)
            e["a"] = a
            blob(f"{name}_tm{k}", 1.0, (0, 0, 0.2), (1.15, 0.95, 2.6), mat_tm, 0.22, 3.0, parent=e)
            blob(f"{name}_in{k}", 1.0, (0.55, 0, -4.4), (1.55, 1.25, 1.7), mat_in, 0.3, 2.2, parent=e)
            blob(f"{name}_out{k}", 0.6, (0.2, 0.25, 3.0), (1.0, 0.8, 0.6), mat_tm, 0.15, 3.0, parent=e)
            self.subs.append(e)
        self.gate_mat = glow(f"{name}_gate", gate_rgb, 0.0)
        bpy.ops.mesh.primitive_torus_add(major_radius=0.75, minor_radius=0.16, location=(x, y, -1.0))
        g = bpy.context.object
        g.data.materials.append(self.gate_mat)
        self.gate = g

    def state(self, frames_open):
        """frames_open: [(frame, 0..1)]; 0 closed, 1 open. The subunits swing out, the pore lights up."""
        for e in self.subs:
            a = e["a"]
            for fr, o in frames_open:
                r = self.r0 + (R_OPEN - self.r0) * o
                e.location = (self.c.x + r * math.cos(a), self.c.y + r * math.sin(a), 0)
                e.rotation_euler = (0, -TILT_OPEN * o, a)
                e.keyframe_insert("location", frame=fr)
                e.keyframe_insert("rotation_euler", frame=fr)
            smooth(e)
        key_input(emis_input(self.gate_mat), [(fr, 9.0 * o) for fr, o in frames_open])
        for fr, o in frames_open:
            s = 0.7 + 0.6 * o
            self.gate.scale = (s, s, 1)
            self.gate.keyframe_insert("scale", frame=fr)


def membrane_world(tint=(0.004, 0.008, 0.02), cold=False):
    bg = world(tint)
    lipids()
    tm = organic("TRPV1", (0.75, 0.12, 0.05), (1.0, 0.28, 0.08), 2.2, sss=0.9, noise=3)
    inner = organic("TRPV1in", (0.55, 0.10, 0.12), (0.9, 0.20, 0.25), 1.2, sss=0.9, noise=2.5)
    chans = [Channel(x, y, tm, inner, name=f"C{i}") for i, (x, y) in enumerate(CHANNELS)]
    for ch in chans[1:]:
        ch.state([(1, 0.0)])
    # drifting soup above and below (bokeh out of focus)
    cols = [(0.2, 0.9, 1.0), (1.0, 0.6, 0.2), (0.9, 0.3, 0.6), (0.5, 1.0, 0.4)]
    for i in range(180):
        z = random.choice((1, -1)) * random.uniform(4, 20)
        loc = Vector((random.uniform(-30, 30), random.uniform(-30, 30), z))
        o = blob(f"dust{i}", random.uniform(0.05, 0.22), loc, (1, 1, 1),
                 glow(f"dustm{i}", random.choice(cols), random.uniform(2, 8)), lump=0, subdiv=2)
        d = Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-0.4, 0.4)))
        key_loc(o, [(1, loc), (N, loc + d * N / FPS * 0.6)])
        linear(o)
    area_light((6, 10, 22), (0, 0, 0), 9000, (1.0, 0.78, 0.55), 14)
    area_light((-14, -10, 6), (0, 0, 0), 3500, (0.3, 0.7, 1.0), 12)
    area_light((0, -4, -14), (0, 0, -3), 2500, (0.2, 1.0, 0.8), 14)
    bloom()
    return chans, bg


def ions(ch, f_start, f_stop, gap=3, count=40, rgb=(0.35, 0.95, 1.0)):
    """Calcium and sodium ions pour into the nerve through the open pore, one after another."""
    m = glow("Ion", rgb, 5.0)
    c = ch.c
    for i in range(count):
        fi = f_start + i * gap
        start = c + Vector((random.uniform(-4, 4), random.uniform(-3.5, 3), random.uniform(3.5, 7)))
        o = blob(f"ion{i}", 0.17, start, (1, 1, 1), m, lump=0, subdiv=2)
        if fi >= f_stop - 6 or fi > N:
            key_loc(o, [(1, start), (N, start + Vector((random.uniform(-1, 1), random.uniform(-1, 1), 0.5)))])
            linear(o)
            continue
        below = c + Vector((random.uniform(-6, 6), random.uniform(-4, 4), random.uniform(-11, -8)))
        key_loc(o, [(1, start), (max(2, fi - 14), start + Vector((0, 0, -0.5))), (fi, c + Vector((0, 0, 3.0))),
                    (fi + 7, c + Vector((0, 0, -2.6))), (fi + 30, below)])
        linear(o)


def capsaicin(name, loc, scale=1.0):
    """Capsaicin, ball and stick: the vanillyl ring (OH and OCH3), the amide link, the 9-carbon fatty tail.
    Built along +X from the ring; returns the parent empty."""
    root = empty(name, loc)
    root.scale = (scale, scale, scale)
    C = glow(name + "C", (1.0, 0.62, 0.12), 6.0)
    O = glow(name + "O", (1.0, 0.18, 0.12), 4.0)
    Nn = glow(name + "N", (0.35, 0.55, 1.0), 4.0)
    bond = glow(name + "B", (0.9, 0.75, 0.55), 1.2)
    atoms = []
    for k in range(6):                          # the benzene ring
        a = k * math.pi / 3
        atoms.append(((0.75 * math.cos(a), 0.75 * math.sin(a), 0), C))
    atoms += [((-1.45, 0.75, 0), O), ((-1.45, -0.75, 0), O), ((-2.2, -1.1, 0), C)]     # OH, OCH3
    x = 0.75
    chain = [C, Nn, C, O, C, C, C, C, C, C, C, C, C]
    pts = []
    for k, el in enumerate(chain):
        x += 0.62
        y = 0.38 if k % 2 else -0.38
        if el is O:
            pts.append(((x - 0.62, y + 0.9, 0), O))   # the carbonyl oxygen hangs off the amide carbon
            x -= 0.62
            continue
        pts.append(((x, y, 0), el))
    pts.append(((x + 0.3, 1.1, 0), C))                    # the branched end (isopropyl)
    atoms += pts
    prev = None
    for k, (p, m) in enumerate(atoms):
        blob(f"{name}a{k}", 0.26 if m is C else 0.3, p, (1, 1, 1), m, lump=0, subdiv=2, parent=root)
    # sticks between neighbours closer than 1 unit
    ps = [Vector(p) for p, _ in atoms]
    for i in range(len(ps)):
        for j in range(i + 1, len(ps)):
            d = ps[j] - ps[i]
            if 0.3 < d.length < 1.05:
                mid = (ps[i] + ps[j]) / 2
                bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.08, depth=d.length, location=mid)
                s = bpy.context.object
                s.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
                s.data.materials.append(bond)
                s.parent = root
    return root


def pocket(ch, k=0):
    """The vanilloid pocket: inside the membrane, between two subunits (stylised position)."""
    a = -math.pi / 3 + k * math.pi / 2
    return ch.c + Vector((2.75 * math.cos(a), 2.75 * math.sin(a), -0.2)), a


def wander(o, start, amp=1.2, every=10, f0=1, f1=None, z_amp=None):
    f1 = f1 or N
    z_amp = amp if z_amp is None else z_amp
    p = Vector(start)
    for fr in range(f0, f1 + 1, every):
        key_loc(o, [(fr, p + Vector((random.uniform(-amp, amp), random.uniform(-amp, amp),
                                     random.uniform(-z_amp, z_amp))))])


# ---------------------------------------------------------------- shots
def heat_particles(hot):
    """Water molecules above the membrane. hot: [(frame, 0..1)]; hot ones jitter fast and glow orange."""
    m = glow("Water", (1.0, 0.45, 0.15), 0.0)
    key_input(emis_input(m), [(fr, 0.6 + 9 * h) for fr, h in hot])
    hot_at = lambda fr: max(0.0, min(1.0, sum(h for f_, h in hot if f_ <= fr) and
                                     next((h for f_, h in reversed(hot) if f_ <= fr), 0)))
    for i in range(130):
        base = Vector((random.uniform(-9, 9), random.uniform(-9, 9), random.uniform(3.2, 10)))
        o = blob(f"w{i}", random.uniform(0.18, 0.3), base, (1, 1, 1), m, lump=0, subdiv=2)
        for fr in range(1, N + 1, 2):
            h = hot_at(fr)
            amp = 0.08 + 0.9 * h
            key_loc(o, [(fr, base + Vector((random.uniform(-amp, amp), random.uniform(-amp, amp),
                                            random.uniform(-amp, amp))))])
        linear(o)


def shot_membrane_dive(cam, tgt, chans):
    key_loc(cam, [(1, (1, -26, 36)), (N, (4, -22, 3.2))])
    key_loc(tgt, [(1, (0, 6, 0)), (N, (0, 0, -1.4))])
    smooth(cam)
    smooth(tgt)
    chans[0].state([(1, 0.0)])


def shot_heat_open(cam, tgt, chans):
    hot = [(1, 0.0), (F(0.15), 0.15), (F(0.42), 1.0), (N, 1.0)]
    heat_particles(hot)
    chans[0].state([(1, 0.0), (F(0.40), 0.0), (F(0.55), 1.0), (N, 1.0)])
    ions(chans[0], F(0.5), N + 99)
    key_loc(cam, [(1, (6, -25, 4.5)), (N, (3.5, -20, 2.2))])
    key_loc(tgt, [(1, (0, 0, -1.2)), (N, (0, 0, -1.4))])
    smooth(cam)
    # the whole scene warms
    SC.world.node_tree.nodes["Background"].inputs["Color"].keyframe_insert("default_value", frame=1)
    SC.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.05, 0.012, 0.006, 1)
    SC.world.node_tree.nodes["Background"].inputs["Color"].keyframe_insert("default_value", frame=F(0.45))
    area_light((0, 0, 16), (0, 0, 0), 0, (1.0, 0.35, 0.1), 16)


def shot_capsaicin_open(cam, tgt, chans):
    heat_particles([(1, 0.0), (N, 0.0)])                  # NO heat: the water stays calm and dark
    ch = chans[0]
    dock, a = pocket(ch, 0)
    f_dock = F(0.42)
    mol = capsaicin("Cap0", dock + Vector((3, -2, 8)), 0.7)
    key_loc(mol, [(1, dock + Vector((3.5, -3, 9))), (F(0.2), dock + Vector((1.5, -1, 4))), (f_dock, dock)])
    smooth(mol)
    for fr, rot in ((1, (0.6, 0.3, 1.2)), (F(0.2), (0.3, 0.1, 0.4)), (f_dock, (1.5708, 0.0, 0.0))):
        mol.rotation_euler = rot
        mol.keyframe_insert("rotation_euler", frame=fr)
    for k in range(5):                                     # more capsaicin drifting in
        p = ch.c + Vector((random.uniform(-9, 9), random.uniform(-9, 9), random.uniform(5, 11)))
        o = capsaicin(f"Cap{k + 1}", p, 0.45)
        key_loc(o, [(1, p), (N, p + Vector((random.uniform(-2, 2), random.uniform(-2, 2), -3)))])
        o.rotation_euler = (random.uniform(0, 3), random.uniform(0, 3), random.uniform(0, 3))
        linear(o)
    ch.state([(1, 0.0), (F(0.46), 0.0), (F(0.6), 1.0), (N, 1.0)])
    ions(ch, F(0.55), N + 99)
    key_loc(cam, [(1, (-5, -25, 5.0)), (N, (-2.5, -20, 2.4))])
    key_loc(tgt, [(1, (0.8, -1, -0.8)), (F(0.45), (1.2, -1.5, -0.6)), (N, (0.3, 0, -1.4))])
    smooth(cam)
    smooth(tgt)


def shot_channel_orbit(cam, tgt, chans, gold=False):
    ch = chans[0]
    ch.state([(1, 1.0)])
    dock, a = pocket(ch, 0)
    mol = capsaicin("Cap0", dock, 0.7)
    mol.rotation_euler = (1.5708, 0, 0)
    ions(ch, 1, N + 99, gap=3, count=int(N / 3) + 10)
    pts = []
    for k in range(0, 9):
        t = k / 8
        ang = -2.2 + 1.2 * t
        pts.append((F(t), (21 * math.cos(ang), 21 * math.sin(ang), 4.5 - 2.0 * t)))
    key_loc(cam, pts)
    smooth(cam)
    key_loc(tgt, [(1, (0, 0, -1.4))])
    if gold:
        area_light((-6, 8, 10), (0, 0, 0), 6000, (1.0, 0.8, 0.35), 8)


def shot_capsaicin_leave(cam, tgt, chans):
    ch = chans[0]
    f_close = F(0.5)
    ch.state([(1, 1.0), (F(0.32), 1.0), (f_close, 0.0), (N, 0.0)])
    dock, a = pocket(ch, 0)
    mol = capsaicin("Cap0", dock, 0.7)
    key_loc(mol, [(1, dock), (F(0.25), dock), (F(0.7), dock + Vector((4, -3, 7))), (N, dock + Vector((6, -5, 11)))])
    smooth(mol)
    for fr, rot in ((1, (1.5708, 0, 0)), (F(0.25), (1.5708, 0, 0)), (N, (2.4, 0.4, 1.5))):
        mol.rotation_euler = rot
        mol.keyframe_insert("rotation_euler", frame=fr)
    ions(ch, 1, f_close, gap=3, count=40)
    key_loc(cam, [(1, (3.5, -20, 2.4)), (N, (6, -24, 5))])
    key_loc(tgt, [(1, (0, 0, -1.4)), (N, (0.8, 0, -0.5))])
    smooth(cam)


def shot_pull_back(cam, tgt, chans):
    ch = chans[0]
    ch.state([(1, 1.0)])
    dock, a = pocket(ch, 0)
    mol = capsaicin("Cap0", dock, 0.7)
    mol.rotation_euler = (1.5708, 0, 0)
    ions(ch, 1, N + 99, gap=3, count=int(N / 3) + 10)
    key_loc(cam, [(1, (3.5, -20, 2.2)), (N, (2, -38, 42))])
    key_loc(tgt, [(1, (0, 0, -1.4)), (N, (0, 6, 0))])
    smooth(cam)
    smooth(tgt)


def shot_cold_tease(cam, tgt, chans):
    """End question (mint and the cold sensor): a different, icy-blue channel (TRPM8 tease) lights up; no answer."""
    cold_tm = organic("TRPM8", (0.10, 0.35, 0.85), (0.4, 0.8, 1.0), 2.5, sss=0.9, noise=3)
    cold_in = organic("TRPM8in", (0.08, 0.25, 0.65), (0.3, 0.6, 1.0), 1.4, sss=0.9, noise=2.5)
    for o in list(SC.objects):                             # re-dress channel 1 as the cold sensor
        if o.name.startswith("C1_tm") or o.name.startswith("C1_out"):
            o.data.materials[0] = cold_tm
        elif o.name.startswith("C1_in"):
            o.data.materials[0] = cold_in
    c1 = chans[1]
    c1.gate_mat.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (0.5, 0.85, 1.0, 1)
    key_input(emis_input(c1.gate_mat), [(1, 0.0), (F(0.4), 0.0), (F(0.8), 6.0)])
    chans[0].state([(1, 0.0)])
    area_light((11, -6, 10), tuple(c1.c), 0, (0.5, 0.8, 1.0), 8)
    li = [o for o in SC.objects if o.type == "LIGHT"][-1]
    li.data.energy = 0
    li.data.keyframe_insert("energy", frame=1)
    li.data.energy = 7000
    li.data.keyframe_insert("energy", frame=F(0.85))
    key_loc(cam, [(1, (3, -28, 14)), (N, (10, -20, 2.6))])
    key_loc(tgt, [(1, (4, 0, -1)), (N, (11, -0.4, -1.4))])
    smooth(cam)
    smooth(tgt)


def shot_nerve_pulse(cam, tgt):
    """The alarm travels: a nerve fibre (unmyelinated, like the C fibres that carry burning pain) with
    signals running along it toward the brain."""
    world((0.004, 0.006, 0.018))
    fibre = organic("Fibre", (0.85, 0.45, 0.25), (1.0, 0.5, 0.25), 0.7, sss=1.0, noise=1.5)
    other = organic("Fibre2", (0.4, 0.25, 0.35), (0.6, 0.3, 0.5), 0.5, sss=1.0, noise=1.5)
    pulse = glow("Pulse", (0.55, 0.95, 1.0), 9.0)

    def tube(name, pts, r, m):
        cu = bpy.data.curves.new(name, "CURVE")
        cu.dimensions = "3D"
        cu.bevel_depth = r
        cu.bevel_resolution = 8
        cu.resolution_u = 24
        sp = cu.splines.new("NURBS")
        sp.points.add(len(pts) - 1)
        for p_, v in zip(sp.points, pts):
            p_.co = (*v, 1)
        sp.use_endpoint_u = True
        sp.order_u = 4
        o = bpy.data.objects.new(name, cu)
        SC.collection.objects.link(o)
        o.data.materials.append(m)
        return o

    main_pts = [(1.5 * math.sin(k * 0.9), 0, -10 + 12 * k) for k in range(14)]
    path = tube("Axon", main_pts, 1.6, fibre)
    for j in range(7):
        ox = random.choice((-1, 1)) * random.uniform(9, 16)
        oz = random.uniform(-9, 9)
        tube(f"Ax{j}", [(ox + math.sin(k + j), 4 + abs(oz), -14 + 14 * k) for k in range(12)],
             random.uniform(0.8, 1.6), other)
    for i in range(6):                                     # signals: glowing rings sliding along the fibre
        bpy.ops.mesh.primitive_torus_add(major_radius=1.5, minor_radius=0.5)
        ring = bpy.context.object
        ring.data.materials.append(pulse)
        ring.scale = (1, 1, 4.0)          # a glowing band that wraps the fibre and runs up it
        ring.location = (0, 0, 0)
        c = ring.constraints.new("FOLLOW_PATH")
        c.target = path
        c.use_curve_follow = True
        c.forward_axis = "FORWARD_Z"
        c.up_axis = "UP_Y"                 # forward Z with the default up Z is degenerate (the band lay sideways)
        c.use_fixed_location = True
        f0 = 1 + i * int(N / 6)
        c.offset_factor = 0.0
        c.keyframe_insert("offset_factor", frame=f0)
        c.offset_factor = 1.0
        c.keyframe_insert("offset_factor", frame=f0 + int(N * 0.8))
        linear(ring)
    path.data.use_path = True
    cols = [(0.2, 0.9, 1.0), (1.0, 0.6, 0.2), (0.9, 0.3, 0.6)]
    for i in range(140):
        loc = Vector((random.uniform(-20, 20), random.uniform(-6, 14), random.uniform(-10, 160)))
        blob(f"dust{i}", random.uniform(0.05, 0.2), loc, (1, 1, 1),
             glow(f"dm{i}", random.choice(cols), random.uniform(2, 8)), lump=0, subdiv=2)
    area_light((8, -12, 30), (0, 0, 20), 9000, (1.0, 0.75, 0.5), 14)
    area_light((-12, -6, 0), (0, 0, 20), 3000, (0.3, 0.7, 1.0), 14)
    key_loc(cam, [(1, (5, -26, -2)), (N, (5, -26, 34))])
    key_loc(tgt, [(1, (0, 0, 2)), (N, (0, 0, 38))])
    linear(cam)
    linear(tgt)
    bloom()


def shot_chilli_macro(cam, tgt):
    """The hook: a real-looking red chilli beside a thermometer that does not move (the mouth stays ~37 C),
    while a red 'alarm' glow pulses round the chilli."""
    world((0.012, 0.006, 0.006))
    # the chilli: rings lofted along a gently bent spine, fat at the shoulder, to a pointed tip
    RING, LEN = 48, 90
    verts, faces = [], []
    L = 7.0
    for i in range(LEN):
        t = i / (LEN - 1)
        cx = 0.9 * math.sin(t * math.pi * 0.85) - 0.2 * t
        cz = L * (1 - t)
        r = 0.78 * (1 - t) ** 0.55 * (1 - 0.35 * math.exp(-t * 18)) + 0.02
        for j in range(RING):
            a = 2 * math.pi * j / RING
            wob = 1 + 0.06 * math.sin(3 * a + t * 5) + 0.03 * math.sin(7 * a)
            verts.append((cx + r * wob * math.cos(a), r * wob * math.sin(a), cz))
    for i in range(LEN - 1):
        for j in range(RING):
            a0, a1 = i * RING + j, i * RING + (j + 1) % RING
            faces.append((a0, a1, a1 + RING, a0 + RING))
    faces.append(tuple(range(RING - 1, -1, -1)))
    faces.append(tuple(range((LEN - 1) * RING, LEN * RING)))
    me = bpy.data.meshes.new("Chilli")
    me.from_pydata(verts, [], faces)
    for p in me.polygons:
        p.use_smooth = True
    chilli = bpy.data.objects.new("Chilli", me)
    SC.collection.objects.link(chilli)
    chilli.modifiers.new("S", "SUBSURF").levels = 1
    red = bpy.data.materials.new("Red")
    red.use_nodes = True
    b = red.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.55, 0.015, 0.008, 1)
    b.inputs["Roughness"].default_value = 0.18
    if "Subsurface Weight" in b.inputs:
        b.inputs["Subsurface Weight"].default_value = 0.35
        b.inputs["Subsurface Radius"].default_value = (1.0, 0.2, 0.1)
    if "Coat Weight" in b.inputs:
        b.inputs["Coat Weight"].default_value = 1.0
    chilli.data.materials.append(red)
    green = organic("Stem", (0.06, 0.25, 0.04), (0.1, 0.3, 0.05), 0.0, sss=0.2, noise=8, rough=0.5)
    blob("Calyx", 0.9, (0, 0, L + 0.05), (1.05, 1.05, 0.35), green, 0.08, 4)
    cu = bpy.data.curves.new("StemC", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = 0.14
    cu.bevel_resolution = 4
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(1)
    sp.bezier_points[0].co = (0, 0, L + 0.2)
    sp.bezier_points[0].handle_right = (0, 0, L + 1.2)
    sp.bezier_points[0].handle_left = (0, 0, L - 0.5)
    sp.bezier_points[1].co = (0.9, 0, L + 1.8)
    sp.bezier_points[1].handle_left = (0.2, 0, L + 1.9)
    sp.bezier_points[1].handle_right = (1.4, 0, L + 1.8)
    st = bpy.data.objects.new("Stem", cu)
    SC.collection.objects.link(st)
    st.data.materials.append(green)
    holder = empty("ChilliRoot")
    for o in (chilli, st, SC.objects["Calyx"]):
        o.parent = holder
    holder.rotation_euler = (0, math.radians(-92), math.radians(-38))
    holder.location = (2.8, -2.8, 0.72)
    # the thermometer, standing behind: glass tube, red column at a fixed level, bulb
    glass = bpy.data.materials.new("Glass")
    glass.use_nodes = True
    gb = glass.node_tree.nodes["Principled BSDF"]
    gb.inputs["Base Color"].default_value = (0.9, 0.95, 1.0, 1)
    gb.inputs["Roughness"].default_value = 0.03
    gb.inputs["Transmission Weight" if "Transmission Weight" in gb.inputs else "Transmission"].default_value = 1.0
    gb.inputs["Alpha"].default_value = 0.35
    try:
        glass.surface_render_method = "BLENDED"
    except Exception:
        pass
    tx, ty = 2.4, 2.6
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.32, depth=9, location=(tx, ty, 5.0))
    bpy.context.object.data.materials.append(glass)
    liquid = glow("Liquid", (0.75, 0.04, 0.03), 0.35)      # calm: body temperature, not a glowing "hot" bar
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=0.55, location=(tx, ty, 0.55))
    bpy.context.object.data.materials.append(liquid)
    for p_ in bpy.context.object.data.polygons:
        p_.use_smooth = True
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.13, depth=1.9, location=(tx, ty, 0.55 + 0.95))
    bpy.context.object.data.materials.append(liquid)
    tick = glow("Tick", (0.9, 0.9, 0.85), 1.0)
    for k in range(16):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(tx + 0.0, ty - 0.33, 1.5 + k * 0.45))
        tk = bpy.context.object
        tk.scale = (0.18 if k % 4 else 0.32, 0.02, 0.03)
        tk.data.materials.append(tick)
    # a dark stone counter
    stone = organic("Stone", (0.03, 0.025, 0.025), (0, 0, 0), 0.0, sss=0.0, noise=20, rough=0.92)
    sb = stone.node_tree.nodes["Principled BSDF"]
    if "Coat Weight" in sb.inputs:
        sb.inputs["Coat Weight"].default_value = 0.0
    if "Specular IOR Level" in sb.inputs:
        sb.inputs["Specular IOR Level"].default_value = 0.15
    bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 0, 0))
    bpy.context.object.data.materials.append(stone)
    area_light((6, -8, 12), (0, 0, 2), 4000, (1.0, 0.9, 0.8), 6)
    area_light((-6, 6, 8), (0, 0, 2), 800, (0.5, 0.7, 1.0), 6)
    rim = area_light((-5, 5, 2.5), (-0.5, -1.2, 0.7), 0, (1.0, 0.25, 0.05), 4)   # behind the chilli, NOT behind the glass
    for fr in range(1, N + 1, 6):                          # the 'on fire' alarm glow, pulsing
        rim.data.energy = 2500 + 2200 * (0.5 + 0.5 * math.sin(fr / FPS * 2 * math.pi * 1.3))
        rim.data.keyframe_insert("energy", frame=fr)
    key_loc(cam, [(1, (1.8, -12.5, 5.2)), (N, (1.2, -10.5, 4.2))])
    key_loc(tgt, [(1, (0.6, -0.6, 2.2)), (N, (0.6, -0.6, 2.0))])
    smooth(cam)
    bloom(0.6, 0.8)


def build():
    lens = SHOT.get("lens", 35)
    cam, tgt = camera(lens, SHOT.get("fstop", 1.4), SHOT.get("shift_y", 0.0))
    if KIND == "chilli_macro":
        cam.data.dof.aperture_fstop = SHOT.get("fstop", 4.0)
        return shot_chilli_macro(cam, tgt)
    if KIND == "nerve_pulse":
        return shot_nerve_pulse(cam, tgt)
    for prefix, mod in (("mosq_", "micro_bugs"), ("wp_", "micro_birds"), ("gk_", "micro_gecko"), ("pc_", "micro_pop"), ("lf_", "micro_leid")):   # topic modules, same helpers
        if KIND.startswith(prefix):
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            m_ = __import__(mod)
            m_.install(globals())
            return m_.build(cam, tgt)
    chans, _ = membrane_world()
    {"membrane_dive": shot_membrane_dive, "heat_open": shot_heat_open, "capsaicin_open": shot_capsaicin_open,
     "channel_orbit": shot_channel_orbit, "capsaicin_leave": shot_capsaicin_leave, "pull_back": shot_pull_back,
     "cold_tease": shot_cold_tease}[KIND](cam, tgt, chans)
    if KIND == "channel_orbit" and SHOT.get("gold"):
        area_light((-6, 8, 10), (0, 0, 0), 6000, (1.0, 0.8, 0.35), 8)


def render():
    os.makedirs(args.out, exist_ok=True)
    f0 = max(1, args.start or 1)
    f1 = N if args.end < 0 else min(N, args.end)
    for fr in range(f0, f1 + 1):
        p = os.path.join(args.out, f"{fr:05d}.png")
        if os.path.exists(p):
            continue
        SC.frame_set(fr)
        SC.render.filepath = p
        bpy.ops.render.render(write_still=True)
    print(f"rendered shot {args.shot} frames {f0}-{f1} of {N}")


build()
if os.environ.get("HERO_SAVE_BLEND"):
    bpy.ops.wm.save_as_mainfile(filepath=os.environ["HERO_SAVE_BLEND"])
render()
