"""Woodpecker shots for micro.py (25 Nov 2026), Van Wassenbergh et al. 2022 Current Biology 32:3189.

A procedural great spotted woodpecker (black back, white shoulder patches and cheeks, red under the tail and on the
nape) clinging to a bark trunk, its stiff tail pressed on the bark. Units are centimetres (the bird is ~23 cm).

Kinds: wp_peck (slow-motion pecking; `markers` = the two tracking dots the high-speed films follow, `rate` pecks per
second of screen time, `wide` for a forest shot), wp_xray (side x-ray: skull, beak bone and brain stop together;
`ghost` adds the cushion that never happens: a blue head that keeps moving after the beak stops),
wp_brains (the same hit on a small woodpecker brain and a big human brain: the big one turns red).
"""
import math
import random

from mathutils import Vector

KINDS = ("wp_peck", "wp_xray", "wp_brains")


def install(g):
    mine = set(globals())
    globals().update({k: v for k, v in g.items() if not k.startswith("__") and k not in mine})


def plain(name, rgb, rough=0.55, coat=0.0):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    if "Coat Weight" in b.inputs:
        b.inputs["Coat Weight"].default_value = coat
    if "Sheen Weight" in b.inputs:
        b.inputs["Sheen Weight"].default_value = 0.6       # feathers
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (9.0, 9.0, 2.2)    # stretched along the body: feather barbs
    wv = nt.nodes.new("ShaderNodeTexWave")
    wv.inputs["Scale"].default_value = 4.0
    wv.inputs["Distortion"].default_value = 6.0
    wv.inputs["Detail"].default_value = 4.0
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.25
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], wv.inputs["Vector"])
    nt.links.new(wv.outputs["Fac"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


def xray(name, rgb, strength=1.5, alpha=0.25):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Emission Color"].default_value = (*rgb, 1)
    fres = nt.nodes.new("ShaderNodeLayerWeight")
    fres.inputs["Blend"].default_value = 0.35
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = strength * 4
    nt.links.new(fres.outputs["Facing"], mul.inputs[0])
    nt.links.new(mul.outputs[0], b.inputs["Emission Strength"])
    b.inputs["Alpha"].default_value = alpha
    try:
        m.surface_render_method = "BLENDED"
    except Exception:
        pass
    return m


# ---------------------------------------------------------------- the bird
def _meta(name, parts, m, parent=None):
    """One metaball object; objects sharing a base name (Wp, Wp.001) fuse into one smooth surface."""
    mb = bpy.data.metaballs.new(name)
    mb.resolution = 0.35
    mb.render_resolution = 0.18
    mb.threshold = 0.6
    for co, r, sz in parts:
        e = mb.elements.new()
        e.type = "ELLIPSOID"
        e.co = co
        e.radius = r
        e.size_x, e.size_y, e.size_z = sz
        e.stiffness = 2.0
    o = bpy.data.objects.new(name, mb)
    SC.collection.objects.link(o)
    o.data.materials.append(m)
    if parent:
        o.parent = parent
    return o


def woodpecker(name, holo=True):
    """Facing +Y toward the trunk; the neck pivot (returned) swings the head and beak in a peck.
    One smooth metaball body (head fused on), stiff tail on the bark, chisel beak; holo = the x-ray scan look
    with the braincase and the small brain visible inside the head."""
    if LOOK == "v2" and not holo and SHOT.get("bird_v2"):   # 28 Nov 2026: WORK IN PROGRESS (micro_woodpecker.py) -
        # marks and feathers placed, but the body still reads as a smooth toy until it gets a contour-feather coat;
        # so it is used only when a shot asks for it explicitly
        import micro_woodpecker
        return micro_woodpecker.woodpecker2(name)
    if holo:
        plum = xray("WpPlumX", (0.35, 0.75, 1.0), 1.2, 0.14)
        red = glow("WpRedX", (1.0, 0.25, 0.2), 1.6)
        beakm = xray("WpBeakX", (1.0, 0.8, 0.3), 2.2, 0.5)
    else:
        plum = plain("WpBlack", (0.012, 0.012, 0.015), 0.45)
        red = plain("WpRed", (0.75, 0.03, 0.03), 0.5)
        beakm = plain("WpBeak", (0.10, 0.10, 0.11), 0.3, 0.3)
    root = empty(name)
    base = "Wp" + name
    _meta(base, [((0, 0.4, 0.5), 3.0, (0.85, 1.0, 2.3)),        # body, upright
                 ((0, 1.0, 3.6), 2.2, (0.9, 0.9, 1.1)),         # upper breast toward the neck
                 ((0, 2.4, -7.5), 1.6, (0.9, 0.35, 2.4)),       # stiff tail down the bark
                 ((0, 1.2, -3.5), 2.2, (0.95, 1.0, 1.4))], plum, root)
    for sx in (-1, 1):                     # wings folded along the sides
        _meta(base, [((sx * 2.2, 0.9, -0.8), 1.6, (0.4, 1.0, 3.2))], plum, root)
    for sx in (-1, 1):                     # zygodactyl feet gripping the bark
        for dz, dy in ((0.4, 1.0), (-0.6, 1.2)):
            _stick(name + "toe", (sx * 1.4, 2.0, -4.0), (sx * 1.7, 3.6 + dy, -4.0 + dz * 2), 0.18, beakm, root)
    blob(name + "vent", 0.9, (0, 0.6, -5.2), (1.2, 1.0, 1.0), red, 0, parent=root)
    neck = empty(name + "neck", (0, 0.8, 5.0))
    neck.parent = root
    _meta(base, [((0, 0.4, 0.8), 1.6, (1.0, 1.0, 1.2)),         # neck, fuses into the body
                 ((0, 1.4, 2.6), 2.2, (0.95, 1.15, 1.0))], plum, neck)   # head
    blob(name + "nape", 0.7, (0, -0.4, 3.5), (1.2, 1.0, 0.9), red, 0, parent=neck)
    for sx in (-1, 1):
        blob(name + "eye", 0.34, (sx * 1.75, 2.6, 2.9), (1, 1, 1), glow("WpEyeX", (0.9, 0.95, 1.0), 6.0), 0, parent=neck)
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.7, radius2=0.04, depth=3.8, location=(0, 5.3, 2.3))
    bk = bpy.context.object
    bk.name = name + "beak"
    bk.rotation_euler = (-math.pi / 2, 0, 0)
    bk.scale = (1.0, 0.75, 1.0)
    bk.data.materials.append(beakm)
    bk.parent = neck
    if holo:                               # inside the head: the braincase and the small brain
        blob(name + "skullX", 1.0, (0, 1.2, 2.7), (1.5, 1.9, 1.5), xray(name + "skx", (0.95, 0.95, 1.0), 1.8, 0.2), 0, parent=neck)
        blob(name + "brainX", 1.0, (0, 0.9, 2.8), (0.95, 1.2, 1.0),
             organic(name + "brx", (1.0, 0.5, 0.55), (1.0, 0.45, 0.5), 3.0, sss=0.8, noise=6), 0.08, 4, parent=neck)
    return root, neck


def _stick(name, a, b, r, m, parent):
    a, b = Vector(a), Vector(b)
    d = b - a
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=r, depth=d.length, location=(a + b) / 2)
    o = bpy.context.object
    o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    o.data.materials.append(m)
    o.parent = parent
    return o


def trunk(y=12.5, r=11):
    bark = organic("Bark", (0.16, 0.11, 0.07), (0, 0, 0), 0.0, sss=0.0, noise=3, rough=0.85)
    b = bark.node_tree.nodes["Principled BSDF"]
    if "Coat Weight" in b.inputs:
        b.inputs["Coat Weight"].default_value = 0.0
    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=r, depth=300, location=(0, y, 0))
    t = bpy.context.object
    t.modifiers.new("S", "SUBSURF").levels = 2
    tex = bpy.data.textures.new("BarkT", "VORONOI")
    tex.noise_scale = 1.8
    d = t.modifiers.new("D", "DISPLACE")
    d.texture = tex
    d.strength = 0.9
    t.data.materials.append(bark)
    for p in t.data.polygons:
        p.use_smooth = True
    return t


def peck_keys(neck, rate, f0=1, strike_deg=24, back_deg=-18, hit_frac=0.32):
    """A peck: draw back, strike, an instant stop on the wood (the stiff hammer), recoil. Returns hit frames."""
    period = max(6, int(round(FPS / rate)))
    hits = []
    fr = f0
    while fr < N + period:
        back = fr
        hit = fr + int(period * hit_frac)
        rec = hit + max(2, int(period * 0.25))
        for f_, ang in ((back, back_deg), (hit, strike_deg), (hit + 1, strike_deg), (rec, back_deg * 0.4)):
            neck.rotation_euler = (math.radians(ang), 0, 0)
            neck.keyframe_insert("rotation_euler", frame=f_)
        hits.append(hit)
        fr += period
    ad = neck.animation_data
    for fc in _fcurves(ad.action):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"         # constant speed in, dead stop at the wood
    return hits


def chips(hits, at, m):
    for i, h in enumerate(hits[:12]):
        for k in range(6):
            o = blob(f"chip{i}_{k}", 0.25, at, (1, 0.4, 0.6), m, 0.05, 2)
            o.hide_render = True
            o.keyframe_insert("hide_render", frame=1)
            o.hide_render = False
            o.keyframe_insert("hide_render", frame=h)
            v = Vector((random.uniform(-4, 4), random.uniform(-6, -2), random.uniform(-1, 4)))
            key_loc(o, [(h, at), (h + 12, Vector(at) + v), (h + 24, Vector(at) + v * 1.4 + Vector((0, 0, -6)))])
            linear(o)


def forest_world():
    world((0.35, 0.45, 0.55), 0.6)
    area_light((-40, -60, 80), (0, 0, 0), 2.5e4, (1.0, 0.92, 0.8), 60)
    area_light((60, -20, 20), (0, 0, 0), 6e3, (0.6, 0.75, 1.0), 40)
    bark = bpy.data.materials.get("Bark")
    for i in range(10):                    # background trunks, out of focus
        x, y = random.uniform(-120, 120), random.uniform(60, 220)
        bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=random.uniform(6, 14), depth=400, location=(x, y, 0))
        bpy.context.object.data.materials.append(bark)
    bloom(0.4, 1.0)


# ---------------------------------------------------------------- shots
def shot_peck(cam, tgt):
    trunk()
    forest_world()
    SC.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.01, 0.015, 0.03, 1)
    real = LOOK == "v2" and bool(SHOT.get("bird_v2"))
    bird, neck = woodpecker("W", holo=not real)          # the feathered bird only when asked; else the scan look
    if real:
        SC.view_settings.exposure = float(SHOT.get("exposure", 1.3))   # black plumage: open up a stop and a bit
    bird.location = (0, -1.6, 0)          # tail and feet on the bark, leaning back; the beak reaches the bark
    bird.rotation_euler = (0.2, 0, 0)
    rate = float(SHOT.get("rate", 2.0))
    hits = peck_keys(neck, rate, 1)
    tip = (0, 1.2, 7.5)
    chips(hits, tip, plain("Chip", (0.55, 0.42, 0.28), 0.8))
    if SHOT.get("markers"):                # the high-speed tracking dots: beak tip and back of the skull
        for nm, p, col in (("mk_beak", (0, 5.9, 2.2), (1.0, 0.85, 0.1)), ("mk_head", (0, -1.6, 2.6), (0.2, 0.9, 1.0))):
            o = blob(nm, 0.45, p, (1, 1, 1), glow(nm, col, 12), 0, parent=neck)
    if SHOT.get("wide"):
        key_loc(cam, [(1, (-55, -30, 12)), (N, (-46, -24, 10))])
        key_loc(tgt, [(1, (0, 4, 2))])
        cam.data.dof.aperture_fstop = 5.6
    else:
        key_loc(cam, [(1, (-44, -4, 5)), (N, (-38, -6, 4))])
        key_loc(tgt, [(1, (0, -1.5, 0))])
        cam.data.dof.aperture_fstop = 4.0
    smooth(cam)
    cam.data.lens = 50


def _xray_head(name, col_skull, col_brain, at):
    if LOOK == "v2":                      # a real skull with the hyoid horns (micro_woodpecker.xray_skull)
        import micro_woodpecker
        return micro_woodpecker.xray_skull(name, col_skull, col_brain, at, xray, organic, glow, blob)
    root = empty(name, at)
    skull = blob(name + "skull", 1.0, (0, 0, 0), (2.6, 2.9, 2.7), xray(name + "sk", col_skull, 1.2, 0.18), 0, parent=root)
    brain = blob(name + "brain", 1.0, (0, -0.3, 0.3), (1.6, 1.9, 1.5), organic(name + "br", col_brain, col_brain, 2.0, sss=0.8, noise=6), 0.08, 4, parent=root)
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.75, radius2=0.04, depth=3.6, location=(0, 4.0, -0.2))
    bk = bpy.context.object
    bk.rotation_euler = (-math.pi / 2, 0, 0)
    bk.data.materials.append(xray(name + "bk", col_skull, 1.5, 0.35))
    bk.parent = root
    for nm, p, col in (("b", (0, 5.6, -0.2), (1.0, 0.85, 0.1)), ("h", (0, -2.9, 0.4), (0.2, 0.9, 1.0))):
        blob(name + "mk" + nm, 0.32, p, (1, 1, 1), glow(name + "mk" + nm, col, 14), 0, parent=root)
    return root, brain


def shot_xray(cam, tgt):
    world((0.004, 0.008, 0.02))
    wood = xray("WoodX", (0.9, 0.55, 0.2), 0.8, 0.3)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 10.5, 0))
    w = bpy.context.object
    w.scale = (14, 4, 30)
    w.data.materials.append(wood)
    ghost = bool(SHOT.get("ghost"))
    xs = (5.5, -5.5) if ghost else (0,)          # used as heights: cushion on top, real below
    period = int(FPS / float(SHOT.get("rate", 1.2)))
    for k, x in enumerate(xs):
        cushion = ghost and k == 0
        col = (0.35, 0.65, 1.0) if cushion else (0.9, 0.95, 1.0)
        head, brain = _xray_head(f"H{k}", col, (1.0, 0.55, 0.6) if not cushion else (0.6, 0.7, 1.0), (0, 0, x))
        fr = 1
        while fr < N + period:
            hit = fr + int(period * 0.4)
            # the whole head moves at speed and stops dead on the wood (beak tip touches at y ~ 8.5)
            key_loc(head, [(fr, (0, -4, x)), (hit, (0, 2.9, x)), (hit + int(period * 0.3), (0, 2.9, x)),
                           (fr + period - 1, (0, -4, x))])
            if cushion:                        # what a cushion would mean: the head keeps going, squashing
                for f_, s in ((hit, 1.0), (hit + 4, 0.72), (hit + 10, 1.0)):
                    head.scale = (1.0 + (1 - s) * 0.5, s, 1.0 + (1 - s) * 0.3)
                    head.keyframe_insert("scale", frame=f_)
            fr += period
        linear(head)
    area_light((-20, -20, 20), (0, 0, 0), 3e3, (0.6, 0.8, 1.0), 20)
    if SHOT.get("orbit"):
        key_loc(cam, [(1, (-34, -8, 8)), (N, (-26, -24, 10))])
    else:
        key_loc(cam, [(1, (-36, 2, 4)), (N, (-34, 0, 3.5))])
    key_loc(tgt, [(1, (0, 2, 0))])
    smooth(cam)
    cam.data.lens = 45 if ghost else 55
    cam.data.dof.aperture_fstop = 8.0
    bloom(0.7, 0.6)


def shot_brains(cam, tgt):
    """Same hit, two brain sizes: a woodpecker's (~2 g) and a human's (~1,400 g, drawn at the same scale)."""
    world((0.004, 0.006, 0.018))
    hit = int(N * 0.35)
    for nm, x, r in (("small", -9, 1.2), ("big", 6, 8.0)):
        m = organic("Br" + nm, (0.85, 0.55, 0.6), (0.4, 0.7, 1.0), 1.0, sss=0.9, noise=2.5 / r * 4)
        b = blob("Brain" + nm, r, (x, 0, r), (1.0, 1.25, 0.8), m, 0.12 * r, 1.3 * r)
        # the hit: both jolt the same amount; pressure glows from the inside, far more in the big one
        e = m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
        col = m.node_tree.nodes["Principled BSDF"]
        peak = 9.0 if nm == "big" else 1.2
        key_input(e, [(1, 0.6), (hit, 0.6), (hit + 3, peak), (hit + 30, peak * 0.5), (N, peak * 0.4)])
        ramp = [n_ for n_ in m.node_tree.nodes if n_.type == "VALTORGB"][0]
        ramp.color_ramp.elements[1].color = (1.0, 0.15, 0.08, 1) if nm == "big" else (0.4, 0.75, 1.0, 1)
        key_loc(b, [(1, (x, 0, r)), (hit, (x, 0, r)), (hit + 2, (x, 1.5, r)), (hit + 8, (x, 0, r))])
        linear(b)
    area_light((-20, -30, 30), (0, 0, 4), 4e3, (1.0, 0.9, 0.85), 20)
    area_light((25, -10, 10), (0, 0, 4), 1.5e3, (0.4, 0.6, 1.0), 20)
    key_loc(cam, [(1, (-2, -42, 18)), (N, (-1, -36, 15))])
    key_loc(tgt, [(1, (-1, 0, 5))])
    smooth(cam)
    cam.data.dof.aperture_fstop = 8.0
    bloom(0.8, 0.7)


def build(cam, tgt):
    {"wp_peck": shot_peck, "wp_xray": shot_xray, "wp_brains": shot_brains}[KIND](cam, tgt)
