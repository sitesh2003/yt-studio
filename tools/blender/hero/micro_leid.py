"""Leidenfrost shots for micro.py (25 Nov 2026): a STYLISED cut-away, no fluid simulation (council, 25 Nov).
Quéré 2013 Annu Rev Fluid Mech 45:197; Biance, Clanet & Quéré 2003 Phys Fluids 15:1632; Lagubeau et al. 2008.

Units are millimetres-ish (drops ~3 mm). Kinds: lf_pan (drops on a pan; `hot` False = they sizzle and shrink fast,
True = they skate around), lf_cut (one drop, side cut-away: the vapour film under it, steam streaming out at the rim,
heat arrows from the metal stopping at the film), lf_compare (warm pan left, hot pan right: the warm drop shrinks fast,
the hot one floats and lasts).
"""
import math
import random

from mathutils import Vector

KINDS = ("lf_pan", "lf_cut", "lf_compare")


def install(g):
    mine = set(globals())
    globals().update({k: v for k, v in g.items() if not k.startswith("__") and k not in mine})


def water_mat():
    m = bpy.data.materials.get("Water")
    if m:
        return m
    m = bpy.data.materials.new("Water")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.02, 0.06, 0.10, 1)   # a glassy bead: dark core, bright rim
    b.inputs["Roughness"].default_value = 0.02
    b.inputs["IOR"].default_value = 1.33
    if "Coat Weight" in b.inputs:
        b.inputs["Coat Weight"].default_value = 1.0
    nt = m.node_tree
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.3
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = 3.0
    nt.links.new(lw.outputs["Facing"], mul.inputs[0])
    b.inputs["Emission Color"].default_value = (0.45, 0.8, 1.0, 1)
    nt.links.new(mul.outputs[0], b.inputs["Emission Strength"])
    return m


def pan(r=60, glow_k=1.0):
    metal = bpy.data.materials.new("PanM")
    metal.use_nodes = True
    nt = metal.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.06, 0.06, 0.065, 1)
    b.inputs["Metallic"].default_value = 1.0
    b.inputs["Roughness"].default_value = 0.3
    b.inputs["Emission Color"].default_value = (1.0, 0.28, 0.05, 1)
    b.inputs["Emission Strength"].default_value = 0.02 * glow_k      # a faint red heat glow from the metal
    bpy.ops.mesh.primitive_cylinder_add(vertices=128, radius=r, depth=2, location=(0, 0, -1))
    p = bpy.context.object
    p.data.materials.append(metal)
    return p


def drop(name, at, r=1.6, flat=0.72):
    o = blob(name, r, (at[0], at[1], r * flat), (1, 1, flat), water_mat(), 0.02, 5)
    return o


def stage(tint=(0.02, 0.012, 0.01)):
    world(tint)
    area_light((30, -40, 50), (0, 0, 0), 1.5e3, (1.0, 0.92, 0.85), 30)
    area_light((-40, 20, 20), (0, 0, 0), 600, (0.5, 0.7, 1.0), 30)
    area_light((0, 0, -30), (0, 0, 0), 0, (1, 0.3, 0.05), 30)
    bloom(0.6, 0.85)


def steam_puffs(at, f0, f1, n=12, rise=8, m=None):
    m = m or glow("Steam", (0.9, 0.95, 1.0), 1.5)
    for i in range(n):
        fs = random.randint(f0, max(f0, f1 - 10))
        o = blob(f"st{len(bpy.data.objects)}", 0.35, at, (1, 1, 1), m, 0.05, 2, subdiv=2)
        o.scale = (0.01, 0.01, 0.01)
        o.keyframe_insert("scale", frame=1)
        o.keyframe_insert("scale", frame=fs)
        o.scale = (1.6, 1.6, 1.6)
        o.keyframe_insert("scale", frame=fs + 18)
        o.scale = (0.01, 0.01, 0.01)
        o.keyframe_insert("scale", frame=fs + 30)
        d = Vector((random.uniform(-1, 1), random.uniform(-1, 1), 0))
        key_loc(o, [(fs, Vector(at)), (fs + 30, Vector(at) + d * 2 + Vector((0, 0, rise)))])


def skate(o, start, f0=1, speed=4.0, bounds=18):
    """A drop gliding with almost no friction: straight lines, bouncing off an invisible rim."""
    p = Vector(start)
    v = Vector((random.uniform(-1, 1), random.uniform(-1, 1), 0)).normalized() * speed / FPS
    for fr in range(f0, N + 1, 2):
        p += v * 2
        if abs(p.x) > bounds:
            v.x *= -1
        if abs(p.y) > bounds:
            v.y *= -1
        o.location = (p.x, p.y, o.location.z)
        o.keyframe_insert("location", frame=fr)
        o.rotation_euler = (0, 0, fr * 0.05)
        o.keyframe_insert("rotation_euler", frame=fr)
    linear(o)


def sizzle(o, f0, f1, at):
    """A drop in contact with a merely warm pan: it flattens, boils violently and is gone fast."""
    s = o.scale.copy()
    o.keyframe_insert("scale", frame=f0)
    o.scale = (s.x * 1.25, s.y * 1.25, s.z * 0.6)
    o.keyframe_insert("scale", frame=f0 + 6)
    o.scale = (0.01, 0.01, 0.01)
    o.keyframe_insert("scale", frame=f1)
    steam_puffs(at, f0, f1, 16, 10)
    m = glow("Bubble", (0.9, 0.97, 1.0), 2.0)
    for i in range(10):                                    # boiling bubbles at the contact
        b = blob(f"bb{len(bpy.data.objects)}", 0.18, (at[0] + random.uniform(-1, 1), at[1] + random.uniform(-1, 1), 0.3),
                 (1, 1, 1), m, 0, subdiv=2)
        fs = random.randint(f0, max(f0, f1 - 4))
        b.scale = (0.01, 0.01, 0.01)
        b.keyframe_insert("scale", frame=1)
        b.keyframe_insert("scale", frame=fs)
        b.scale = (1.2, 1.2, 1.2)
        b.keyframe_insert("scale", frame=fs + 4)
        b.scale = (0.01, 0.01, 0.01)
        b.keyframe_insert("scale", frame=fs + 7)


def shot_pan(cam, tgt):
    hot = bool(SHOT.get("hot", True))
    stage()
    pan(glow_k=2.0 if hot else 0.6)
    for i in range(9):
        at = (random.uniform(-14, 14), random.uniform(-10, 14))
        d = drop(f"D{i}", at, random.uniform(1.0, 2.0), 0.8 if hot else 0.55)
        if hot:
            skate(d, d.location, speed=random.uniform(2, 6))
            # a few steam wisps lift off the rim of each floating drop
            steam_puffs((at[0], at[1], 0.6), 1, N, 3, 4)
        else:
            f0 = int(N * random.uniform(0.05, 0.4))
            sizzle(d, f0, f0 + int(FPS * random.uniform(0.6, 1.2)), (at[0], at[1], 0.5))
    key_loc(cam, [(1, (0, -40, 24)), (N, (2, -32, 18))])
    key_loc(tgt, [(1, (0, 2, 0.5))])
    smooth(cam)
    cam.data.dof.aperture_fstop = 4.0


def shot_cut(cam, tgt):
    """Side cut-away (magnified): drop, the vapour film beneath it (drawn thick enough to see), vapour streaming
    out at the edges, and heat arrows rising from the metal that fade at the film."""
    stage((0.01, 0.01, 0.02))
    pan(80, 2.5)
    film_m = glow("Film", (0.85, 0.95, 1.0), 1.2)
    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=7.2, depth=0.6, location=(0, 0, 0.3))
    film = bpy.context.object
    film.data.materials.append(film_m)
    d = blob("Drop", 8.0, (0, 0, 0.6 + 8.0 * 0.62), (1, 1, 0.62), water_mat(), 0.03, 5)
    key_loc(d, [(1, (0, 0, 0.6 + 4.96)), (F(0.5), (0, 0, 0.75 + 4.96)), (N, (0, 0, 0.62 + 4.96))])
    smooth(d)
    m = glow("Vap", (0.9, 0.97, 1.0), 2.0)
    for i in range(36):                                    # vapour escaping sideways from under the drop
        a = random.uniform(0, 2 * math.pi)
        o = blob(f"v{i}", 0.25, (6.5 * math.cos(a), 6.5 * math.sin(a), 0.3), (1, 1, 1), m, 0, subdiv=2)
        f0 = random.randint(-30, N)
        life = 30
        pts = []
        fr = f0
        while fr < N + life:
            pts += [(fr, (6.5 * math.cos(a), 6.5 * math.sin(a), 0.3)), (fr + life - 1, (12 * math.cos(a), 12 * math.sin(a), 3.5))]
            fr += life
        for fr_, p in pts:
            o.location = p
            o.keyframe_insert("location", frame=fr_)
        for fc in _fcurves(o.animation_data.action):
            for k, kp in enumerate(fc.keyframe_points):
                kp.interpolation = "LINEAR" if k % 2 == 0 else "CONSTANT"
    heat = glow("HeatArrow", (1.0, 0.4, 0.1), 4.0)
    for i in range(7):                                     # heat rising from the metal, stopped at the film
        x = -9 + i * 3
        bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=0.5, radius2=0.0, depth=1.2, location=(x, -2, -0.2))
        c = bpy.context.object
        c.data.materials.append(heat)
        key_loc(c, [(1 + i * 4, (x, -2, -1.5)), (31 + i * 4, (x, -2, 0.0))])
        for fc in _fcurves(c.animation_data.action):
            fc.modifiers.new("CYCLES")
    key_loc(cam, [(1, (0, -62, 6)), (N, (0, -54, 5))])
    key_loc(tgt, [(1, (0, 0, 3.5))])
    smooth(cam)
    cam.data.lens = 50
    cam.data.dof.aperture_fstop = 8.0


def shot_compare(cam, tgt):
    """Warm pan in front, hot pan behind (stacked for a vertical frame): the warm drop sizzles away fast,
    the hot one floats and is still there at the end."""
    stage()
    p1 = pan(17, 0.5)
    p1.location = (0, -20, -1)
    p2 = pan(17, 2.2)
    p2.location = (0, 20, -1)
    warm = drop("Warm", (0, -20), 4.0, 0.55)
    sizzle(warm, F(0.15), F(0.45), (0, -20, 1.0))
    hot = drop("Hot", (0, 20), 4.0, 0.82)
    key_loc(hot, [(1, (-3, 18, 3.3)), (F(0.5), (3, 22, 3.3)), (N, (-2, 23, 3.3))])
    smooth(hot)
    steam_puffs((0, 20, 1.2), 1, N, 6, 5)
    key_loc(cam, [(1, (0, -78, 70)), (N, (0, -70, 62))])
    key_loc(tgt, [(1, (0, 2, 0))])
    smooth(cam)
    cam.data.lens = 40
    cam.data.dof.aperture_fstop = 11.0


def build(cam, tgt):
    {"lf_pan": shot_pan, "lf_cut": shot_cut, "lf_compare": shot_compare}[KIND](cam, tgt)
