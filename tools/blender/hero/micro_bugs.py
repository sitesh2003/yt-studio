"""Mosquito shots for micro.py (25 Nov 2026), De Obaldia et al. 2022 Cell 185:4099.

Imported by micro.py for the kinds below; install(globals()) hands over micro.py's helpers (blob, glow, organic,
camera keys, F, N, SC ...). Units are centimetres. The mosquito is a procedural female Aedes aegypti (black body,
white bands on the abdomen and legs, a white lyre on the thorax), drawn about twice life size so it reads on a phone.

Kinds: mosq_magnet (two forearms, the swarm picks one), mosq_sleeve (a nylon sleeve on a forearm, hours pass),
mosq_choice (the two-choice test: two sleeves, mosquitoes fly up one scent plume; `skew` = share choosing B),
mosq_skin (skin close-up: oil droplets, carboxylic acid molecules rising), mosq_follow (a mosquito tracks a scent
plume to the arm), mosq_land (a mosquito lands on the skin).
"""
import math
import random

from mathutils import Vector

KINDS = ("mosq_magnet", "mosq_sleeve", "mosq_choice", "mosq_skin", "mosq_follow", "mosq_land")


def install(g):
    mine = set(globals())                  # never replace this module's own functions (build, ...)
    globals().update({k: v for k, v in g.items() if not k.startswith("__") and k not in mine})


# ---------------------------------------------------------------- the mosquito
def _mats():
    if "MqBody" in bpy.data.materials:
        return tuple(bpy.data.materials[n] for n in ("MqBody", "MqWhite", "MqEye", "MqWing"))
    body = bpy.data.materials.new("MqBody")
    body.use_nodes = True
    b = body.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.012, 0.012, 0.014, 1)
    b.inputs["Roughness"].default_value = 0.35
    if "Coat Weight" in b.inputs:
        b.inputs["Coat Weight"].default_value = 0.5
    white = glow("MqWhite", (0.92, 0.92, 0.95), 0.25)
    white.name = "MqWhite"
    eye = bpy.data.materials.new("MqEye")
    eye.use_nodes = True
    e = eye.node_tree.nodes["Principled BSDF"]
    e.inputs["Base Color"].default_value = (0.05, 0.03, 0.06, 1)
    e.inputs["Roughness"].default_value = 0.15
    wing = bpy.data.materials.new("MqWing")
    wing.use_nodes = True
    w = wing.node_tree.nodes["Principled BSDF"]
    w.inputs["Base Color"].default_value = (0.8, 0.85, 0.95, 1)
    w.inputs["Roughness"].default_value = 0.1
    w.inputs["Alpha"].default_value = 0.22
    if "Thin Film Thickness" in w.inputs:
        w.inputs["Thin Film Thickness"].default_value = 500
    try:
        wing.surface_render_method = "BLENDED"
    except Exception:
        pass
    return body, white, eye, wing


def _stick(name, a, b, r, m, parent):
    a, b = Vector(a), Vector(b)
    d = b - a
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=r, depth=d.length, location=(a + b) / 2)
    o = bpy.context.object
    o.name = name
    o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    o.data.materials.append(m)
    o.parent = parent
    return o


def mosquito(name, size=1.2):
    """A female Aedes aegypti facing +Y, about `size` cm long. Returns (root, [wing pivots])."""
    body, white, eye, wing = _mats()
    root = empty(name)
    s = size / 0.62                       # the build below is ~0.62 units long
    root.scale = (s, s, s)
    # thorax with the white lyre
    blob(name + "th", 0.1, (0, 0, 0), (0.85, 1.1, 0.95), body, 0.0, parent=root, subdiv=3)
    for sx in (-1, 1):
        _stick(name + "ly", (sx * 0.035, -0.06, 0.088), (sx * 0.05, 0.07, 0.08), 0.008, white, root)
    # head, eyes, proboscis, palps, antennae
    blob(name + "hd", 0.055, (0, 0.13, -0.01), (1, 1, 0.95), body, 0.0, parent=root, subdiv=3)
    for sx in (-1, 1):
        blob(name + "ey", 0.035, (sx * 0.035, 0.145, 0.0), (1, 1, 1), eye, 0.0, parent=root, subdiv=2)
        _stick(name + "an", (sx * 0.015, 0.17, 0.02), (sx * 0.06, 0.32, 0.09), 0.004, body, root)
        _stick(name + "pa", (sx * 0.01, 0.17, -0.03), (sx * 0.012, 0.22, -0.06), 0.006, white, root)
    _stick(name + "pr", (0, 0.17, -0.035), (0, 0.42, -0.13), 0.006, body, root)
    # abdomen: eight segments, white band on each
    for k in range(8):
        y = -0.12 - k * 0.055
        r = 0.065 * (1 - k * 0.07)
        blob(name + f"ab{k}", r, (0, y, -0.02 - k * 0.006), (0.9, 0.62, 0.8), body, 0.0, parent=root, subdiv=2)
        blob(name + f"bd{k}", r * 0.92, (0, y + 0.024, -0.02 - k * 0.006), (0.92, 0.12, 0.82), white, 0.0,
             parent=root, subdiv=2)
    # six long legs, white tarsal bands
    for side in (-1, 1):
        for j, (fy, spread) in enumerate(((0.05, 0.6), (0.0, 0.0), (-0.05, -0.7))):
            a = Vector((side * 0.06, fy, -0.06))
            knee = a + Vector((side * 0.22, spread * 0.18 + fy, 0.16))
            foot = knee + Vector((side * 0.16, spread * 0.25 + (0.15 if j == 0 else -0.1 if j == 2 else 0), -0.36))
            _stick(name + "lf", a, knee, 0.006, body, root)
            mid = knee.lerp(foot, 0.6)
            _stick(name + "ls", knee, mid, 0.005, body, root)
            _stick(name + "lt", mid, foot, 0.005, white, root)
    # wings on pivots, folded back over the abdomen at rest, beating in flight
    pivots = []
    for side in (-1, 1):
        pv = empty(name + f"wp{side}", (side * 0.05, 0.02, 0.07))
        pv.parent = root
        bpy.ops.mesh.primitive_circle_add(vertices=24, radius=0.5, fill_type="NGON", location=(0, 0, 0))
        wg = bpy.context.object
        wg.name = name + "wg"
        wg.scale = (0.11, 0.42, 1)
        wg.location = (side * 0.035, -0.2, 0)
        wg.data.materials.append(wing)
        wg.parent = pv
        pv["side"] = side
        pivots.append(pv)
    return root, pivots


def fly(root, pivots, path, every=2, beat=True):
    """path: [(frame, location)]; the mosquito faces where it is going and its wings blur-beat."""
    pts = sorted(path)
    for (f0, p0), (f1, p1) in zip(pts, pts[1:]):
        d = Vector(p1) - Vector(p0)
        if d.length > 1e-4:
            q = d.normalized().to_track_quat("Y", "Z").to_euler()
            for fr in (f0, f1 - 1):
                root.rotation_euler = q
                root.keyframe_insert("rotation_euler", frame=max(1, fr))
    for fr, p in pts:
        root.location = p
        root.keyframe_insert("location", frame=fr)
    linear(root)
    if beat:
        for pv in pivots:
            sd = pv["side"]
            for fr in range(1, N + 1):
                up = fr % 2 == 0
                pv.rotation_euler = (0, sd * (0.9 if up else -0.4), sd * (1.25 if up else 0.9))
                pv.keyframe_insert("rotation_euler", frame=fr)
            ad = pv.animation_data
            for fc in _fcurves(ad.action):
                for kp in fc.keyframe_points:
                    kp.interpolation = "CONSTANT"


def wander_path(start, end, f0, f1, wobble=1.5, every=3):
    pts = []
    for fr in range(f0, f1 + 1, every):
        t = (fr - f0) / max(1, f1 - f0)
        e = t * t * (3 - 2 * t)
        p = Vector(start).lerp(Vector(end), e)
        w = wobble * (1 - e) ** 0.7
        pts.append((fr, p + Vector((random.uniform(-w, w), random.uniform(-w, w), random.uniform(-w, w) * 0.6))))
    pts[-1] = (pts[-1][0], Vector(end))
    return pts


# ---------------------------------------------------------------- arms, sleeves, scent
def skin_mat():
    if "Skin" in bpy.data.materials:
        return bpy.data.materials["Skin"]
    m = organic("Skin", (0.55, 0.33, 0.24), (0.6, 0.25, 0.15), 0.05, sss=0.5, noise=40, rough=0.62)
    b = m.node_tree.nodes["Principled BSDF"]
    if "Coat Weight" in b.inputs:
        b.inputs["Coat Weight"].default_value = 0.0     # skin is not lacquered: no mirror highlight
    return m


def forearm(name, x, length=30, r=4.0, z=3.4):
    """A forearm lying along Y on the table, wrist toward +Y: a smooth stretched sphere, slimmer at the wrist."""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=64, radius=1.0, location=(x, 0, z))
    o = bpy.context.object
    o.name = name
    o.scale = (r, length / 2, r * 0.82)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for v in o.data.vertices:                  # flatten the ends (it is a forearm, not an egg) and slim the wrist
        y = v.co.y / (length / 2)
        k = 1.0 - 0.22 * max(0.0, y)
        v.co.x *= k
        v.co.z *= k
        v.co.y = math.copysign(min(abs(v.co.y), length / 2 * 0.86), v.co.y) * 1.16
    o.modifiers.new("S", "SUBSURF").levels = 1
    o.data.materials.append(skin_mat())
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def sleeve(x, length=22, r=4.25, z=3.4, y=-2):
    m = bpy.data.materials.get("Nylon")
    if m is None:
        m = bpy.data.materials.new("Nylon")
        m.use_nodes = True
        nt = m.node_tree
        b = nt.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (0.85, 0.72, 0.58, 1)
        b.inputs["Roughness"].default_value = 0.6
        if "Sheen Weight" in b.inputs:
            b.inputs["Sheen Weight"].default_value = 1.0
        wave = nt.nodes.new("ShaderNodeTexWave")
        wave.inputs["Scale"].default_value = 60
        wave.inputs["Distortion"].default_value = 2
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.35
        ramp.color_ramp.elements[0].color = (0.25, 0.25, 0.25, 1)
        ramp.color_ramp.elements[1].color = (0.8, 0.8, 0.8, 1)
        nt.links.new(wave.outputs["Fac"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], b.inputs["Alpha"])
        try:
            m.surface_render_method = "BLENDED"
        except Exception:
            pass
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=r, depth=length, end_fill_type="NOTHING", location=(x, y, z))
    o = bpy.context.object
    o.rotation_euler = (math.pi / 2, 0, 0)
    o.scale = (1.0, 0.84, 1.0)
    o.modifiers.new("S", "SUBSURF").levels = 1
    o.data.materials.append(m)
    return o


def scent_plume(src, to, count, rgb, strength, f_rise=1, spread=2.5, size=(0.12, 0.3)):
    """Glowing scent particles drifting from src toward `to` over the shot (a plume the mosquitoes follow)."""
    m = glow(f"Scent{len(bpy.data.materials)}", rgb, strength)
    src, to = Vector(src), Vector(to)
    for i in range(count):
        o = blob(f"sc{len(bpy.data.objects)}", random.uniform(*size), src, (1, 1, 1), m, lump=0, subdiv=2)
        f0 = f_rise + int(random.uniform(0, N))
        life = int(random.uniform(1.5, 3.0) * FPS)
        j = Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1)))
        a = src + j * 0.6
        b = to + j * spread
        # loop: each particle rises, then restarts at the source (wraps across the shot)
        pts = []
        fr = f0 - life * 3
        while fr < N + life:
            pts += [(fr, a), (fr + life - 1, b)]
            fr += life
        for fr_, p in pts:
            o.location = p
            o.keyframe_insert("location", frame=fr_)
        ad = o.animation_data
        if ad:
            for fc in _fcurves(ad.action):
                for k, kp in enumerate(fc.keyframe_points):
                    kp.interpolation = "LINEAR" if k % 2 == 0 else "CONSTANT"


def table_world():
    world((0.012, 0.013, 0.02))
    wood = organic("Table", (0.10, 0.07, 0.05), (0, 0, 0), 0.0, sss=0.0, noise=3, rough=0.6)
    b = wood.node_tree.nodes["Principled BSDF"]
    if "Coat Weight" in b.inputs:
        b.inputs["Coat Weight"].default_value = 0.0
    bpy.ops.mesh.primitive_plane_add(size=600, location=(0, 0, 0))
    bpy.context.object.data.materials.append(wood)
    area_light((30, -40, 60), (0, 0, 0), 1.2e4, (1.0, 0.9, 0.8), 40)
    area_light((-50, 20, 30), (0, 0, 0), 4e3, (0.5, 0.7, 1.0), 40)
    area_light((0, 60, 20), (0, 0, 4), 7e3, (1.0, 0.75, 0.5), 30)
    bloom(0.5, 0.9)


def acid(name, loc, scale=1.0):
    """A skin carboxylic acid, ball and stick: a carbon chain ending in COOH (two red oxygens)."""
    root = empty(name, loc)
    root.scale = (scale, scale, scale)
    C = bpy.data.materials.get("AcC") or glow("AcC", (0.95, 0.75, 0.25), 3.0)
    C.name = "AcC"
    O = bpy.data.materials.get("AcO") or glow("AcO", (1.0, 0.2, 0.15), 5.0)
    O.name = "AcO"
    n = random.choice((4, 5, 6, 8))
    pts = [(k * 0.6, 0.35 if k % 2 else -0.35, 0) for k in range(n)]
    for k, p in enumerate(pts):
        blob(f"{name}c{k}", 0.24, p, (1, 1, 1), C, lump=0, subdiv=2, parent=root)
    end = Vector(pts[-1])
    for d in ((0.45, 0.6, 0), (0.6, -0.45, 0)):
        blob(f"{name}o", 0.28, end + Vector(d), (1, 1, 1), O, lump=0, subdiv=2, parent=root)
    return root


# ---------------------------------------------------------------- shots
def shot_magnet(cam, tgt):
    table_world()
    forearm("ArmA", -6.5)
    forearm("ArmB", 6.5)
    scent_plume((6.5, 0, 8.5), (6.5, 0, 20), 60, (1.0, 0.6, 0.25), 3.0, size=(0.06, 0.16))
    scent_plume((-6.5, 0, 8.5), (-6.5, 0, 16), 12, (1.0, 0.6, 0.25), 1.5, size=(0.05, 0.12))
    for i in range(16):
        r, pv = mosquito(f"M{i}", 1.2)
        start = Vector((random.uniform(-22, 22), random.uniform(-25, 15), random.uniform(18, 34)))
        goes_b = i < 14                    # nearly all pick arm B
        x0 = 6.5 if goes_b else -6.5
        end = Vector((x0 + random.uniform(-3, 3), random.uniform(-10, 10), random.uniform(10, 15)))
        f_end = int(N * random.uniform(0.55, 0.95))
        path = wander_path(start, end, 1, f_end, 4.0) + [(N, end + Vector((random.uniform(-1, 1), 0, random.uniform(-0.5, 0.5))))]
        fly(r, pv, path)
    key_loc(cam, [(1, (15, -25, 12)), (N, (12, -20, 10))])
    key_loc(tgt, [(1, (5, -2, 9)), (N, (5.5, -2, 9))])
    smooth(cam)
    cam.data.lens = 45
    cam.data.dof.aperture_fstop = 2.8


def shot_sleeve(cam, tgt):
    table_world()
    forearm("Arm", 0)
    sleeve(0)
    r, pv = mosquito("M0", 1.2)
    fly(r, pv, wander_path((-14, -20, 22), (-9, -10, 16), 1, N, 2.0))
    key_loc(cam, [(1, (17, -32, 15)), (N, (13, -26, 12))])
    key_loc(tgt, [(1, (0, -3, 5)), (N, (0, -3, 5))])
    smooth(cam)
    cam.data.lens = 45
    cam.data.dof.aperture_fstop = 2.8


def _tunnel():
    glass = bpy.data.materials.new("Box")
    glass.use_nodes = True
    gb = glass.node_tree.nodes["Principled BSDF"]
    gb.inputs["Roughness"].default_value = 0.02
    gb.inputs["Alpha"].default_value = 0.08
    try:
        glass.surface_render_method = "BLENDED"
    except Exception:
        pass
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 14))
    box = bpy.context.object
    box.scale = (60, 22, 24)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)   # wire thickness in cm, not stretched
    edge = glow("Edge", (0.5, 0.8, 1.0), 0.8)
    box.data.materials.append(edge)
    wf = box.modifiers.new("W", "WIREFRAME")
    wf.thickness = 0.3
    wf.use_replace = True
    for sx in (-1, 1):                     # the two ports, each with a sleeve behind a mesh screen
        bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=6, depth=3, location=(sx * 30, 0, 14))
        port = bpy.context.object
        port.rotation_euler = (0, math.pi / 2, 0)
        port.data.materials.append(edge)
        s = sleeve(sx * 36, 14, 3.6, 14, 0)
        s.rotation_euler = (0, 0, math.pi / 2)
        s.rotation_euler = (0, math.pi / 2, 0)


def shot_choice(cam, tgt):
    table_world()
    _tunnel()
    skew = float(SHOT.get("skew", 0.8))
    scent_plume((30, 0, 14), (-5, 0, 14), int(30 + 60 * skew), (1.0, 0.6, 0.25), 3.0, spread=5)
    scent_plume((-30, 0, 14), (5, 0, 14), int(30 + 60 * (1 - skew)), (0.4, 0.8, 1.0), 2.0, spread=5)
    n = 14
    for i in range(n):
        r, pv = mosquito(f"M{i}", 2.6)
        start = Vector((random.uniform(-6, 6), random.uniform(-6, 6), random.uniform(8, 20)))
        right = random.random() < skew
        end = Vector(((15 if right else -15) + random.uniform(-2, 2), random.uniform(-4, 4), 14 + random.uniform(-4, 4)))
        f0 = int(N * random.uniform(0.05, 0.3))
        path = [(1, start)] + wander_path(start, end, f0, int(N * random.uniform(0.6, 0.95)), 3.0) + [(N, end)]
        fly(r, pv, path)
    key_loc(cam, [(1, (-22, -46, 27)), (N, (-16, -38, 22))])
    key_loc(tgt, [(1, (2, 0, 13)), (N, (3, 0, 13))])
    smooth(cam)
    cam.data.dof.aperture_fstop = 8.0


def shot_skin(cam, tgt):
    """Skin up close (units ~0.1 mm): cells, oil droplets at the pores, acid molecules rising off them."""
    world((0.01, 0.006, 0.006))
    m = organic("SkinMacro", (0.55, 0.30, 0.22), (0.7, 0.3, 0.2), 0.15, sss=0.8, noise=1.2, rough=0.55)
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=220, y_subdivisions=220, size=80, location=(0, 0, 0))
    g = bpy.context.object
    tex = bpy.data.textures.new("Cells", "VORONOI")
    tex.noise_scale = 1.6
    d = g.modifiers.new("D", "DISPLACE")
    d.texture = tex
    d.strength = -0.6
    g.modifiers.new("S", "SUBSURF").levels = 1
    g.data.materials.append(m)
    for p in g.data.polygons:
        p.use_smooth = True
    oil = bpy.data.materials.new("Oil")
    oil.use_nodes = True
    ob = oil.node_tree.nodes["Principled BSDF"]
    ob.inputs["Base Color"].default_value = (0.95, 0.8, 0.4, 1)
    ob.inputs["Roughness"].default_value = 0.02
    ob.inputs["Transmission Weight" if "Transmission Weight" in ob.inputs else "Transmission"].default_value = 0.6
    ob.inputs["Emission Color"].default_value = (1.0, 0.75, 0.3, 1)
    ob.inputs["Emission Strength"].default_value = 0.4
    drops = []
    for i in range(14):
        p = Vector((random.uniform(-14, 14), random.uniform(-10, 18), 0.2))
        o = blob(f"oil{i}", random.uniform(0.8, 1.8), p, (1, 1, 0.45), oil, 0.05, 2)
        drops.append(p)
    for i in range(26):                    # acids lifting off the oil and drifting up
        p0 = random.choice(drops) + Vector((0, 0, 0.6))
        a = acid(f"ac{i}", p0, random.uniform(0.35, 0.55))
        f0 = int(random.uniform(-0.4, 0.8) * N)
        p1 = p0 + Vector((random.uniform(-4, 4), random.uniform(-2, 6), random.uniform(14, 22)))
        key_loc(a, [(f0, p0), (f0 + int(N * 0.9), p1)])
        linear(a)
        a.rotation_euler = (random.uniform(0, 3), random.uniform(0, 3), random.uniform(0, 3))
        a.keyframe_insert("rotation_euler", frame=f0)
        a.rotation_euler = (random.uniform(0, 3), random.uniform(0, 3), random.uniform(0, 3))
        a.keyframe_insert("rotation_euler", frame=f0 + int(N * 0.9))
    area_light((20, -20, 30), (0, 0, 0), 6e3, (1.0, 0.85, 0.7), 20)
    area_light((-25, 15, 12), (0, 0, 0), 2.5e3, (0.4, 0.6, 1.0), 20)
    key_loc(cam, [(1, (3, -30, 16)), (N, (2, -24, 10))])
    key_loc(tgt, [(1, (0, 2, 3)), (N, (0, 2, 5))])
    smooth(cam)
    cam.data.dof.aperture_fstop = 2.8
    bloom(0.7, 0.7)


def shot_follow(cam, tgt):
    table_world()
    forearm("Arm", 0)
    scent_plume((0, 0, 8.5), (-6, -40, 26), 90, (1.0, 0.6, 0.25), 3.5, spread=4, size=(0.08, 0.2))
    many = int(SHOT.get("many", 1))
    for i in range(many):
        r, pv = mosquito(f"M{i}", 1.4)
        start = Vector((-6 + random.uniform(-6, 6), -40 + random.uniform(-6, 6), 26 + random.uniform(-4, 4)))
        end = Vector((random.uniform(-2.5, 2.5), random.uniform(-8, 8), 9.6))
        zig = []
        for k in range(12):                # zig-zag up the plume, as mosquitoes cast across an odour plume
            t = k / 11
            p = start.lerp(end, t) + Vector(((-1) ** k * 3.5 * (1 - t), 0, 0))
            zig.append((1 + int(t * N * random.uniform(0.75, 0.95)), p))
        zig.append((N, end))
        fly(r, pv, zig)
        if i == 0:
            hero = r
    # side-on to the plume: the arm low in frame, the scent trail rising across it, mosquitoes working down it
    key_loc(cam, [(1, (34, -30, 16)), (N, (24, -12, 12))])
    key_loc(tgt, [(1, (-2, -24, 15)), (N, (0, -6, 9))])
    smooth(cam)
    smooth(tgt)
    cam.data.lens = 40
    cam.data.dof.aperture_fstop = 5.6


def shot_land(cam, tgt):
    table_world()
    forearm("Arm", 0)
    r, pv = mosquito("M0", 1.4)
    end = Vector((0.5, -4, 3.4 + 3.28 + 0.8))
    path = wander_path((-8, -16, 14), end + Vector((0, 0, 1.2)), 1, int(N * 0.55), 1.2) + [(int(N * 0.7), end), (N, end)]
    fly(r, pv, path)
    key_loc(cam, [(1, (9, -16, 11)), (N, (6, -12, 8.5))])
    key_loc(tgt, [(1, (-2, -8, 9)), (int(N * 0.7), tuple(end)), (N, tuple(end))])
    smooth(cam)
    smooth(tgt)
    cam.data.dof.aperture_fstop = 2.8


def build(cam, tgt):
    {"mosq_magnet": shot_magnet, "mosq_sleeve": shot_sleeve, "mosq_choice": shot_choice, "mosq_skin": shot_skin,
     "mosq_follow": shot_follow, "mosq_land": shot_land}[KIND](cam, tgt)
