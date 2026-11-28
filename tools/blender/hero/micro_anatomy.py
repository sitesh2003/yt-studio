"""Anatomy-first animals (28 Nov 2026, step 4 of the council's 3D order).

mosquito2(): a female Aedes aegypti built from its real body plan, same interface as micro_bugs.mosquito()
(returns (root, [wing pivots]), faces +Y, wing pivots carry "side" and fold the wings back at rest).
Morphology after Christophers (1960) "Aedes aegypti (L.), the Yellow Fever Mosquito", Cambridge UP, and the
Walter Reed Biosystematics Unit identification key for Ae. aegypti:
  - scutum with a LYRE of silver-white scales (two curved outer lines + two thin median lines);
  - proboscis dark, about as long as the fore femur; female palps short (about 1/5 of the proboscis), white tips;
  - female antenna: 13 flagellomeres with sparse whorls of short hairs (the male's are bushy);
  - abdominal tergites dark with basal white bands and lateral white spots;
  - legs: white knee spots, basal white bands on the tarsomeres; hind tarsomere 5 all white;
  - narrow wings (female wing ~2.5-3.0 mm), dark-scaled veins, scaled fringe on the hind margin; halteres.
Built in millimetres (head-to-abdomen-tip ~5 units), then scaled so the body is `size` scene units long.
"""
import math

import bpy
from mathutils import Vector

import look

BODY_MM = 5.0


def _empty(name, loc=(0, 0, 0), parent=None):
    e = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(e)
    e.location = loc
    if parent:
        e.parent = parent
    return e


def _tubes(name, strands, mat, parent, res=6, smooth=False):
    """One curve object; strands = [[(point, radius), ...], ...], each a straight-segment tube."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = 1.0
    cu.bevel_resolution = max(1, res // 2)
    cu.use_fill_caps = True
    for pts in strands:
        sp = cu.splines.new("NURBS" if smooth else "POLY")
        sp.points.add(len(pts) - 1)
        for p, (co, r) in zip(sp.points, pts):
            p.co = (*co, 1.0)
            p.radius = r
        if smooth:
            sp.order_u = min(4, len(pts))
            sp.use_endpoint_u = True
            sp.resolution_u = 12
    o = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(mat)
    o.parent = parent
    return o


def _blob(name, loc, scale, mat, parent, seg=32, rot=(0, 0, 0)):
    me = bpy.data.meshes.new(name)
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg // 2, radius=1.0)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    o.location, o.scale, o.rotation_euler = loc, scale, rot
    o.data.materials.append(mat)
    o.parent = parent
    return o


def _on_surface(obj, x, y, top=True):
    """Project (x, y) onto the top (or bottom) of a blob in its parent's space."""
    inv = obj.matrix_basis.inverted()
    z0 = 50.0 if top else -50.0
    o = inv @ Vector((x, y, z0))
    d = (inv.to_3x3() @ Vector((0, 0, -1 if top else 1))).normalized()
    # analytic: the blob is a unit sphere in its own space
    b = 2 * o.dot(d)
    c = o.dot(o) - 1.0
    disc = b * b - 4 * c
    if disc < 0:
        return None
    t = (-b - math.sqrt(disc)) / 2
    return obj.matrix_basis @ (o + d * t)


def _mosq_mats():
    dark = look.chitin("Mq2Dark", (0.018, 0.016, 0.017), scale_size=22.0)
    white = look.chitin("Mq2White", (0.82, 0.83, 0.86), scale_size=22.0, film=180.0)
    white.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.3
    eye, b = look._principled("Mq2Eye")
    if b is not None:
        nt = eye.node_tree
        b.inputs["Base Color"].default_value = (0.025, 0.02, 0.022, 1)
        b.inputs["Roughness"].default_value = 0.22
        b.inputs["Coat Weight"].default_value = 1.0
        b.inputs["Coat Roughness"].default_value = 0.05
        b.inputs["Thin Film Thickness"].default_value = 320.0          # the faint green-purple sheen of the cornea
        v = nt.nodes.new("ShaderNodeTexVoronoi")                      # ommatidia: ~20 micrometres -> ~45 per mm
        v.inputs["Scale"].default_value = 45.0
        tc = nt.nodes.new("ShaderNodeTexCoord")
        nt.links.new(tc.outputs["Object"], v.inputs["Vector"])
        bp = nt.nodes.new("ShaderNodeBump")
        bp.inputs["Strength"].default_value = 0.6
        bp.inputs["Distance"].default_value = 0.01
        nt.links.new(v.outputs["Distance"], bp.inputs["Height"])
        nt.links.new(bp.outputs["Normal"], b.inputs["Coat Normal"])
        nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
        eye["look_v2"] = 1
    wing = look.insect_wing("Mq2Wing", veins=False)
    return dark, white, eye, wing


# leg joints in body mm for the RIGHT side (x > 0), standing on a surface 1.45 mm below the thorax centre;
# hind legs raised and curled up behind, as Aedes rests.
_LEGS = {
    "fore": [(0.20, 0.38, -0.42), (0.95, 1.45, 0.20), (1.30, 2.35, -1.45)],
    "mid":  [(0.28, 0.02, -0.46), (1.65, 0.15, 0.28), (2.40, 0.20, -1.45)],
    "hind": [(0.24, -0.30, -0.42), (1.25, -1.55, 0.40), (1.65, -2.55, -0.85)],
}
_TARSI = {   # tarsomere end points (5 each)
    "fore": [(1.45, 3.05, -1.45), (1.55, 3.40, -1.45), (1.62, 3.62, -1.45), (1.67, 3.78, -1.45), (1.70, 3.90, -1.45)],
    "mid":  [(3.25, 0.22, -1.45), (3.65, 0.20, -1.45), (3.90, 0.18, -1.45), (4.05, 0.16, -1.45), (4.16, 0.15, -1.45)],
    "hind": [(1.72, -3.35, -0.45), (1.75, -3.75, 0.05), (1.73, -3.98, 0.40), (1.70, -4.12, 0.65), (1.66, -4.22, 0.85)],
}


def _lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


AB_Y0, AB_SEG, AB_N = -0.62, 0.36, 8


def _abdomen(name, root, dark, white):
    import bmesh
    m = bpy.data.materials.get("Mq2Abd")
    if m is None:
        m = look.chitin("Mq2Abd", (0.018, 0.016, 0.017), scale_size=22.0)
        nt = m.node_tree
        b = nt.nodes["Principled BSDF"]
        tc = nt.nodes.new("ShaderNodeTexCoord")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(tc.outputs["Object"], sep.inputs[0])
        ph = nt.nodes.new("ShaderNodeMath")                      # (y0 - y) / seg -> segment phase
        ph.operation = "MULTIPLY_ADD"
        ph.inputs[1].default_value = -1.0 / AB_SEG
        ph.inputs[2].default_value = AB_Y0 / AB_SEG
        nt.links.new(sep.outputs["Y"], ph.inputs[0])
        fr = nt.nodes.new("ShaderNodeMath")
        fr.operation = "FRACT"
        nt.links.new(ph.outputs[0], fr.inputs[0])
        band = nt.nodes.new("ShaderNodeMath")                    # the front 22% of each segment is white
        band.operation = "LESS_THAN"
        band.inputs[1].default_value = 0.22
        nt.links.new(fr.outputs[0], band.inputs[0])
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.inputs["A"].default_value = (0.018, 0.016, 0.017, 1)
        mix.inputs["B"].default_value = (0.8, 0.81, 0.84, 1)
        nt.links.new(band.outputs[0], mix.inputs["Factor"])
        nt.links.new(mix.outputs["Result"], b.inputs["Base Color"])
    bm = bmesh.new()
    rings, seg_v = 120, 40
    L = AB_SEG * AB_N
    prev = None
    first = last = None
    for i in range(rings + 1):
        t = i / rings
        y = AB_Y0 - L * t
        ph = (t * AB_N) % 1.0
        pinch = 1.0 - 0.07 * math.exp(-((ph - 0.0) / 0.06) ** 2) - 0.07 * math.exp(-((ph - 1.0) / 0.06) ** 2)
        prof = math.sin(math.pi * min(1.0, 0.12 + t * 0.95)) ** 0.55          # rounded at the waist, tapered tip
        rx = 0.4 * prof * pinch * (1 - 0.25 * t)
        rz = 0.31 * prof * pinch * (1 - 0.3 * t)
        zc = -0.12 - 0.22 * t + 0.25 * t ** 3                                 # hangs a little, tip lifts
        ring = [bm.verts.new((rx * math.cos(2 * math.pi * j / seg_v), y, zc + rz * math.sin(2 * math.pi * j / seg_v)))
                for j in range(seg_v)]
        if prev:
            for j in range(seg_v):
                bm.faces.new((prev[j], prev[(j + 1) % seg_v], ring[(j + 1) % seg_v], ring[j]))
        else:
            first = ring
        prev = ring
    last = prev
    bm.faces.new(list(reversed(first)))
    bm.faces.new(last)
    me = bpy.data.meshes.new(name + "abd")
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    o = bpy.data.objects.new(name + "abd", me)
    bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(m)
    o.parent = root
    for k in range(AB_N):                                                    # lateral white spots
        t = (k + 0.3) / AB_N
        y = AB_Y0 - L * t
        prof = math.sin(math.pi * min(1.0, 0.12 + t * 0.95)) ** 0.55
        rx = 0.4 * prof * (1 - 0.25 * t)
        zc = -0.12 - 0.22 * t + 0.25 * t ** 3
        for sx in (-1, 1):
            _blob(name + f"ls{k}", (sx * rx * 0.96, y, zc - 0.05), (0.035, 0.08, 0.06), white, root, seg=12)
    return o


def mosquito2(name, size=1.2):
    dark, white, eye, wing = _mosq_mats()
    root = _empty(name)
    s = size / BODY_MM
    root.scale = (s, s, s)
    root["stand_off"] = 1.45 * s          # the feet are this far below the root: land at surface + stand_off
    dk, wh = [], []                       # strands by material

    # ---- thorax: scutum hump + scutellum, the lyre on top
    th = _blob(name + "th", (0, 0.0, 0.05), (0.52, 0.78, 0.62), dark, root)
    _blob(name + "scl", (0, -0.62, 0.32), (0.34, 0.16, 0.14), dark, root)          # scutellum
    _blob(name + "pl", (0, 0.1, -0.25), (0.48, 0.6, 0.38), dark, root)             # pleura / sternum
    for sx in (-1, 1):                    # lateral white pleural patches
        _blob(name + "pw", (sx * 0.43, 0.1, -0.12), (0.07, 0.22, 0.1), white, root)
    lyre = []
    for sx in (-1, 1):                    # the two curved outer lines: bow outward, meet near the front
        pts = []
        for k in range(12):
            t = k / 11
            x = sx * (0.08 + 0.22 * math.sin(math.pi * (0.15 + 0.7 * t)))
            y = 0.55 - 1.0 * t
            p = _on_surface(th, x, y)
            if p is not None:
                pts.append((tuple(p + Vector((0, 0, 0.012))), 0.022))
        lyre.append(pts)
        med = []                          # the thin median lines
        for k in range(8):
            y = 0.35 - 0.8 * k / 7
            p = _on_surface(th, sx * 0.035, y)
            if p is not None:
                med.append((tuple(p + Vector((0, 0, 0.01))), 0.011))
        lyre.append(med)
    _tubes(name + "lyre", lyre, white, root, res=4)

    # ---- head, compound eyes, antennae, palps, proboscis
    hd = (0, 0.88, -0.05)
    _blob(name + "hd", hd, (0.3, 0.27, 0.3), dark, root)
    for sx in (-1, 1):                    # big eyes that almost meet on top
        _blob(name + "ey", (sx * 0.17, 0.93, -0.02), (0.2, 0.22, 0.27), eye, root, seg=48)
    _blob(name + "clp", (0, 1.12, -0.1), (0.1, 0.08, 0.09), white, root)            # clypeus
    hairs = []
    for sx in (-1, 1):
        base = Vector((sx * 0.06, 1.13, 0.02))
        _blob(name + "ped", tuple(base), (0.075, 0.075, 0.075), dark, root)         # pedicel (Johnston's organ)
        tip = base + Vector((sx * 0.75, 1.2, 0.85))
        ant = [(tuple(base.lerp(tip, k / 13)), 0.018 - 0.008 * k / 13) for k in range(14)]
        dk.append(ant)
        side = Vector((sx, 0, 0))
        axis = (tip - base).normalized()
        u = axis.cross(Vector((0, 0, 1))).normalized()
        v = axis.cross(u).normalized()
        for k in range(1, 13):            # a whorl of short hairs at each flagellomere joint
            c = base.lerp(tip, k / 13)
            for j in range(7):
                a = 2 * math.pi * j / 7
                d = (u * math.cos(a) + v * math.sin(a)) * 0.13 + axis * 0.05
                hairs.append([(tuple(c), 0.004), (tuple(c + d), 0.0015)])
        pb = Vector((sx * 0.04, 1.14, -0.13))                                           # female palp: short
        pm = pb + Vector((sx * 0.03, 0.3, -0.12))
        pt = pm + Vector((sx * 0.01, 0.12, -0.05))
        dk.append([(tuple(pb), 0.035), (tuple(pm), 0.032)])
        wh.append([(tuple(pm), 0.032), (tuple(pt), 0.028)])
    _tubes(name + "hair", hairs, dark, root, res=2)
    pr = [(0, 1.15, -0.16), (0, 1.75, -0.4), (0, 2.45, -0.72), (0, 2.95, -0.98), (0, 3.08, -1.05)]
    dk.append([(p, r) for p, r in zip(pr, (0.03, 0.024, 0.021, 0.019, 0.026))])        # labium, labella at the tip

    # ---- abdomen: one smooth lofted body (8 segments with slight constrictions); the basal white band of each
    #      tergite is painted by position, so it always sits on its segment
    _abdomen(name, root, dark, white)

    # ---- legs: coxa-femur-tibia as tubes, knee spot, banded tarsi, claws
    for sx in (-1, 1):
        for leg, (b, kn, an) in _LEGS.items():
            m = lambda p: (sx * p[0], p[1], p[2])
            b, kn, an = m(b), m(kn), m(an)
            dk.append([(b, 0.0562), (_lerp(b, kn, 0.85), 0.0465)])                          # coxa + femur
            wh.append([(_lerp(b, kn, 0.85), 0.0465), (kn, 0.0413)])                         # white knee spot
            dk.append([(kn, 0.039), (an, 0.03)])                                           # tibia
            prev = an
            for i, tp in enumerate(_TARSI[leg]):
                tp = m(tp)
                r0 = 0.027 - 0.004 * i
                if leg == "hind" and i == 4:
                    wh.append([(prev, r0), (tp, r0 * 0.85)])                              # hind tarsomere 5: all white
                elif i < 3:
                    mid = _lerp(prev, tp, 0.35)
                    wh.append([(prev, r0), (mid, r0 * 0.95)])                             # basal white band
                    dk.append([(mid, r0 * 0.95), (tp, r0 * 0.85)])
                else:
                    dk.append([(prev, r0), (tp, r0 * 0.85)])
                prev = tp
            for cx in (-0.05, 0.05):                                                       # paired claws
                c1 = Vector(prev) + Vector((cx, 0.05, -0.03))
                dk.append([(prev, 0.012), (tuple(c1), 0.004)])
    _tubes(name + "dk", dk, dark, root)
    _tubes(name + "wh", wh, white, root)

    # ---- halteres: stalk + knob behind each wing base
    for sx in (-1, 1):
        hb = Vector((sx * 0.38, -0.45, 0.18))
        hk = hb + Vector((sx * 0.12, -0.3, 0.05))
        _tubes(name + "hlt", [[(tuple(hb), 0.02), (tuple(hk), 0.018)]], white, root, res=2)
        _blob(name + "hkn", tuple(hk), (0.06, 0.07, 0.05), white, root, seg=12)

    # ---- wings on pivots, folded back over the abdomen at rest (one over the other)
    pivots = []
    L, W = 2.9, 0.62
    for side in (-1, 1):
        pv = _empty(name + f"wp{side}", (side * 0.33, 0.05, 0.42), root)
        pv["side"] = side
        outline = []
        n = 28
        for k in range(n + 1):            # costa (leading, outer) edge from base to tip
            t = k / n
            outline.append((side * (0.06 + W * 0.55 * math.sin(math.pi * min(1, t * 1.05)) ** 0.6), -L * t))
        for k in range(n, -1, -1):        # hind margin back to the base
            t = k / n
            outline.append((-side * (0.02 + W * 0.45 * math.sin(math.pi * t) ** 0.9), -L * t))
        me = bpy.data.meshes.new(name + "wg")
        me.from_pydata([(x, y, side * 0.004) for x, y in outline], [], [list(range(len(outline)))])
        wg = bpy.data.objects.new(name + "wg", me)
        bpy.context.scene.collection.objects.link(wg)
        wg.data.materials.append(wing)
        wg.parent = pv
        mod = wg.modifiers.new("tri", "TRIANGULATE")
        # veins: costa, subcosta, R1, R2/R3 fork, R4+5, M1+2/M3+4 fork, CuA1/CuA2, 1A (Culicidae plan)
        cw = lambda t: side * (0.06 + W * 0.55 * math.sin(math.pi * min(1, t * 1.05)) ** 0.6)
        hw = lambda t: -side * (0.02 + W * 0.45 * math.sin(math.pi * t) ** 0.9)
        def at(t, f):                    # a point at length fraction t, f=0 hind margin .. 1 costa
            return (hw(t) + (cw(t) - hw(t)) * f, -L * t, side * 0.01)
        veins = [
            [at(0.0, 0.95), at(0.5, 0.99), at(1.0, 0.6)],                     # costa
            [at(0.02, 0.85), at(0.45, 0.93)],                                 # subcosta
            [at(0.02, 0.75), at(0.6, 0.86), at(0.97, 0.78)],                  # R1
            [at(0.05, 0.62), at(0.62, 0.68)], [at(0.62, 0.68), at(0.99, 0.62)], [at(0.62, 0.68), at(0.97, 0.45)],  # R2, R3
            [at(0.05, 0.55), at(0.55, 0.52), at(0.95, 0.33)],                 # R4+5
            [at(0.05, 0.45), at(0.66, 0.38)], [at(0.66, 0.38), at(0.92, 0.22)], [at(0.66, 0.38), at(0.85, 0.08)],  # M
            [at(0.04, 0.33), at(0.5, 0.2)], [at(0.5, 0.2), at(0.68, 0.03)], [at(0.5, 0.2), at(0.38, 0.02)],      # CuA
            [at(0.03, 0.18), at(0.62, 0.05)],                                 # anal vein
        ]
        _tubes(name + "vn", [[(p, 0.0075) for p in v] for v in veins], dark, wg, res=2)
        fringe = []
        for k in range(4, 40):           # scaled fringe on the hind margin
            t = k / 40
            p = Vector((hw(t), -L * t, side * 0.008))
            fringe.append([(tuple(p), 0.006), (tuple(p + Vector((-side * 0.11, -0.03, 0))), 0.003)])
        _tubes(name + "fr", fringe, dark, wg, res=2)
        pivots.append(pv)
    return root, pivots
