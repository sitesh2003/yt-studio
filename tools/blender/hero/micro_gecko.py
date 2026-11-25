"""Gecko shots for micro.py (25 Nov 2026). Autumn et al. 2002 PNAS 99:12252; Huber et al. 2005 PNAS 102:16293.

Kinds: gk_climb (a Tokay gecko climbing a glass pane, seen from behind the glass; `from_front` sees its back),
gk_toe (a toe pressed on glass: the ridges (lamellae) flattened against it), gk_setae (a forest of hairs on one
ridge; each hair fans into hundreds of tiny spatula tips; the camera dives in), gk_vdw (one spatula tip over the
glass, atom by atom: attraction links light up as it comes close), gk_peel (the toe peels off from the tip).
"""
import math
import random

from mathutils import Vector

KINDS = ("gk_climb", "gk_toe", "gk_setae", "gk_vdw", "gk_peel")


def install(g):
    mine = set(globals())
    globals().update({k: v for k, v in g.items() if not k.startswith("__") and k not in mine})


def gecko_skin():
    m = bpy.data.materials.get("Tokay")
    if m:
        return m
    m = bpy.data.materials.new("Tokay")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.55
    for k in ("Subsurface Weight",):
        if k in b.inputs:
            b.inputs[k].default_value = 0.25
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.inputs["Scale"].default_value = 0.7               # spots ~1.5 cm apart, in object space (cm)
    tco = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(tco.outputs["Object"], vor.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.18
    ramp.color_ramp.elements[0].color = (0.85, 0.32, 0.08, 1)     # the Tokay's orange spots
    ramp.color_ramp.elements[1].position = 0.24
    ramp.color_ramp.elements[1].color = (0.18, 0.26, 0.42, 1)     # blue-grey body
    nt.links.new(vor.outputs["Distance"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.5
    v2 = nt.nodes.new("ShaderNodeTexVoronoi")
    v2.inputs["Scale"].default_value = 14
    nt.links.new(v2.outputs["Distance"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def _meta(name, parts, m, parent=None):
    mb = bpy.data.metaballs.new(name)
    mb.resolution = 0.4
    mb.render_resolution = 0.2
    mb.threshold = 0.5
    for co, r, sz in parts:
        e = mb.elements.new()
        e.type = "ELLIPSOID"
        e.co = co
        e.radius = r * 1.7                 # metaball surfaces sit well inside the radius: fatter, so parts fuse
        e.size_x, e.size_y, e.size_z = sz
        e.stiffness = 2.0
    o = bpy.data.objects.new(name, mb)
    SC.collection.objects.link(o)
    o.data.materials.append(m)
    if parent:
        o.parent = parent
    return o


def toe_pad_mat():
    return bpy.data.materials.get("Pad") or organic("Pad", (0.75, 0.68, 0.6), (0.6, 0.5, 0.4), 0.05, sss=0.6, noise=8, rough=0.7)


def gecko(name):
    """A Tokay gecko in cm (~25 cm with tail), belly on the XY plane facing +Y (up the glass), back toward +Z.
    Returns (root, [four leg pivots])."""
    skin = gecko_skin()
    pad = toe_pad_mat()
    root = empty(name)
    base = "Gk" + name
    _meta(base, [((0, 0, 1.1), 2.0, (0.9, 2.6, 0.55)),          # body
                 ((0, 5.6, 1.2), 1.5, (1.15, 1.25, 0.65)),      # head
                 ((0, 3.8, 1.1), 1.1, (0.9, 1.0, 0.6)),         # neck
                 ((0, -5.0, 0.9), 1.1, (0.8, 1.5, 0.5)),        # tail, tapering, overlapping so it fuses
                 ((0, -7.4, 0.8), 0.95, (0.7, 1.5, 0.45)),
                 ((0, -9.8, 0.7), 0.8, (0.62, 1.5, 0.42)),
                 ((0, -12.0, 0.6), 0.65, (0.55, 1.5, 0.4)),
                 ((0, -14.0, 0.5), 0.5, (0.5, 1.4, 0.38))], skin, root)
    for sx in (-1, 1):
        blob(name + "eye", 0.45, (sx * 1.25, 6.4, 1.8), (1, 1, 1), glow("GkEye", (0.9, 0.7, 0.2), 1.2), 0, parent=root)
    pivots = []
    for sx, sy in ((-1, 2.6), (1, 2.6), (-1, -2.4), (1, -2.4)):
        pv = empty(name + "leg", (sx * 1.4, sy, 0.9))
        pv.parent = root
        _meta(base, [((sx * 1.3, 0.3 * (1 if sy > 0 else -1), 0.1), 0.6, (1.6, 0.6, 0.5)),
                     ((sx * 2.6, 0.6 * (1 if sy > 0 else -1), -0.4), 0.45, (0.6, 0.6, 1.0))], skin, pv)
        for k in range(5):                                       # five splayed toes with flat pads
            a = math.radians((-70 + k * 35) * sx + (0 if sy > 0 else 180))
            d = Vector((math.sin(a), math.cos(a), 0))
            c = Vector((sx * 2.7, 0.6 * (1 if sy > 0 else -1), -0.75)) + d * 1.1
            t = blob(name + "toe", 0.5, c, (0.32, 0.75, 0.12), pad, 0.02, 4, parent=pv)
            t.rotation_euler = (0, 0, -a)
        pivots.append(pv)
    return root, pivots


def glass_pane(size=80, z=0.0):
    g = bpy.data.materials.new("Glass")
    g.use_nodes = True
    b = g.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.85, 0.95, 1.0, 1)
    b.inputs["Roughness"].default_value = 0.02
    b.inputs["Alpha"].default_value = 0.12
    if "Specular IOR Level" in b.inputs:
        b.inputs["Specular IOR Level"].default_value = 0.08   # see through it, not a mirror of the lights
    try:
        g.surface_render_method = "BLENDED"
    except Exception:
        pass
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, z - 0.3))
    p = bpy.context.object
    p.scale = (size, size * 2, 0.6)
    p.data.materials.append(g)
    return p


def lab_world(tint=(0.02, 0.03, 0.05)):
    world(tint)
    area_light((20, -30, 40), (0, 0, 0), 2.6e4, (1.0, 0.92, 0.85), 40)
    area_light((-30, 20, -30), (0, 0, 0), 1.2e4, (0.5, 0.75, 1.0), 40)
    area_light((0, 40, 10), (0, 0, 0), 4e3, (1.0, 0.7, 0.5), 30)
    bloom(0.5, 0.9)


# ---------------------------------------------------------------- shots
def shot_climb(cam, tgt):
    """The glass is the XY plane; the gecko walks up +Y on its top side; the camera is below the glass looking up
    through it at the feet (the famous view), or above for its back."""
    lab_world()
    glass_pane()
    g, legs = gecko("G")
    speed = 6.0                                                  # cm per second up the glass
    key_loc(g, [(1, (0, -6, 0)), (N, (0, -6 + speed * N / FPS, 0))])
    linear(g)
    stride = int(FPS * 0.4)
    for i, pv in enumerate(legs):                               # diagonal pairs step together
        phase = 0 if i in (0, 3) else stride // 2
        for fr in range(1 - stride, N + stride, stride):
            f0 = fr + phase
            pv.rotation_euler = (0, 0, math.radians(18))
            pv.keyframe_insert("rotation_euler", frame=f0)
            pv.rotation_euler = (0, 0, math.radians(-18))
            pv.keyframe_insert("rotation_euler", frame=f0 + stride // 2)
    follow = empty("Follow")
    follow.parent = g
    if SHOT.get("from_front"):
        key_loc(cam, [(1, (14, -30, 28)), (N, (10, -10, 22))])
    else:
        key_loc(cam, [(1, (6, -26, -22)), (N, (4, -8, -16))])
    c = tgt.constraints.new("COPY_LOCATION")
    c.target = g
    smooth(cam)
    cam.data.lens = 40
    cam.data.dof.aperture_fstop = 4.0


def _ridges(name, n, at, m, w=3.0):
    rs = []
    for k in range(n):
        r = blob(f"{name}{k}", 1.0, (at[0], at[1] + k * 0.42, at[2]), (w, 0.18, 0.12), m, 0.02, 3)
        rs.append(r)
    return rs


def shot_toe(cam, tgt):
    """One toe from under the glass, magnified (units ~mm): pale ridges (lamellae) pressed flat on the glass."""
    lab_world((0.01, 0.015, 0.03))
    glass_pane(60, 0)
    pad = toe_pad_mat()
    toe = _meta("GkToe", [((0, 0, 1.6), 2.0, (1.0, 3.6, 0.7)), ((0, 7, 1.4), 1.4, (1.0, 1.4, 0.7))], gecko_skin())
    for k in range(14):
        blob(f"lam{k}", 1.0, (0, -5.6 + k * 0.85, 0.35), (1.7, 0.32, 0.3), pad, 0.03, 3)
    key_loc(cam, [(1, (6, -14, -12)), (N, (3, -8, -8))])
    key_loc(tgt, [(1, (0, 0, 0.3))])
    smooth(cam)
    cam.data.dof.aperture_fstop = 2.8


def _seta(name):
    """One seta: a stalk that branches at the top into a brush of tiny flat spatula paddles (stylised count)."""
    m = bpy.data.materials.get("Keratin") or organic("Keratin", (0.8, 0.72, 0.55), (0.9, 0.75, 0.45), 0.4, sss=0.6, noise=6)
    parts = []
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.06, depth=3.0, location=(0, 0, 1.5))
    parts.append(bpy.context.object)
    for k in range(18):
        a = k * 2.4
        rr = 0.12 + 0.03 * (k % 6)
        tip = Vector((rr * math.cos(a), rr * math.sin(a) + 0.15, 3.25))
        base = Vector((0, 0.05, 2.9))
        d = tip - base
        bpy.ops.mesh.primitive_cylinder_add(vertices=5, radius=0.012, depth=d.length, location=(base + tip) / 2)
        br = bpy.context.object
        br.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
        parts.append(br)
        bpy.ops.mesh.primitive_cube_add(size=1, location=tip + Vector((0, 0, 0.02)))
        sp = bpy.context.object
        sp.scale = (0.05, 0.05, 0.006)
        parts.append(sp)
    bpy.ops.object.select_all(action="DESELECT")
    for o in parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    o = bpy.context.object
    o.name = name
    o.data.materials.append(m)
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def shot_setae(cam, tgt):
    """A forest of setae standing on one ridge (stylised: real setae are ~0.1 mm; here 1 unit ~ 30 um).
    The camera dives from the forest down to the brushes of spatula tips touching the glass."""
    lab_world((0.01, 0.012, 0.025))
    src = _seta("SetaSrc")
    src.location = (0, 0, -500)
    pts = []
    for i in range(-26, 27):
        for j in range(-14, 30):
            pts.append((i * 0.55 + random.uniform(-0.12, 0.12), j * 0.55 + random.uniform(-0.12, 0.12), 0))
    _instancer("Setae", pts, src, 0.9, 1.1)
    base = organic("Ridge", (0.7, 0.6, 0.5), (0.6, 0.45, 0.35), 0.2, sss=0.7, noise=2)
    bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, 0))
    bpy.context.object.data.materials.append(base)
    glass = bpy.data.materials.new("GlassTop")
    glass.use_nodes = True
    gb = glass.node_tree.nodes["Principled BSDF"]
    gb.inputs["Base Color"].default_value = (0.6, 0.85, 1.0, 1)
    gb.inputs["Alpha"].default_value = 0.1
    gb.inputs["Emission Color"].default_value = (0.4, 0.7, 1.0, 1)
    gb.inputs["Emission Strength"].default_value = 0.15
    try:
        glass.surface_render_method = "BLENDED"
    except Exception:
        pass
    bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, 3.32))
    bpy.context.object.data.materials.append(glass)
    key_loc(cam, [(1, (6, -18, 7)), (N, (1.6, -3.5, 3.0))])
    key_loc(tgt, [(1, (0, 2, 2.0)), (N, (0, 0.5, 3.1))])
    smooth(cam)
    smooth(tgt)
    cam.data.lens = 35
    cam.data.dof.aperture_fstop = 2.0


def shot_vdw(cam, tgt):
    """Atom scale: the tip's atoms (warm) come down to the glass's atoms (cool); when close, faint links light up
    between neighbours: the van der Waals pull (weak, short-range, but a billion tips add up)."""
    world((0.004, 0.006, 0.018))
    warm = organic("TipAtom", (0.9, 0.6, 0.3), (1.0, 0.6, 0.25), 1.5, sss=0.6, noise=5)
    cool = organic("GlassAtom", (0.3, 0.6, 0.9), (0.3, 0.7, 1.0), 1.2, sss=0.6, noise=5)
    link = glow("Link", (1.0, 0.95, 0.6), 0.0)
    tip = empty("Tip", (0, 0, 9))
    for i in range(-5, 6):
        for j in range(-5, 6):
            for k in range(2):
                blob(f"ta{i}_{j}_{k}", 0.62, (i * 1.4 + 0.7 * k, j * 1.4 + 0.7 * k, k * 1.2), (1, 1, 1), warm, 0.05, 3, subdiv=2, parent=tip)
    for i in range(-9, 10):
        for j in range(-9, 10):
            for k in range(2):
                blob(f"ga{i}_{j}_{k}", 0.62, (i * 1.4 + 0.7 * k, j * 1.4 + 0.7 * k, -k * 1.2), (1, 1, 1), cool, 0.05, 3, subdiv=2)
    f_close = F(0.45)
    key_loc(tip, [(1, (0, 0, 9)), (f_close, (0, 0, 1.55)), (N, (0, 0, 1.45))])
    smooth(tip)
    for i in range(-5, 6, 2):                                   # attraction links between facing atoms
        for j in range(-5, 6, 2):
            bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.07, depth=0.95, location=(i * 1.4, j * 1.4, 0.95))
            bpy.context.object.data.materials.append(link)
    key_input(emis_input(link), [(1, 0.0), (f_close - 6, 0.0), (f_close + 6, 8.0), (N, 6.0)])
    area_light((-15, -20, 25), (0, 0, 2), 4e3, (1.0, 0.9, 0.8), 20)
    area_light((20, 10, -10), (0, 0, 0), 2e3, (0.4, 0.6, 1.0), 20)
    key_loc(cam, [(1, (4, -24, 8)), (N, (3, -20, 5))])
    key_loc(tgt, [(1, (0, 0, 2.5)), (N, (0, 0, 1.0))])
    smooth(cam)
    cam.data.dof.aperture_fstop = 5.6
    bloom(0.8, 0.7)


def shot_peel(cam, tgt):
    """The toe lets go by peeling from its tip, like tape: the ridges lift one after another."""
    lab_world((0.01, 0.015, 0.03))
    glass_pane(60, 0)
    pad = toe_pad_mat()
    hinge = empty("Hinge", (0, -6, 0.3))
    _meta("GkToeP", [((0, 6, 1.3), 2.0, (1.0, 3.6, 0.7)), ((0, 12.5, 1.1), 1.4, (1.0, 1.4, 0.7))], gecko_skin(), hinge)
    for k in range(14):
        blob(f"plam{k}", 1.0, (0, 0.4 + k * 0.85, 0.05), (1.7, 0.32, 0.3), pad, 0.03, 3, parent=hinge)
    f0, f1 = F(0.25), F(0.75)
    for fr, ang in ((1, 0), (f0, 0), (f1, -55), (N, -60)):     # the tip rises first: rotate about the heel
        hinge.rotation_euler = (math.radians(-ang), 0, 0)
        hinge.keyframe_insert("rotation_euler", frame=fr)
    hinge.location = (0, -6, 0.3)
    smooth(hinge)
    key_loc(cam, [(1, (32, 4, 10)), (N, (30, 5, 12))])
    key_loc(tgt, [(1, (0, 4, 4))])
    smooth(cam)
    cam.data.dof.aperture_fstop = 4.0


def build(cam, tgt):
    {"gk_climb": shot_climb, "gk_toe": shot_toe, "gk_setae": shot_setae, "gk_vdw": shot_vdw,
     "gk_peel": shot_peel}[KIND](cam, tgt)
