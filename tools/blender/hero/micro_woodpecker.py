"""Anatomy-first woodpecker (28 Nov 2026, step 4 of the council's 3D order).

Great Spotted Woodpecker (Dendrocopos major), adult male - one of the species measured in Van Wassenbergh et al.
(2022, Current Biology 32:3189, "Woodpeckers minimize cranial absorption of shocks"). Field marks (Svensson et al.,
Collins Bird Guide, 2nd ed.): black crown and back, buff forehead, RED NAPE patch (male), white cheeks framed by a
black moustache stripe, large white oval SCAPULAR patches, black wings barred with white spots, buff-white
underparts, RED undertail. Zygodactyl feet (two toes forward, two back) and a stiff tail propped on the bark.
Same frame as micro_birds.woodpecker(): faces +Y toward the trunk, belly on +Y, neck pivot at (0, 0.8, 5.0).
xray_skull(): same frame and markers as micro_birds._xray_head(), with a real skull and the hyoid horns.
"""
import math

import bmesh
import bpy
from mathutils import Vector

import look
from micro_anatomy import _blob, _empty, _tubes


def _mask(nt, co, center, radii, soft=0.35):
    """1 inside an ellipsoid (center, radii) in the given coordinates, fading to 0 over `soft`."""
    sub = nt.nodes.new("ShaderNodeVectorMath")
    sub.operation = "SUBTRACT"
    sub.inputs[1].default_value = center
    nt.links.new(co, sub.inputs[0])
    div = nt.nodes.new("ShaderNodeVectorMath")
    div.operation = "DIVIDE"
    div.inputs[1].default_value = radii
    nt.links.new(sub.outputs[0], div.inputs[0])
    ln = nt.nodes.new("ShaderNodeVectorMath")
    ln.operation = "LENGTH"
    nt.links.new(div.outputs[0], ln.inputs[0])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.interpolation_type = "SMOOTHSTEP"
    mr.inputs["From Min"].default_value = 1.0
    mr.inputs["From Max"].default_value = 1.0 - soft
    nt.links.new(ln.outputs["Value"], mr.inputs["Value"])
    return mr.outputs["Result"]


def _plumage(name, regions, base=(0.012, 0.012, 0.014), barb=9.0, cells=1.6):
    """Feathered surface: barb ridges, overlapping feather tips, sheen, colour regions in object space."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.82
    b.inputs["Specular IOR Level"].default_value = 0.25
    b.inputs["Sheen Weight"].default_value = 0.45
    b.inputs["Sheen Roughness"].default_value = 0.5
    b.inputs["Coat Weight"].default_value = 0.0
    co = nt.nodes.new("ShaderNodeTexCoord").outputs["Object"]
    prev = None
    for center, radii, rgb in regions:
        mk = _mask(nt, co, center, radii)
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        if prev is None:
            mix.inputs["A"].default_value = (*base, 1)
        else:
            nt.links.new(prev, mix.inputs["A"])
        mix.inputs["B"].default_value = (*rgb, 1)
        nt.links.new(mk, mix.inputs["Factor"])
        prev = mix.outputs["Result"]
    if prev is not None:
        nt.links.new(prev, b.inputs["Base Color"])
    else:
        b.inputs["Base Color"].default_value = (*base, 1)
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (barb, barb, barb * 0.25)
    nt.links.new(co, mp.inputs["Vector"])
    wv = nt.nodes.new("ShaderNodeTexWave")
    wv.inputs["Scale"].default_value = 3.0
    wv.inputs["Distortion"].default_value = 5.0
    wv.inputs["Detail"].default_value = 3.0
    nt.links.new(mp.outputs["Vector"], wv.inputs["Vector"])
    v = nt.nodes.new("ShaderNodeTexVoronoi")
    v.feature = "DISTANCE_TO_EDGE"
    v.inputs["Scale"].default_value = cells
    nt.links.new(co, v.inputs["Vector"])
    add = nt.nodes.new("ShaderNodeMath")
    add.operation = "MULTIPLY_ADD"
    add.inputs[1].default_value = 0.5
    nt.links.new(wv.outputs["Fac"], add.inputs[0])
    nt.links.new(v.outputs["Distance"], add.inputs[2])
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.75
    nt.links.new(add.outputs[0], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    m["look_v2"] = 1
    return m


def _math(nt, op, a, b=None, val=None):
    n = nt.nodes.new("ShaderNodeMath")
    n.operation = op
    nt.links.new(a, n.inputs[0])
    if b is not None:
        nt.links.new(b, n.inputs[1])
    elif val is not None:
        n.inputs[1].default_value = val
    return n.outputs[0]


def _flight_mat(name, spots=True):
    """A flight or tail feather card: black, pale shaft, white spot bars on the outer vane (Dendrocopos wing)."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.5
    b.inputs["Sheen Weight"].default_value = 0.6
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["UV"], sep.inputs[0])             # u across the vane (0..1), v along the feather
    ab = _math(nt, "ABSOLUTE", _math(nt, "SUBTRACT", sep.outputs["X"], val=0.5))
    shaft = nt.nodes.new("ShaderNodeMapRange")
    shaft.interpolation_type = "SMOOTHSTEP"
    shaft.inputs["From Min"].default_value = 0.035
    shaft.inputs["From Max"].default_value = 0.0
    nt.links.new(ab, shaft.inputs["Value"])
    mx1 = nt.nodes.new("ShaderNodeMix")
    mx1.data_type = "RGBA"
    mx1.inputs["A"].default_value = (0.012, 0.012, 0.014, 1)
    mx1.inputs["B"].default_value = (0.85, 0.84, 0.8, 1)
    if spots:
        bars = _math(nt, "GREATER_THAN", _math(nt, "SINE", _math(nt, "MULTIPLY", sep.outputs["Y"], val=2 * math.pi * 4.5)),
                     val=0.82)
        outer = _math(nt, "GREATER_THAN", sep.outputs["X"], val=0.72)
        notip = _math(nt, "LESS_THAN", sep.outputs["Y"], val=0.82)
        nt.links.new(_math(nt, "MULTIPLY", _math(nt, "MULTIPLY", bars, outer), notip), mx1.inputs["Factor"])
    else:
        mx1.inputs["Factor"].default_value = 0.0
    mx2 = nt.nodes.new("ShaderNodeMix")
    mx2.data_type = "RGBA"
    nt.links.new(mx1.outputs["Result"], mx2.inputs["A"])
    mx2.inputs["B"].default_value = (0.25, 0.24, 0.23, 1)
    nt.links.new(shaft.outputs["Result"], mx2.inputs["Factor"])
    nt.links.new(mx2.outputs["Result"], b.inputs["Base Color"])
    wv2 = nt.nodes.new("ShaderNodeTexWave")                   # barbs off the shaft
    wv2.inputs["Scale"].default_value = 40.0
    wv2.inputs["Distortion"].default_value = 1.5
    nt.links.new(tc.outputs["UV"], wv2.inputs["Vector"])
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.2
    nt.links.new(wv2.outputs["Fac"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    m.use_backface_culling = False
    m["look_v2"] = 1
    return m


def _feather(name, base, tip, width, mat, parent, normal=(1, 0, 0), curl=0.15, pointed=False):
    """A feather card from base to tip: tapered vane, slight curve, UV u across / v along."""
    base, tip = Vector(base), Vector(tip)
    ax = tip - base
    L = ax.length
    d = ax.normalized()
    side = d.cross(Vector(normal)).normalized()
    nrm = side.cross(d).normalized()
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new()
    rows, cols = 14, 4
    grid = []
    for i in range(rows + 1):
        v = i / rows
        w = width * (math.sin(math.pi * min(1.0, 0.18 + v * 0.9)) ** 0.5)
        if pointed:
            w *= (1 - v) ** 0.6 + 0.08
        row = []
        for j in range(cols + 1):
            u = j / cols
            p = base + d * (L * v) + side * (w * (u - 0.5)) + nrm * (curl * L * v ** 2 + 0.04 * L * (u - 0.5) ** 2)
            row.append((bm.verts.new(p), u, v))
        grid.append(row)
    for i in range(rows):
        for j in range(cols):
            q = (grid[i][j], grid[i][j + 1], grid[i + 1][j + 1], grid[i + 1][j])
            f = bm.faces.new([c[0] for c in q])
            for lp, c in zip(f.loops, q):
                lp[uvl].uv = (c[1], c[2])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(mat)
    o.parent = parent
    o.modifiers.new("T", "SOLIDIFY").thickness = 0.03
    return o


def _meta(name, parts, m, parent=None):
    mb = bpy.data.metaballs.new(name)
    mb.resolution = 0.35
    mb.render_resolution = 0.14
    mb.threshold = 0.6
    for co, r, sz in parts:
        e = mb.elements.new()
        e.type = "ELLIPSOID"
        e.co = co
        e.radius = r
        e.size_x, e.size_y, e.size_z = sz
        e.stiffness = 2.0
    o = bpy.data.objects.new(name, mb)
    bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(m)
    if parent:
        o.parent = parent
    return o


WHITE, BUFF, RED, BLACK = (0.9, 0.89, 0.84), (0.72, 0.64, 0.52), (0.62, 0.02, 0.03), (0.012, 0.012, 0.014)


def woodpecker2(name):
    root = _empty(name)
    body_m = _plumage("Wp2Body", [
        ((0, 3.3, 0.5), (2.3, 2.0, 4.2), BUFF),            # breast and belly (the belly faces the trunk, +Y)
        ((0, 3.0, 2.8), (1.9, 1.8, 2.0), WHITE),           # whiter upper breast
        ((0, 1.6, -4.6), (1.5, 1.8, 1.4), RED),            # red undertail
        ((1.55, -1.7, 2.0), (0.75, 1.0, 1.7), WHITE),      # white scapular ovals on the back
        ((-1.55, -1.7, 2.0), (0.75, 1.0, 1.7), WHITE),
    ])
    base = "Wp2" + name
    _meta(base, [((0, 0.4, 0.5), 3.0, (0.85, 1.0, 2.3)),
                 ((0, 1.0, 3.6), 2.2, (0.9, 0.9, 1.1)),
                 ((0, 1.2, -3.5), 2.2, (0.95, 1.0, 1.4)),
                 ((0, 0.9, 5.4), 1.5, (1.0, 1.0, 1.1))], body_m, root)
    # ---- folded wings: coverts, then 6 secondaries + 9 primaries per side, white spot bars
    fm = _flight_mat("Wp2Flight", True)
    cov = _plumage("Wp2Cov", [((2.0, -0.4, 2.5), (1.0, 1.3, 1.5), WHITE), ((-2.0, -0.4, 2.5), (1.0, 1.3, 1.5), WHITE)],
                   barb=12.0)
    for sx in (-1, 1):
        _meta(base + "cv", [((sx * 2.0, 0.2, 2.2), 1.5, (0.45, 1.0, 1.6))], cov, root)
        for k in range(15):
            prim = k >= 6
            t = k / 14
            b0 = Vector((sx * (2.15 - 0.25 * t + 0.012 * k), 0.6 - 1.5 * t, 3.2 - 0.6 * t))
            tp = Vector((sx * (1.55 - 0.9 * t + 0.012 * k), -0.5 - 1.3 * t, -3.0 - (3.2 if prim else 1.6) * (0.4 + 0.6 * t)))
            _feather(name + f"fw{sx}{k}", b0, tp, 0.95 if prim else 1.15, fm, root, normal=(sx, -0.3, 0), curl=0.05)
    # ---- stiff tail: 10 pointed feathers propped on the bark
    tm = _flight_mat("Wp2Tail", False)
    tmo = _flight_mat("Wp2TailOuter", True)
    for k in range(10):
        u = (k - 4.5) / 4.5
        _feather(name + f"tl{k}", (u * 0.6, 1.2, -4.2), (u * 2.0, 2.6 + 0.3 * (1 - abs(u)), -11.0 + 1.2 * abs(u)),
                 1.0, tmo if abs(u) > 0.75 else tm, root, normal=(0, -1, 0.15), curl=-0.04, pointed=True)
    # ---- zygodactyl feet: short grey tarsus, two toes up, two toes down, curved claws
    km = look.keratin("Wp2Foot", (0.22, 0.22, 0.24), 20.0)
    for sx in (-1, 1):
        ank = Vector((sx * 1.3, 2.4, -3.6))
        strands = [[(tuple(Vector((sx * 1.2, 1.6, -3.0))), 0.22), (tuple(ank), 0.2)]]
        for dz, dx in ((1.0, 0.25), (0.75, -0.2), (-1.0, 0.3), (-0.8, -0.15)):
            t1 = ank + Vector((sx * dx, 1.0, dz))
            t2 = t1 + Vector((sx * dx * 0.3, 0.55, dz * 0.25))
            cl = t2 + Vector((0, 0.15, dz * 0.35))
            strands.append([(tuple(ank), 0.14), (tuple(t1), 0.12), (tuple(t2), 0.1)])
            strands.append([(tuple(t2), 0.08), (tuple(cl), 0.02)])
        _tubes(name + f"ft{sx}", strands, km, root)
    # ---- the head: its own mesh on the neck pivot, marks painted in head space
    neck = _empty(name + "neck", (0, 0.8, 5.0), root)
    # head marks in the head mesh's OWN space: a unit sphere (+Y toward the beak, +Z up); the eye sits at ~(0.87, 0.46, 0.16)
    head_m = _plumage("Wp2Head", [
        ((0, 0.86, 0.42), (0.34, 0.24, 0.24), BUFF),                 # buff forehead above the beak
        ((0.86, 0.02, -0.12), (0.34, 0.36, 0.2), WHITE),             # white cheek / ear coverts, behind and below the eye
        ((-0.86, 0.02, -0.12), (0.34, 0.36, 0.2), WHITE),
        ((0, 0.55, -0.72), (0.5, 0.42, 0.3), WHITE),                 # white throat (black moustache stripe left between)
        ((0, -0.78, 0.32), (0.5, 0.34, 0.4), RED),                   # red nape patch (adult male)
    ], barb=40.0, cells=9.0)
    hd = _blob(name + "head", (0, 1.5, 2.45), (1.75, 2.3, 1.75), head_m, neck, seg=48)
    _meta(base, [((0, 0.4, 0.8), 1.6, (1.0, 1.0, 1.2))], body_m, neck)        # neck, fuses into the body
    eye_m, b = look._principled("Wp2Eye")
    if b is not None:
        b.inputs["Base Color"].default_value = (0.09, 0.015, 0.012, 1)    # dark red-brown iris
        b.inputs["Roughness"].default_value = 0.1
        b.inputs["Coat Weight"].default_value = 1.0
        b.inputs["Coat Roughness"].default_value = 0.02
    for sx in (-1, 1):
        _blob(name + "eye", (sx * 1.5, 2.55, 2.75), (0.3, 0.3, 0.3), eye_m, neck, seg=24)
    # chisel beak: straight, flattened side to side toward the tip
    bkm = look.keratin("Wp2Beak", (0.07, 0.07, 0.08), 35.0)
    bm = bmesh.new()
    rings, segs = 16, 20
    vs = []
    for i in range(rings + 1):
        t = i / rings
        r = 0.72 * (1 - t) ** 0.9 + 0.03
        ring = [bm.verts.new((r * math.cos(2 * math.pi * j / segs) * (1 - 0.35 * t), 3.35 + 3.9 * t,
                              2.25 - 0.1 * t + r * 1.05 * math.sin(2 * math.pi * j / segs))) for j in range(segs)]
        if vs:
            for j in range(segs):
                bm.faces.new((vs[-1][j], vs[-1][(j + 1) % segs], ring[(j + 1) % segs], ring[j]))
        vs.append(ring)
    bm.faces.new(vs[-1])
    me = bpy.data.meshes.new(name + "beak")
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    bk = bpy.data.objects.new(name + "beak", me)
    bpy.context.scene.collection.objects.link(bk)
    bk.data.materials.append(bkm)
    bk.parent = neck
    hairs = []                            # nasal bristles over the nostrils (they keep wood dust out)
    for sx in (-1, 1):
        for k in range(14):
            p0 = Vector((sx * (0.35 + 0.02 * k), 3.35, 2.55 + 0.03 * (k % 5)))
            hairs.append([(tuple(p0), 0.03), (tuple(p0 + Vector((sx * 0.05, 0.55, 0.12))), 0.008)])
    _tubes(name + "brs", hairs, bkm, neck, res=2)
    return root, neck


def xray_skull(name, col_skull, col_brain, at, xray, organic, glow, blob):
    """X-ray woodpecker skull: braincase, orbits, upper beak bone, lower jaw, the small brain, and the HYOID horns
    that start under the jaw, run back around the skull and over the top toward the nostril
    (Bock 1999, Wilson Bulletin 111:494; Jung et al. 2016, Acta Biomaterialia 35:319). Markers as before."""
    root = _empty(name, at)
    skm = xray(name + "sk", col_skull, 1.2, 0.18)
    _blob(name + "case", (0, -0.6, 0.35), (2.3, 2.45, 2.25), skm, root, seg=48)
    for sx in (-1, 1):
        _blob(name + "orb", (sx * 1.35, 1.15, 0.45), (0.95, 0.95, 0.95), xray(name + "ob", col_skull, 2.0, 0.08), root)
    _tubes(name + "up", [[((0, 1.4, 0.25), 0.85), ((0, 3.3, -0.05), 0.5), ((0, 5.6, -0.2), 0.04)]],
           xray(name + "bk", col_skull, 1.5, 0.35), root, res=8)
    _tubes(name + "lo", [[((0, -0.2, -1.1), 0.35), ((0, 2.4, -0.75), 0.32), ((0, 5.4, -0.35), 0.04)]],
           xray(name + "lj", col_skull, 1.5, 0.35), root, res=8)
    hy = []
    for sx in (-1, 1):
        pts = [(sx * 0.2, 1.5, -1.25), (sx * 0.6, -0.6, -1.7), (sx * 0.9, -2.6, -1.0), (sx * 0.85, -3.25, 0.6),
               (sx * 0.55, -2.4, 2.35), (sx * 0.25, -0.5, 2.85), (sx * 0.1, 1.2, 2.3), (0.05 * sx, 2.4, 0.9)]
        hy.append([(p, 0.09) for p in pts])
    _tubes(name + "hyoid", hy, glow(name + "hy", (1.0, 0.75, 0.3), 1.6), root, res=6, smooth=True)
    brain = blob(name + "brain", 1.0, (0, -0.85, 0.6), (1.35, 1.55, 1.3),
                 organic(name + "br", col_brain, col_brain, 2.0, sss=0.8, noise=6), 0.06, 4, parent=root)
    for nm, p, col in (("b", (0, 5.6, -0.2), (1.0, 0.85, 0.1)), ("h", (0, -2.9, 0.4), (0.2, 0.9, 1.0))):
        blob(name + "mk" + nm, 0.32, p, (1, 1, 1), glow(name + "mk" + nm, col, 14), 0, parent=root)
    return root, brain
