"""ATP book shots for micro.py (26 Nov 2026): "The Tiny Turbine That Powers Your Body".

Sources: Watt et al. 2010 PNAS 107:16823 (vertebrate c8 ring, ~100 rev/s, 3 ATP per turn); Noji et al. 1997 Nature
386:299 (rotation seen with a filament on the gamma shaft; rotor ~1 nm radius in a ~5 nm alpha3-beta3 barrel);
Boyer 1997 Annu Rev Biochem 66:717 (binding change: open, loose, tight); Zuhra & Szabo 2022 FEBS J (cyanide blocks
Complex IV). Units ~nm. The F1 head points UP into the matrix; the intermembrane space (where protons are pumped) is
DOWN, so protons flow UP through the turbine. Rotation is shown slowed (the label says so).

Kinds: atp_muscle, atp_molecule, atp_mito, atp_chain (`cyanide`: CN jams Complex IV and everything stops),
atp_dam, atp_synthase (`mode`: "spin" | "protons" | "beta" | "orbit"; `slow` = turns per second on screen),
atp_noji (the 1997 experiment: F1 on glass, a long glowing filament turning on its shaft).
"""
import math
import random

from mathutils import Vector

KINDS = ("atp_muscle", "atp_molecule", "atp_mito", "atp_chain", "atp_dam", "atp_synthase", "atp_noji")
G = {}

PROTON = (1.0, 0.42, 0.12)
ELECTRON = (1.0, 0.92, 0.25)


def install(g):
    global G
    G = g                                                       # the SAME dict as micro.py's globals (not a copy)
    mine = set(globals())
    globals().update({k: v for k, v in g.items() if not k.startswith("__") and k not in mine})


def proton_mat():
    return bpy.data.materials.get("Proton") or glow("Proton", PROTON, 7.0)


def soup(n=140, spread=60, zr=(-30, 30)):
    cols = [(0.2, 0.9, 1.0), (1.0, 0.6, 0.2), (0.9, 0.3, 0.6), (0.5, 1.0, 0.4)]
    for i in range(n):
        loc = Vector((random.uniform(-spread, spread), random.uniform(-spread, spread), random.uniform(*zr)))
        o = blob(f"dust{i}", random.uniform(0.06, 0.25), loc, (1, 1, 1),
                 glow(f"dm{i}", random.choice(cols), random.uniform(2, 7)), lump=0, subdiv=2)
        d = Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-0.4, 0.4)))
        key_loc(o, [(1, loc), (N, loc + d * N / FPS * 0.5)])
        linear(o)


def lights(scale=1.0):
    area_light((10, -24, 30), (0, 0, 4), 1.2e4 * scale, (1.0, 0.82, 0.62), 18)
    area_light((-26, -8, 8), (0, 0, 4), 4e3 * scale, (0.35, 0.7, 1.0), 16)
    area_light((0, 20, -10), (0, 0, 0), 3e3 * scale, (0.3, 1.0, 0.8), 16)


# ---------------------------------------------------------------- ATP molecule
def atp_molecule(name, loc, s=1.0, glow_k=1.0):
    """Ball and stick: adenine (two fused rings), ribose (a five-ring), three phosphates in a row (P with oxygens)."""
    root = empty(name, loc)
    root.scale = (s, s, s)
    Cm = bpy.data.materials.get("AtC") or glow("AtC", (0.75, 0.85, 1.0), 2.0 * glow_k)
    Nm = bpy.data.materials.get("AtN") or glow("AtN", (0.35, 0.55, 1.0), 3.0 * glow_k)
    Om = bpy.data.materials.get("AtO") or glow("AtO", (1.0, 0.22, 0.15), 3.0 * glow_k)
    Pm = bpy.data.materials.get("AtP") or glow("AtP", (1.0, 0.65, 0.1), 5.0 * glow_k)
    pts = []
    for k in range(6):                                          # adenine six-ring
        a = k * math.pi / 3
        pts.append(((-3.2 + 0.7 * math.cos(a), 0.7 * math.sin(a), 0), Nm if k % 2 else Cm))
    for k, a in enumerate((0.9, 0.0, -0.9)):                     # fused five-ring
        pts.append(((-2.0 + 0.55 * math.cos(a), 0.55 * math.sin(a) + 0.0, 0), Nm if k == 1 else Cm))
    for k in range(5):                                          # ribose
        a = k * 2 * math.pi / 5
        pts.append(((-0.6 + 0.55 * math.cos(a), -0.2 + 0.55 * math.sin(a), 0), Om if k == 0 else Cm))
    for j in range(3):                                          # three phosphates
        x = 0.8 + j * 1.3
        pts.append(((x, 0.0, 0), Pm))
        for d in ((0, 0.62, 0), (0, -0.62, 0), (0, 0, 0.62)):
            pts.append(((x + d[0], d[1], d[2]), Om))
    for k, (p, m) in enumerate(pts):
        blob(f"{name}a{k}", 0.34 if m is Pm else 0.27, p, (1, 1, 1), m, lump=0, subdiv=2, parent=root)
    return root


# ---------------------------------------------------------------- ATP synthase
def synthase(name="AS", at=(0, 0, 0), membrane=True):
    """Returns (root, rotor, betas, csubs). Rotor = c-ring + crooked gamma shaft (turns about Z)."""
    root = empty(name, at)
    rotor = empty(name + "rot", at)
    cmat = organic(name + "c", (0.10, 0.55, 0.85), (0.2, 0.7, 1.0), 2.0, sss=0.8, noise=4)
    gmat = organic(name + "g", (0.95, 0.75, 0.15), (1.0, 0.75, 0.1), 3.0, sss=0.8, noise=4)
    amat = organic(name + "a", (0.75, 0.15, 0.35), (0.9, 0.25, 0.4), 1.6, sss=0.8, noise=3)
    bmat = organic(name + "b", (0.95, 0.45, 0.1), (1.0, 0.45, 0.1), 2.2, sss=0.8, noise=3)
    stator = organic(name + "s", (0.6, 0.6, 0.65), (0.6, 0.7, 0.9), 0.8, sss=0.6, noise=3)
    csubs = []
    for k in range(8):                                          # the c8 ring, spanning the membrane
        a = k * 2 * math.pi / 8
        c = blob(f"{name}c{k}", 1.0, (2.4 * math.cos(a), 2.4 * math.sin(a), 0),
                 (0.75, 0.75, 2.6), cmat, 0.12, 3, parent=rotor)
        csubs.append(c)
    cu = bpy.data.curves.new(name + "gam", "CURVE")             # the crooked gamma shaft
    cu.dimensions = "3D"
    cu.bevel_depth = 0.9
    cu.bevel_resolution = 6
    sp = cu.splines.new("NURBS")
    pts = [(0, 0, 1.5), (0.2, 0, 4.0), (0.9, 0.2, 7.0), (0.5, -0.3, 10.0), (-0.2, 0, 13.0)]
    sp.points.add(len(pts) - 1)
    for p_, v in zip(sp.points, pts):
        p_.co = (v[0], v[1], v[2], 1)
    sp.use_endpoint_u = True
    gam = bpy.data.objects.new(name + "gamma", cu)
    SC.collection.objects.link(gam)
    gam.data.materials.append(gmat)
    gam.parent = rotor
    blob(name + "eps", 1.0, (0.6, 0.4, 3.2), (1.6, 1.3, 1.0), gmat, 0.1, 3, parent=rotor)
    betas = []
    for k in range(6):                                          # alpha3 beta3 head, alternating
        a = k * math.pi / 3 + math.pi / 6
        isb = k % 2 == 0
        pv = empty(f"{name}hd{k}", (3.0 * math.cos(a), 3.0 * math.sin(a), 11.0))
        pv["a"] = a
        pv["w"] = tuple(Vector(at) + pv.location)          # its world position (root is never rotated)
        pv.parent = root
        blob(f"{name}{'b' if isb else 'al'}{k}", 1.0, (0, 0, 0), (2.1, 2.1, 3.3),
             bmat if isb else stator, 0.25, 2.5, parent=pv)
        if isb:
            betas.append(pv)
    blob(name + "delta", 1.0, (0, 0, 16.0), (2.4, 2.4, 1.2), stator, 0.15, 3, parent=root)
    blob(name + "asub", 1.0, (4.6, 0, 0), (1.4, 2.0, 2.6), amat, 0.15, 3, parent=root)
    cu2 = bpy.data.curves.new(name + "bst", "CURVE")            # the peripheral stalk holding the head still
    cu2.dimensions = "3D"
    cu2.bevel_depth = 0.45
    sp2 = cu2.splines.new("NURBS")
    p2 = [(5.0, 0, 1.0), (6.2, 0, 6), (6.0, 0, 11), (4.0, 0, 15.5), (1.5, 0, 16.4)]
    sp2.points.add(len(p2) - 1)
    for p_, v in zip(sp2.points, p2):
        p_.co = (v[0], v[1], v[2], 1)
    sp2.use_endpoint_u = True
    bs = bpy.data.objects.new(name + "bstalk", cu2)
    SC.collection.objects.link(bs)
    bs.data.materials.append(amat)
    bs.parent = root
    return root, rotor, betas, csubs


def spin(rotor, tps, f0=1, f1=None, slow_to_stop=None):
    """Turn the rotor at tps turns per (screen) second; slow_to_stop=(fa, fb) eases it to a halt."""
    f1 = f1 or N
    ang = 0.0
    for fr in range(f0, f1 + 1, 2):
        k = 1.0
        if slow_to_stop and fr > slow_to_stop[0]:
            k = max(0.0, 1 - (fr - slow_to_stop[0]) / max(1, slow_to_stop[1] - slow_to_stop[0]))
        rotor.rotation_euler = (0, 0, ang)
        rotor.keyframe_insert("rotation_euler", frame=fr)
        ang += 2 * math.pi * tps * k * 2 / FPS
    linear(rotor)
    return ang


def protons_through(at, tps, f0, f1, n_per_turn=8, mat=None):
    """Protons arrive from below at the a-subunit, ride the ring almost a full turn, and leave upward."""
    mat = mat or proton_mat()
    at = Vector(at)
    period = FPS / max(tps, 1e-3)
    step = period / n_per_turn
    i = 0
    t = f0
    while t < f1:
        start_ang = 2 * math.pi * tps * (t - 1) / FPS
        o = blob(f"hp{len(bpy.data.objects)}", 0.32, at + Vector((5.5, 0, -6)), (1, 1, 1), mat, 0, subdiv=2)
        keys = [(1, at + Vector((5.5 + random.uniform(-1, 1), random.uniform(-2, 2), -9))),
                (int(t) - 10, at + Vector((5.0, 0.0, -4.5))), (int(t), at + Vector((3.2, 0.0, -0.8)))]
        for j in range(1, 15):                                  # riding the ring, 7/8 of a turn
            fr = int(t + period * 0.875 * j / 14)
            ang = 2 * math.pi * 0.875 * j / 14
            keys.append((fr, at + Vector((3.2 * math.cos(ang), 3.2 * math.sin(ang), -0.8 + 1.6 * j / 14))))
        fe = int(t + period * 0.875)
        keys.append((fe + 8, at + Vector((4.2, 0.0, 3.5))))
        keys.append((fe + 30, at + Vector((5 + random.uniform(-2, 2), random.uniform(-3, 3), 9))))
        key_loc(o, keys)
        linear(o)
        t += step
        i += 1


def beta_cycle(betas, tps, f0=1, f1=None, loads=True, at=(0, 0, 0)):
    """Binding change: each beta goes open -> loose -> tight a third of a turn apart; ADP + P go in, ATP comes out."""
    f1 = f1 or N
    third = FPS / max(tps, 1e-3) / 3
    states = {"open": (1.12, 1.12, 0.95), "loose": (1.0, 1.0, 1.0), "tight": (0.86, 0.86, 1.05)}
    order = ["open", "loose", "tight"]
    for bi, pv in enumerate(betas):
        k = bi
        fr = f0
        while fr <= f1 + third:
            st = order[k % 3]
            pv.scale = states[st]
            pv.keyframe_insert("scale", frame=int(fr))
            if loads and st == "open" and fr + third < f1:
                a = pv["a"]
                out = Vector((math.cos(a), math.sin(a), 0))
                c = Vector(pv["w"])
                m = atp_molecule(f"atpo{len(bpy.data.objects)}", c, 0.32, 1.6)   # new ATP leaves
                m.scale = (0.001, 0.001, 0.001)
                m.keyframe_insert("scale", frame=1)
                m.keyframe_insert("scale", frame=max(1, int(fr) - 1))
                m.scale = (0.32, 0.32, 0.32)
                m.keyframe_insert("scale", frame=int(fr))
                key_loc(m, [(int(fr), c), (int(fr + third * 2), c + out * 9 + Vector((0, 0, 3)))])
                adp = blob(f"adp{len(bpy.data.objects)}", 0.5, c + out * 9, (1, 1, 1),
                           bpy.data.materials.get("AdpM") or glow("AdpM", (0.6, 0.8, 1.0), 4.0), 0, subdiv=2)
                key_loc(adp, [(1, c + out * 10 + Vector((0, 0, -3))), (int(fr + third * 0.2), c + out * 7),
                              (int(fr + third * 0.9), c + out * 1.2)])
                adp.scale = (1, 1, 1)
                adp.keyframe_insert("scale", frame=int(fr + third * 0.9))
                adp.scale = (0.001, 0.001, 0.001)
                adp.keyframe_insert("scale", frame=int(fr + third * 2))
            k += 1
            fr += third
        smooth(pv)


# ---------------------------------------------------------------- shots
def _membrane(holes):
    G["CHANNELS"] = holes                                       # micro.lipids reads this for its holes
    lipids(extent=60, hole=4.6)


def shot_synthase(cam, tgt):
    world((0.004, 0.008, 0.02))
    _membrane([(0, 0)])
    root, rotor, betas, csubs = synthase()
    mode = SHOT.get("mode", "spin")
    tps = float(SHOT.get("slow", 0.4))
    spin(rotor, tps)
    if mode in ("protons", "spin", "orbit"):
        protons_through((0, 0, 0), tps, 1, N)
        for i in range(60):                                     # the crowd waiting below (intermembrane space)
            p = Vector((random.uniform(-14, 14), random.uniform(-10, 4), random.uniform(-14, -4)))
            o = blob(f"crowd{i}", 0.32, p, (1, 1, 1), proton_mat(), 0, subdiv=2)
            wander(o, p, 0.6, 8)
            linear(o)
    if mode in ("beta", "orbit"):
        beta_cycle(betas, tps, 1, N)
    soup()
    lights()
    bloom(0.8, 0.6)
    if mode == "beta":
        key_loc(cam, [(1, (14, -26, 18)), (N, (10, -22, 15))])
        key_loc(tgt, [(1, (0, 0, 10.5))])
    elif mode == "protons":
        key_loc(cam, [(1, (18, -26, -2)), (N, (13, -21, 0))])
        key_loc(tgt, [(1, (2, 0, -1))])
    elif mode == "orbit":
        pts = [(F(t / 8), (44 * math.cos(-2.0 + 1.4 * t / 8), 44 * math.sin(-2.0 + 1.4 * t / 8), 12 + 4 * t / 8))
               for t in range(9)]
        key_loc(cam, pts)
        key_loc(tgt, [(1, (0, 0, 8.5))])                        # far enough that the top cap never leaves frame
    else:
        key_loc(cam, [(1, (24, -40, 14)), (N, (20, -35, 12))])
        key_loc(tgt, [(1, (0, 0, 8.5))])
    smooth(cam)
    cam.data.dof.aperture_fstop = 2.8


def shot_noji(cam, tgt):
    """1997: the F1 part fixed upside-down on glass; a long fluorescent filament on the gamma shaft turns round."""
    world((0.002, 0.004, 0.01))
    glass = bpy.data.materials.new("Slide")
    glass.use_nodes = True
    gb = glass.node_tree.nodes["Principled BSDF"]
    gb.inputs["Base Color"].default_value = (0.05, 0.08, 0.12, 1)
    gb.inputs["Roughness"].default_value = 0.15
    bpy.ops.mesh.primitive_plane_add(size=400, location=(0, 0, 0))
    bpy.context.object.data.materials.append(glass)
    head = empty("NojiHead", (0, 0, 0))
    stator = organic("NojiS", (0.6, 0.6, 0.65), (0.6, 0.7, 0.9), 0.8, sss=0.6, noise=3)
    bmat = organic("NojiB", (0.95, 0.45, 0.1), (1.0, 0.45, 0.1), 2.2, sss=0.8, noise=3)
    for k in range(6):
        a = k * math.pi / 3
        blob(f"nh{k}", 1.0, (3.0 * math.cos(a), 3.0 * math.sin(a), 3.4), (2.1, 2.1, 3.3), bmat if k % 2 == 0 else stator, 0.25, 2.5)
    rotor = empty("NojiRot", (0, 0, 0))
    gmat = organic("NojiG", (0.95, 0.75, 0.15), (1.0, 0.75, 0.1), 3.0, sss=0.8, noise=4)
    blob("ngam", 1.0, (0, 0, 7.5), (0.9, 0.9, 3.5), gmat, 0.1, 3, parent=rotor)
    fil = glow("Filament", (0.4, 1.0, 0.5), 8.0)                # the fluorescent actin filament (~1 um: drawn shorter)
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.55, depth=60, location=(30, 0, 11))
    f = bpy.context.object
    f.rotation_euler = (0, math.pi / 2, 0)
    f.data.materials.append(fil)
    f.parent = rotor
    spin(rotor, float(SHOT.get("slow", 0.5)))
    lights(0.7)
    bloom(0.9, 0.5)
    key_loc(cam, [(1, (0, -48, 52)), (N, (0, -42, 46))])
    key_loc(tgt, [(1, (10, 0, 6))])
    smooth(cam)
    cam.data.lens = SHOT.get("lens", 30)
    cam.data.dof.aperture_fstop = 11


def _complex(name, at, parts, m):
    root = empty(name, at)
    for k, (off, sz) in enumerate(parts):
        blob(f"{name}{k}", 1.0, tuple(1.5 * v for v in off), tuple(1.5 * v for v in sz), m, 0.2, 2.5, parent=root)
    return root


def shot_chain(cam, tgt):
    """The electron transport chain on the cut membrane: I, III and IV pump protons DOWN (into the space between the
    membranes); electrons (yellow) hop I -> III -> IV; at IV they meet oxygen and make water. `cyanide` jams IV."""
    world((0.004, 0.008, 0.02))
    X = {"I": -16, "III": 0, "IV": 14, "AS": 30}
    _membrane([(X["I"], 0), (X["III"], 0), (X["IV"], 0), (X["AS"], 0)])
    m1 = organic("CxI", (0.35, 0.75, 0.30), (0.4, 1.0, 0.4), 1.8, sss=0.8, noise=3)
    m3 = organic("CxIII", (0.30, 0.45, 0.95), (0.4, 0.6, 1.0), 1.8, sss=0.8, noise=3)
    m4 = organic("CxIV", (0.80, 0.30, 0.80), (1.0, 0.4, 1.0), 1.8, sss=0.8, noise=3)
    _complex("I", (X["I"], 0, 0), [((0, 0, 0), (4.0, 2.4, 2.6)), ((-1.5, 0, 5.5), (1.6, 1.8, 4.0))], m1)   # the L
    _complex("III", (X["III"], 0, 0), [((-1.6, 0, 0), (2.2, 2.2, 2.8)), ((1.6, 0, 0), (2.2, 2.2, 2.8))], m3)
    iv = _complex("IV", (X["IV"], 0, 0), [((0, 0, 0), (2.6, 2.4, 2.8))], m4)
    root, rotor, betas, csubs = synthase("AS", (X["AS"], 0, 0))
    cyan = bool(SHOT.get("cyanide"))
    f_block = F(0.3) if cyan else N + 999
    tps = 0.4
    spin(rotor, tps, 1, N, slow_to_stop=(f_block + 20, F(0.92)) if cyan else None)
    if not cyan or f_block > 30:
        protons_through((X["AS"], 0, 0), tps, 1, f_block if cyan else N)
    e = glow("Electron", ELECTRON, 14.0)
    route = [(X["I"] - 1.5, 0, 8), (X["I"], 0, 1), (X["I"] + 7, 0, 0), (X["III"] - 1, 0, 0), (X["III"] + 4, -1, -4.5),
             (X["IV"] - 1, 0, -2.5), (X["IV"], 0, 1.5)]
    k = 0
    for f0 in range(1, N, 9):                                   # a stream of electrons along the chain
        o = blob(f"el{k}", 0.35, route[0], (1, 1, 1), e, 0, subdiv=2)
        stop = len(route)
        if f0 > f_block - 40:
            stop = 4                                            # jammed: they pile up before IV
        keys = [(1, Vector(route[0]) + Vector((0, 0, 4))), (f0, route[0])]
        for j in range(1, stop):
            keys.append((f0 + j * 10, Vector(route[j]) + (Vector((random.uniform(-1, 1), 0, random.uniform(-1, 1))) if stop == 4 and j == 3 else Vector())))
        key_loc(o, keys)
        linear(o)
        k += 1
    pm = proton_mat()
    for cx in (X["I"], X["III"], X["IV"]):                      # pumping: protons cross DOWN at three complexes
        for f0 in range(1, N, 14):
            if f0 > f_block:
                break
            o = blob(f"pp{len(bpy.data.objects)}", 0.32, (cx, 0, 7), (1, 1, 1), pm, 0, subdiv=2)
            end = Vector((cx + random.uniform(-6, 6), random.uniform(-6, 4), random.uniform(-14, -7)))
            key_loc(o, [(1, (cx + random.uniform(-3, 3), random.uniform(-3, 3), 9)), (f0, (cx, 0, 4)),
                        (f0 + 12, (cx, 0, -3)), (f0 + 40, end)])
            linear(o)
    ox = glow("Oxygen", (1.0, 0.25, 0.2), 4.0)
    wat = glow("WaterM", (0.6, 0.85, 1.0), 4.0)
    for f0 in range(20, min(N, f_block), 40):                   # O2 + electrons + protons -> water at IV
        o = blob(f"o2{f0}", 0.55, (X["IV"] + 6, 0, 9), (1.8, 1, 1), ox, 0, subdiv=2)
        key_loc(o, [(1, (X["IV"] + 9, 2, 12)), (f0, (X["IV"] + 1, 0, 4.2))])
        o.scale = (1.8, 1, 1)
        o.keyframe_insert("scale", frame=f0)
        o.scale = (0.01, 0.01, 0.01)
        o.keyframe_insert("scale", frame=f0 + 4)
        w = blob(f"h2o{f0}", 0.5, (X["IV"] + 1, 0, 4.2), (1, 1, 1), wat, 0, subdiv=2)
        w.scale = (0.01, 0.01, 0.01)
        w.keyframe_insert("scale", frame=1)
        w.keyframe_insert("scale", frame=f0 + 3)
        w.scale = (1, 1, 1)
        w.keyframe_insert("scale", frame=f0 + 6)
        key_loc(w, [(f0 + 6, (X["IV"] + 1, 0, 4.2)), (f0 + 50, (X["IV"] + random.uniform(-4, 4), -3, 12))])
    for i in range(70 if not cyan else 90):                     # the crowd below; with cyanide it drains away
        p = Vector((random.uniform(-26, 36), random.uniform(-10, 4), random.uniform(-14, -5)))
        o = blob(f"crowd{i}", 0.32, p, (1, 1, 1), pm, 0, subdiv=2)
        if cyan and i % 3:
            o.scale = (1, 1, 1)
            o.keyframe_insert("scale", frame=f_block + int(i * 2))
            o.scale = (0.01, 0.01, 0.01)
            o.keyframe_insert("scale", frame=f_block + int(i * 2) + 25)
    if cyan:                                                    # the cyanide molecule docks into IV
        cn = empty("CN", (0, 0, 0))
        blob("cnC", 0.5, (X["IV"] + 10, -6, 12), (1, 1, 1), glow("CNc", (0.7, 0.7, 0.75), 3.0), 0, parent=cn)
        blob("cnN", 0.5, (X["IV"] + 10.9, -6, 12), (1, 1, 1), glow("CNn", (0.3, 0.5, 1.0), 4.0), 0, parent=cn)
        key_loc(cn, [(1, (0, 0, 0)), (f_block, (-9.5, 6, -10.5))])
        smooth(cn)
    soup(120, 70)
    lights()
    bloom(0.8, 0.6)
    focus = SHOT.get("focus", "all")
    if focus == "pumps":
        key_loc(cam, [(1, (-6, -40, 6)), (N, (-2, -34, 4))])
        key_loc(tgt, [(1, (-6, 0, 0))])
    elif focus == "iv":
        key_loc(cam, [(1, (14, -30, 8)), (N, (14, -24, 6))])
        key_loc(tgt, [(1, (14, 0, 2))])
    else:
        key_loc(cam, [(1, (6, -84, 18)), (N, (8, -74, 14))])
        key_loc(tgt, [(1, (7, 0, 4))])
    smooth(cam)
    cam.data.dof.aperture_fstop = 4.0


def shot_dam(cam, tgt):
    """Protons crowded below like water behind a dam; the turbine is the one way back."""
    world((0.004, 0.008, 0.02))
    _membrane([(0, 0)])
    root, rotor, betas, csubs = synthase()
    tps = 0.3
    spin(rotor, tps)
    protons_through((0, 0, 0), tps, F(0.4), N)
    pm = proton_mat()
    for i in range(260):
        p = Vector((random.uniform(-40, 40), random.uniform(-12, 10), random.uniform(-18, -3.2)))
        o = blob(f"crowd{i}", 0.34, p, (1, 1, 1), pm, 0, subdiv=2)
        wander(o, p, 0.5, 10)
        linear(o)
    for i in range(20):
        p = Vector((random.uniform(-40, 40), random.uniform(-12, 10), random.uniform(4, 20)))
        blob(f"few{i}", 0.34, p, (1, 1, 1), pm, 0, subdiv=2)
    soup(100, 70)
    lights()
    bloom(0.8, 0.6)
    key_loc(cam, [(1, (0, -80, 4)), (N, (4, -60, 3))])
    key_loc(tgt, [(1, (0, 0, -2))])
    smooth(cam)
    cam.data.dof.aperture_fstop = 5.6


def shot_mito(cam, tgt):
    """A mitochondrion cut open: smooth outer membrane, inner membrane folded into cristae, turbines dotted on them."""
    world((0.006, 0.006, 0.016))
    outer = bpy.data.materials.new("Outer")
    outer.use_nodes = True
    ob = outer.node_tree.nodes["Principled BSDF"]
    ob.inputs["Base Color"].default_value = (0.95, 0.45, 0.4, 1)
    ob.inputs["Alpha"].default_value = 0.35
    ob.inputs["Emission Color"].default_value = (1.0, 0.4, 0.35, 1)
    ob.inputs["Emission Strength"].default_value = 0.15
    try:
        outer.surface_render_method = "BLENDED"
    except Exception:
        pass
    inner = organic("Inner", (0.9, 0.55, 0.3), (1.0, 0.55, 0.25), 1.0, sss=0.8, noise=2)
    root = empty("Mito")
    bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, radius=1.0)
    o = bpy.context.object
    o.scale = (40, 16, 16)
    o.data.materials.append(outer)
    o.parent = root
    cut = None
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -20, 0))
    cut = bpy.context.object
    cut.scale = (120, 40, 60)
    cut.hide_render = True
    cut.hide_viewport = True
    for k in range(-6, 7):                                      # cristae: folded plates across the inside
        x = k * 5.6
        w = 15 * math.sqrt(max(0.05, 1 - (x / 40) ** 2))
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, 0, (-1) ** k * 2.5))
        c = bpy.context.object
        c.scale = (0.9, w * 1.7, w * 1.5)
        c.modifiers.new("B", "BEVEL").width = 0.4
        c.data.materials.append(inner)
        b = c.modifiers.new("C", "BOOLEAN")
        b.object = cut
        b.operation = "DIFFERENCE"
        c.parent = root
        for j in range(10):                                     # turbines dotted on the crista edge
            z = random.uniform(-w * 0.6, w * 0.6)
            blob(f"lolly{k}_{j}", 0.35, (x + 0.6, random.uniform(0, w * 0.7), z), (1, 1, 1),
                 glow("Lolly", (1.0, 0.8, 0.3), 3.0), 0, subdiv=2, parent=root)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, radius=1.0)
    im = bpy.context.object
    im.scale = (38.5, 14.5, 14.5)
    sol = im.modifiers.new("S", "SOLIDIFY")
    sol.thickness = 0.04
    b2 = im.modifiers.new("C", "BOOLEAN")
    b2.object = cut
    b2.operation = "DIFFERENCE"
    im.data.materials.append(inner)
    im.parent = root
    root.rotation_euler = (0, 0, math.radians(8))
    soup(160, 90, (-40, 40))
    lights(1.1)
    bloom(0.7, 0.7)
    if SHOT.get("dive"):
        key_loc(cam, [(1, (10, -120, 40)), (N, (6, -26, 6))])
        key_loc(tgt, [(1, (0, 0, 0)), (N, (4, 4, 2))])
    else:
        key_loc(cam, [(1, (20, -110, 36)), (N, (10, -90, 24))])
        key_loc(tgt, [(1, (0, 0, 0))])
    smooth(cam)
    smooth(tgt)
    cam.data.dof.aperture_fstop = 5.6


def shot_muscle(cam, tgt):
    """Muscle fibres (striated tubes) pulling in rhythm, glowing ATP sparks being spent along them."""
    world((0.01, 0.004, 0.006))
    m = bpy.data.materials.new("Myo")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    if "Subsurface Weight" in b.inputs:
        b.inputs["Subsurface Weight"].default_value = 0.6
    b.inputs["Roughness"].default_value = 0.45
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.inputs["Scale"].default_value = 3.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.35, 0.03, 0.05, 1)
    ramp.color_ramp.elements[1].color = (0.85, 0.25, 0.25, 1)
    nt.links.new(wave.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    fibres = []
    for i in range(26):
        y, z = random.uniform(-14, 14), random.uniform(-9, 9)
        bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=random.uniform(1.4, 2.2), depth=140,
                                            location=(0, y, z))
        f = bpy.context.object
        f.rotation_euler = (0, math.pi / 2, 0)
        f.data.materials.append(m)
        for p in f.data.polygons:
            p.use_smooth = True
        fibres.append(f)
    for fr in range(1, N + 1, 6):                               # contract and relax
        s = 1.0 - 0.06 * (0.5 + 0.5 * math.sin(fr / FPS * 2 * math.pi * 0.8))
        for f in fibres:
            f.scale = (1 + (1 - s) * 0.8, 1 + (1 - s) * 0.8, s)
            f.keyframe_insert("scale", frame=fr)
    spark = glow("Spark", (1.0, 0.85, 0.3), 10.0)
    for i in range(160):                                        # ATP being spent: sparks flare and fade
        p = Vector((random.uniform(-40, 40), random.uniform(-15, 15), random.uniform(-10, 10)))
        o = blob(f"sp{i}", 0.8, p, (1, 1, 1), spark, 0, subdiv=2)
        f0 = random.randint(1, max(2, N - 10))
        o.scale = (0.01, 0.01, 0.01)
        o.keyframe_insert("scale", frame=1)
        o.keyframe_insert("scale", frame=f0)
        o.scale = (1.4, 1.4, 1.4)
        o.keyframe_insert("scale", frame=f0 + 3)
        o.scale = (0.01, 0.01, 0.01)
        o.keyframe_insert("scale", frame=f0 + 14)
    lights(2.0)
    bloom(0.8, 0.6)
    key_loc(cam, [(1, (-40, -62, 14)), (N, (20, -54, 10))])
    key_loc(tgt, [(1, (-20, 0, 0)), (N, (30, 0, 0))])
    linear(cam)
    linear(tgt)
    cam.data.dof.aperture_fstop = 2.8


def shot_molecule(cam, tgt):
    world((0.003, 0.006, 0.016))
    m = atp_molecule("ATP", (-1.0, 0, 0), 1.6, 1.0)
    m.rotation_euler = (0.3, 0, 0)
    m.keyframe_insert("rotation_euler", frame=1)
    m.rotation_euler = (0.3, 0, 1.2)
    m.keyframe_insert("rotation_euler", frame=N)
    linear(m)
    if SHOT.get("split"):                                        # the last phosphate breaks off: energy released
        tip = sorted((o for o in m.children if o.name.startswith("ATPa")), key=lambda o: int(o.name[4:].split(".")[0]))[-4:]
        last = empty("Pi", (0, 0, 0))
        for o in tip:
            o.parent = last
        last.parent = m
        key_loc(last, [(1, (0, 0, 0)), (F(0.45), (0, 0, 0)), (F(0.8), (3.0, 1.0, 0.5))])
        flash = glow("Flash", (1.0, 0.9, 0.5), 0.0)
        blob("fl", 0.7, (3.6, 0, 0), (1, 1, 1), flash, 0, subdiv=3, parent=m)
        key_input(emis_input(flash), [(1, 0), (F(0.45), 0), (F(0.5), 9), (F(0.75), 0)])
    soup(100, 30, (-15, 15))
    lights(0.6)
    bloom(0.9, 0.5)
    key_loc(cam, [(1, (2, -22, 6)), (N, (1, -17, 4))])
    key_loc(tgt, [(1, (0, 0, 0))])
    smooth(cam)
    cam.data.dof.aperture_fstop = 4.0


def build(cam, tgt):
    {"atp_muscle": shot_muscle, "atp_molecule": shot_molecule, "atp_mito": shot_mito, "atp_chain": shot_chain,
     "atp_dam": shot_dam, "atp_synthase": shot_synthase, "atp_noji": shot_noji}[KIND](cam, tgt)
