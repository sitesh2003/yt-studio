"""Popcorn shots for micro.py (25 Nov 2026). Virot & Ponomarenko 2015, J R Soc Interface 12:20141247.

Units are centimetres (a kernel ~0.6 cm, a popped flake ~2 cm). Everything procedural.
Kinds: pc_pan (kernels on a hot pan; `pops` = how many burst and jump during the shot), pc_cut (a cut-away kernel:
hard hull, starch, water droplets turning to steam bubbles as it heats; `burst` ends with the crack),
pc_burst (one kernel, very slow motion: crack, starch foam, the LEG pressing on the pan, squash, launch),
pc_steam (the pop: steam puffs out at the crack while sound rings spread).
"""
import math
import random

from mathutils import Vector

KINDS = ("pc_pan", "pc_cut", "pc_burst", "pc_steam")


def install(g):
    mine = set(globals())
    globals().update({k: v for k, v in g.items() if not k.startswith("__") and k not in mine})


def mats():
    if "Hull" in bpy.data.materials:
        return [bpy.data.materials[n] for n in ("Hull", "Foam", "Pan", "Tip")]
    hull = bpy.data.materials.new("Hull")
    hull.use_nodes = True
    b = hull.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.85, 0.42, 0.04, 1)
    b.inputs["Roughness"].default_value = 0.22
    if "Coat Weight" in b.inputs:
        b.inputs["Coat Weight"].default_value = 0.8
    if "Subsurface Weight" in b.inputs:
        b.inputs["Subsurface Weight"].default_value = 0.3
    foam = organic("Foam", (0.95, 0.9, 0.78), (1.0, 0.95, 0.8), 0.15, sss=0.9, noise=9, rough=0.7)
    fb = foam.node_tree.nodes["Principled BSDF"]
    if "Coat Weight" in fb.inputs:
        fb.inputs["Coat Weight"].default_value = 0.0
    pan = bpy.data.materials.new("Pan")
    pan.use_nodes = True
    pb = pan.node_tree.nodes["Principled BSDF"]
    pb.inputs["Base Color"].default_value = (0.03, 0.03, 0.035, 1)
    pb.inputs["Metallic"].default_value = 0.9
    pb.inputs["Roughness"].default_value = 0.35
    tip = bpy.data.materials.new("Tip")
    tip.use_nodes = True
    tip.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.9, 0.8, 0.6, 1)
    return hull, foam, pan, tip


def kernel(name, loc, s=1.0):
    """A popcorn kernel: a rounded teardrop of glossy orange hull with a pale tip (where it was attached)."""
    hull, foam, pan, tip = mats()
    root = empty(name, loc)
    root.scale = (s, s, s)
    k = blob(name + "h", 0.3, (0, 0, 0.26), (1.0, 0.8, 1.15), hull, 0.02, 3, parent=root)
    tp = k.modifiers.new("Tear", "SIMPLE_DEFORM")      # a teardrop: narrow at the tip, round at the crown
    tp.deform_method = "TAPER"
    tp.factor = 0.9
    tp.deform_axis = "Z"
    blob(name + "t", 0.09, (0, 0, -0.06), (1, 0.8, 0.7), tip, 0, parent=root)
    return root, k


def flake(name, at, parent=None, n=9, r=0.75):
    """A popped flake: a fused cloud of foam lobes (metaballs). Returns the metaball object."""
    hull, foam, pan, tip = mats()
    mb = bpy.data.metaballs.new(name)
    mb.resolution = 0.06
    mb.render_resolution = 0.03
    mb.threshold = 0.6
    for i in range(n):
        e = mb.elements.new()
        d = Vector((random.gauss(0, 1), random.gauss(0, 1), random.gauss(0, 1))).normalized()
        e.co = d * r * random.uniform(0.3, 0.8)
        e.radius = r * random.uniform(0.45, 0.7)
    o = bpy.data.objects.new(name, mb)
    SC.collection.objects.link(o)
    o.data.materials.append(foam)
    o.location = at
    if parent:
        o.parent = parent
    return o


def kitchen(warm=0.0):
    world((0.03, 0.02, 0.015))
    hull, foam, pan, tip = mats()
    bpy.ops.mesh.primitive_cylinder_add(vertices=128, radius=14, depth=0.5, location=(0, 0, -0.25))
    p = bpy.context.object
    p.data.materials.append(pan)
    heat = glow("Heat", (1.0, 0.3, 0.05), 0.0)
    bpy.ops.mesh.primitive_torus_add(major_radius=10, minor_radius=1.2, location=(0, 0, -1.3))
    h = bpy.context.object
    h.data.materials.append(heat)
    key_input(emis_input(heat), [(1, 2.0 + 6 * warm), (N, 3.0 + 6 * warm)])
    area_light((12, -14, 18), (0, 0, 0), 2.5e3, (1.0, 0.9, 0.78), 12)
    area_light((-14, 8, 8), (0, 0, 0), 900, (0.6, 0.75, 1.0), 12)
    area_light((0, 14, 4), (0, 0, 0), 1.2e3, (1.0, 0.6, 0.3), 10)
    bloom(0.5, 0.9)


def pop(name, at, f_pop, hop=6.0, side=(0.0, 0.0)):
    """One kernel pops at f_pop: foam swells out, a leg presses on the pan, squashes, and the flake jumps."""
    root, k = kernel(name, at)
    for fr in range(1, f_pop, 2):                             # jiggles as the pressure builds
        root.rotation_euler = (random.uniform(-0.08, 0.08), random.uniform(-0.08, 0.08), random.uniform(0, 0.2))
        root.keyframe_insert("rotation_euler", frame=fr)
    fl = flake(name + "F", (0, 0, 0.45), root, r=1.0)
    leg = flake(name + "L", (0, 0, 0.0), root, n=4, r=0.32)
    for i_, e in enumerate(leg.data.elements):        # the leg: a short column of foam from the crack down to the pan
        e.co = (random.uniform(-0.05, 0.05), random.uniform(-0.05, 0.05), -0.12 - i_ * 0.16)
        e.radius = 0.3
    for o, s0_, s1_ in ((fl, 0.01, 1.0), (leg, 0.01, 1.0)):
        o.scale = (s0_, s0_, s0_)
        o.keyframe_insert("scale", frame=f_pop)
        o.scale = (s1_, s1_, s1_)
        o.keyframe_insert("scale", frame=f_pop + 4)
    leg.scale = (1.3, 1.3, 0.45)                             # the leg squashes on the pan ...
    leg.keyframe_insert("scale", frame=f_pop + 7)
    leg.scale = (0.9, 0.9, 1.25)                             # ... and pushes back
    leg.keyframe_insert("scale", frame=f_pop + 10)
    k.scale = (1.0, 0.8, 1.15)
    k.keyframe_insert("scale", frame=f_pop)
    k.scale = (0.6, 0.5, 0.5)                                # the hull splits back behind the foam
    k.keyframe_insert("scale", frame=f_pop + 4)
    t0 = f_pop + 10
    lift = Vector(at) + Vector((0, 0, 0.62))          # the growing leg lifts the kernel off the pan ...
    pts = [(f_, lift + Vector((side[0] * (f_ - t0) / 30, side[1] * (f_ - t0) / 30,
                               max(0.0, hop * 4 * ((f_ - t0) / 30) * (1 - (f_ - t0) / 30)))))
           for f_ in range(t0, t0 + 31, 2)]
    key_loc(root, [(1, at), (f_pop, at), (f_pop + 4, lift), (f_pop + 7, Vector(at) + Vector((0, 0, 0.34))),
                   (t0, lift)] + pts)                 # ... squashes it down, then springs it up and away
    linear(root)
    spin = random.choice((-1, 1)) * random.uniform(4, 8)
    root.keyframe_insert("rotation_euler", frame=t0)
    root.rotation_euler = (spin, spin * 0.5, 0)
    root.keyframe_insert("rotation_euler", frame=t0 + 30)
    return root


def shot_pan(cam, tgt):
    kitchen(0.4)
    pops = int(SHOT.get("pops", 0))
    spots = []
    for i in range(46):
        while True:
            p = Vector((random.uniform(-7, 7), random.uniform(-7, 7), 0.05))
            if p.length < 7.5 and all((p - q).length > 1.0 for q in spots):
                break
        spots.append(p)
    for i, p in enumerate(spots):
        if i < pops:
            pop(f"K{i}", p, F(random.uniform(0.15, 0.8)), random.uniform(4, 8),
                (random.uniform(-3, 3), random.uniform(-3, 3)))
        else:
            r, _ = kernel(f"K{i}", p)
            r.rotation_euler = (math.pi / 2 * random.choice((0, 1)), random.uniform(0, 3), random.uniform(0, 6))
            for fr in range(1, N + 1, 3):
                r.location = p + Vector((0, 0, random.uniform(0, 0.04)))
                r.keyframe_insert("location", frame=fr)
    key_loc(cam, [(1, (0, -15, 9)), (N, (1, -12, 7))])
    key_loc(tgt, [(1, (0, 0, 0.5))])
    smooth(cam)
    cam.data.dof.aperture_fstop = 2.8


def shot_cut(cam, tgt):
    """A kernel cut in half: hull, starch inside, water droplets that turn into growing steam bubbles."""
    kitchen(0.6)
    hull, foam, pan, tip = mats()
    root = empty("CutK", (0, 0, 1.6))
    root.scale = (5, 5, 5)                                   # magnified 5x
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=0.3, location=(0, 0, 0.26))
    sh = bpy.context.object
    sh.scale = (1.0, 0.8, 1.15)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    sh.location = (0, 0, 0.26)
    sol = sh.modifiers.new("Shell", "SOLIDIFY")
    sol.thickness = 0.035
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.5, 0.26))
    cutter = bpy.context.object
    cutter.parent = root
    cutter.hide_render = True
    cutter.hide_viewport = True
    bo = sh.modifiers.new("Cut", "BOOLEAN")
    bo.object = cutter
    bo.operation = "DIFFERENCE"
    sh.data.materials.append(hull)
    sh.parent = root
    starch = organic("Starch", (0.95, 0.85, 0.55), (1.0, 0.8, 0.4), 0.3, sss=0.8, noise=12)
    for i in range(70):
        p = Vector((random.uniform(-0.24, 0.24), random.uniform(0.0, 0.2), random.uniform(0.0, 0.55)))
        if ((p.x / 0.26) ** 2 + (p.y / 0.21) ** 2 + ((p.z - 0.26) / 0.31) ** 2) < 1:
            blob(f"st{i}", 0.035, p, (1, 1, 1), starch, 0.01, 2, subdiv=2, parent=root)
    water = glow("Water", (0.4, 0.75, 1.0), 2.0)
    steam = bpy.data.materials.new("Steam")
    steam.use_nodes = True
    sb = steam.node_tree.nodes["Principled BSDF"]
    sb.inputs["Base Color"].default_value = (0.9, 0.95, 1.0, 1)
    sb.inputs["Alpha"].default_value = 0.35
    sb.inputs["Emission Color"].default_value = (0.8, 0.9, 1.0, 1)
    sb.inputs["Emission Strength"].default_value = 1.2
    try:
        steam.surface_render_method = "BLENDED"
    except Exception:
        pass
    for i in range(18):
        p = Vector((random.uniform(-0.18, 0.18), random.uniform(0.0, 0.12), random.uniform(0.08, 0.45)))
        d = blob(f"w{i}", 0.02, p, (1, 1, 1), water, 0, parent=root)
        b = blob(f"b{i}", 0.02, p, (1, 1, 1), steam, 0, parent=root)
        f_ = F(random.uniform(0.15, 0.6))
        d.scale = (1, 1, 1)
        d.keyframe_insert("scale", frame=f_)
        d.scale = (0.01, 0.01, 0.01)
        d.keyframe_insert("scale", frame=f_ + 8)
        b.scale = (0.01, 0.01, 0.01)
        b.keyframe_insert("scale", frame=f_)
        b.scale = (2.6, 2.6, 2.6)
        b.keyframe_insert("scale", frame=min(N, f_ + int(N * 0.35)))
    if SHOT.get("burst"):                                    # the hull gives way at the end
        crack = glow("Crack", (1.0, 0.9, 0.6), 0.0)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0.1, 0.0, 0.5))
        c = bpy.context.object
        c.scale = (0.012, 0.25, 0.22)
        c.rotation_euler = (0, 0.4, 0)
        c.data.materials.append(crack)
        c.parent = root
        key_input(emis_input(crack), [(1, 0), (F(0.8), 0), (F(0.85), 20), (N, 30)])
    key_loc(cam, [(1, (0, -14, 4.5)), (N, (0, -11, 4))])
    key_loc(tgt, [(1, (0, 0, 2.9))])
    smooth(cam)
    cam.data.dof.aperture_fstop = 5.6


def shot_burst(cam, tgt):
    kitchen(0.6)
    hero = pop("Hero", (0, 0, 0.05), F(0.18), 5.0, (1.2, 0.4))
    for i in range(10):                                      # neighbours, out of focus
        p = Vector((random.uniform(-6, 6), random.uniform(2, 8), 0.05))
        kernel(f"N{i}", p)
    key_loc(cam, [(1, (2.6, -6.0, 1.4)), (N, (4.0, -10.5, 3.6))])
    key_loc(tgt, [(1, (0, 0, 0.0))])
    c_ = tgt.constraints.new("COPY_LOCATION")       # the camera keeps the jumping kernel in frame
    c_.target = hero
    c_.influence = 0.8
    smooth(cam)
    cam.data.lens = 60
    cam.data.dof.aperture_fstop = 2.0


def shot_steam(cam, tgt):
    kitchen(0.6)
    f_pop = F(0.25)
    pop("Hero", (0, 0, 0.05), f_pop, 5.0, (0.8, 0.2))
    steam = bpy.data.materials.get("Puff") or bpy.data.materials.new("Puff")
    steam.use_nodes = True
    sb = steam.node_tree.nodes["Principled BSDF"]
    sb.inputs["Base Color"].default_value = (0.95, 0.97, 1.0, 1)
    sb.inputs["Alpha"].default_value = 0.12
    sb.inputs["Emission Color"].default_value = (1, 1, 1, 1)
    sb.inputs["Emission Strength"].default_value = 0.5
    try:
        steam.surface_render_method = "BLENDED"
    except Exception:
        pass
    for i in range(40):                                      # the steam jet at the crack
        o = blob(f"puff{i}", 0.12, (0, 0, 0.4), (1, 1, 1), steam, 0.03, 2, subdiv=2)
        f0 = f_pop + random.randint(0, 4)
        d = Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(0.3, 1.5))).normalized()
        o.scale = (0.01, 0.01, 0.01)
        o.keyframe_insert("scale", frame=1)
        o.keyframe_insert("scale", frame=f0)
        o.scale = (2.5, 2.5, 2.5)
        o.keyframe_insert("scale", frame=f0 + 25)
        key_loc(o, [(f0, (0, 0, 0.4)), (f0 + 25, Vector((0, 0, 0.4)) + d * random.uniform(2, 4))])
    ring = glow("Sound", (0.6, 0.85, 1.0), 2.0)
    for k in range(3):                                       # sound rings spreading from the pop
        bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.012, location=(0, 0, 0.5))
        t = bpy.context.object
        t.rotation_euler = (math.pi / 2, 0, 0)
        t.data.materials.append(ring)
        f0 = f_pop + k * 5
        t.scale = (0.01, 0.01, 0.01)
        t.keyframe_insert("scale", frame=1)
        t.keyframe_insert("scale", frame=f0)
        t.scale = (9, 9, 9)
        t.keyframe_insert("scale", frame=f0 + 30)
    key_loc(cam, [(1, (2.5, -9, 2.5)), (N, (3.5, -11, 3.2))])
    key_loc(tgt, [(1, (0, 0, 1.0))])
    smooth(cam)
    cam.data.lens = 45
    cam.data.dof.aperture_fstop = 2.8


def build(cam, tgt):
    {"pc_pan": shot_pan, "pc_cut": shot_cut, "pc_burst": shot_burst, "pc_steam": shot_steam}[KIND](cam, tgt)
