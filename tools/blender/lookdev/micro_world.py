"""Look-development test (24 Nov 2026): can we reach the cinematic "inside a cell" level of the reference Shorts
the owner added to the EVER THOUGHT WHY playlist (glowing organic proteins, a beaded microtubule track, deep
depth of field, floating particles, dark background)?

    blender -b --python tools/blender/lookdev/micro_world.py -- <out.png> [eevee|cycles] [w] [h]

Everything is procedural (no downloaded assets): a microtubule built the way it is in a cell (13 protofilaments,
alternating alpha/beta tubulin beads on a helical lattice, 8 nm per dimer), a two-headed motor protein with a coiled
stalk, a cargo vesicle, and drifting molecules. Scale is stylised for the camera; the structure is real.
"""
import math
import random
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else "micro.png"
ENGINE = argv[1] if len(argv) > 1 else "eevee"
W = int(argv[2]) if len(argv) > 2 else 1080
H = int(argv[3]) if len(argv) > 3 else 1920
random.seed(3)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.render.film_transparent = False
if ENGINE == "cycles":
    sc.render.engine = "CYCLES"
    sc.cycles.samples = 96
    sc.cycles.use_denoising = True
    try:
        pr = bpy.context.preferences.addons["cycles"].preferences
        pr.compute_device_type = "OPTIX"
        pr.get_devices()
        for d in pr.devices:
            d.use = True
        sc.cycles.device = "GPU"
    except Exception:
        pass
else:
    sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in [e.identifier for e in
                                                                       bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items] else "BLENDER_EEVEE"
    sc.eevee.taa_render_samples = 64
sc.view_settings.view_transform = "Standard"     # AgX washed the coloured glows to white
sc.view_settings.look = "AgX - Punchy" if "AgX - Punchy" in [i.identifier for i in sc.view_settings.bl_rna.properties["look"].enum_items] else "None"

# world: near-black blue with a faint gradient
world = bpy.data.worlds.new("W")
sc.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.004, 0.008, 0.02, 1)
bg.inputs["Strength"].default_value = 1.0


def mat_organic(name, base, emit, emit_str, sss=0.6, noise_scale=6.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1)
    b.inputs["Roughness"].default_value = 0.35
    for k in ("Subsurface Weight", "Subsurface"):
        if k in b.inputs:
            b.inputs[k].default_value = sss
            break
    if "Subsurface Radius" in b.inputs:
        b.inputs["Subsurface Radius"].default_value = (1.0, 0.5, 0.3)
    if "Coat Weight" in b.inputs:
        b.inputs["Coat Weight"].default_value = 0.4
    # emission broken up by noise, so it glows from within unevenly (the reference's living look)
    tex = nt.nodes.new("ShaderNodeTexNoise")
    tex.inputs["Scale"].default_value = noise_scale
    tex.inputs["Detail"].default_value = 6
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.45
    ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
    ramp.color_ramp.elements[1].color = (*emit, 1)
    nt.links.new(tex.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = emit_str
    # surface bumps
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.35
    n2 = nt.nodes.new("ShaderNodeTexNoise")
    n2.inputs["Scale"].default_value = noise_scale * 3
    nt.links.new(n2.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def lumpy(obj, strength=0.12, scale=2.5):
    t = bpy.data.textures.new(obj.name + "N", "CLOUDS")
    t.noise_scale = 1.0 / scale
    md = obj.modifiers.new("Lumps", "DISPLACE")
    md.texture = t
    md.strength = strength
    md.mid_level = 0.5


# --- the microtubule: 13 protofilaments, alpha/beta tubulin, a 3-start helix (a dimer every 8 nm) -----------------
alpha = mat_organic("Alpha", (0.05, 0.42, 0.36), (0.1, 0.9, 0.7), 0.6, noise_scale=4)
beta = mat_organic("Beta", (0.04, 0.30, 0.30), (0.05, 0.6, 0.6), 0.35, noise_scale=4)
R, PF, MON = 1.25, 13, 0.4      # tube radius, protofilaments, monomer spacing (scene units; 1 unit ~ 10 nm)
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=0.24)
proto_a = bpy.context.object
lumpy(proto_a, 0.05, 6)
proto_a.data.materials.append(alpha)
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=0.24)
proto_b = bpy.context.object
lumpy(proto_b, 0.05, 6)
proto_b.data.materials.append(beta)
for o in (proto_a, proto_b):
    o.location = (0, 0, -100)
coll = bpy.data.collections.new("MT")
sc.collection.children.link(coll)
pitch = 3 * MON * 2 / PF          # 3-start lattice: each protofilament is offset along the axis
for p in range(PF):
    ang = 2 * math.pi * p / PF
    for k in range(-60, 26):
        y = k * MON + p * pitch / 2
        src = proto_a if k % 2 == 0 else proto_b
        o = bpy.data.objects.new(f"t{p}_{k}", src.data)
        coll.objects.link(o)
        o.location = (R * math.cos(ang), y, R * math.sin(ang))
        o.scale = (1.0, 1.15, 1.0)
        o.rotation_euler = (random.uniform(0, 3), random.uniform(0, 3), random.uniform(0, 3))

# --- the motor protein: two heads on the track, a coiled-coil stalk up to the cargo -------------------------------
gold = mat_organic("Motor", (0.95, 0.45, 0.06), (1.0, 0.45, 0.05), 6.0, sss=1.0, noise_scale=3)
heads = []
for i, (y, lift) in enumerate(((-0.9, 0.0), (0.25, 0.35))):          # trailing head down, leading head stepping
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=0.42, location=(0.15, y, R + 0.45 + lift))
    h = bpy.context.object
    h.scale = (1.1, 0.9, 0.8)
    lumpy(h, 0.18, 3.5)
    h.modifiers.new("S", "SUBSURF").levels = 1
    h.data.materials.append(gold)
    heads.append(h)
# the stalk: two strands twisted round each other (a coiled coil), rising to the vesicle
top = Vector((0.3, -0.2, R + 6.0))
for strand in (0, 1):
    cu = bpy.data.curves.new(f"stalk{strand}", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = 0.07
    cu.bevel_resolution = 4
    sp = cu.splines.new("NURBS")
    pts = []
    base = heads[0].location.lerp(heads[1].location, 0.5) + Vector((0, 0, 0.45))
    for j in range(40):
        t = j / 39
        c = base.lerp(top, t)
        a = t * 14 * math.pi + strand * math.pi
        pts.append(c + Vector((0.12 * math.cos(a), 0.12 * math.sin(a), 0)))
    sp.points.add(len(pts) - 1)
    for p_, v in zip(sp.points, pts):
        p_.co = (*v, 1)
    sp.use_endpoint_u = True
    o = bpy.data.objects.new(f"stalk{strand}", cu)
    sc.collection.objects.link(o)
    o.data.materials.append(gold)

# --- the cargo: a vesicle, a soap-bubble membrane full of glowing molecules ---------------------------------------
ves = bpy.data.materials.new("Vesicle")
ves.use_nodes = True
vb = ves.node_tree.nodes["Principled BSDF"]
vb.inputs["Base Color"].default_value = (0.9, 0.35, 0.45, 1)
vb.inputs["Roughness"].default_value = 0.05
vb.inputs["Transmission Weight" if "Transmission Weight" in vb.inputs else "Transmission"].default_value = 0.85
vb.inputs["IOR"].default_value = 1.25
if "Thin Film Thickness" in vb.inputs:
    vb.inputs["Thin Film Thickness"].default_value = 450
vb.inputs["Emission Color"].default_value = (1.0, 0.3, 0.4, 1)
vb.inputs["Emission Strength"].default_value = 0.25
try:
    ves.surface_render_method = "DITHERED"
except Exception:
    pass
bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, radius=3.3, location=(0.5, -0.4, R + 9.0))
v = bpy.context.object
lumpy(v, 0.25, 1.2)
v.data.materials.append(ves)
inner = mat_organic("Inner", (0.95, 0.75, 0.2), (1.0, 0.7, 0.2), 6.0, noise_scale=3)
for _ in range(90):
    d = Vector((random.gauss(0, 1), random.gauss(0, 1), random.gauss(0, 1))).normalized() * random.uniform(0, 2.7)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=random.uniform(0.05, 0.18),
                                          location=v.location + d)
    bpy.context.object.data.materials.append(inner)

# --- the soup: molecules drifting everywhere (they become bokeh out of focus) -------------------------------------
cols = [(0.2, 0.9, 1.0), (1.0, 0.6, 0.2), (0.9, 0.3, 0.6), (0.5, 1.0, 0.4)]
for i in range(260):
    loc = Vector((random.uniform(-14, 14), random.uniform(-40, 12), random.uniform(-10, 18)))
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=random.uniform(0.04, 0.25), location=loc)
    m = bpy.data.materials.new(f"dust{i}")
    m.use_nodes = True
    e = m.node_tree.nodes["Principled BSDF"]
    c = random.choice(cols)
    e.inputs["Base Color"].default_value = (*c, 1)
    e.inputs["Emission Color"].default_value = (*c, 1)
    e.inputs["Emission Strength"].default_value = random.uniform(2, 10)
    bpy.context.object.data.materials.append(m)

# --- light: a warm key from above-behind (rim on the motor), cool fill, and a faint fog --------------------------
for loc, energy, col, size in (((3, 8, R + 12), 2500, (1.0, 0.75, 0.5), 6),
                               ((-8, -6, R + 3), 900, (0.3, 0.7, 1.0), 8),
                               ((0, -3, R - 6), 400, (0.2, 1.0, 0.8), 10)):
    ld = bpy.data.lights.new("L", "AREA")
    ld.energy, ld.color, ld.size = energy, col, size
    lo = bpy.data.objects.new("L", ld)
    sc.collection.objects.link(lo)
    lo.location = loc
    lo.rotation_euler = (Vector((0, 0, R)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()

# --- camera: low, close to the track, looking up the stalk to the cargo; shallow focus on the heads --------------
cd = bpy.data.cameras.new("C")
cd.lens = 32
cd.dof.use_dof = True
cd.dof.aperture_fstop = 0.35
cam = bpy.data.objects.new("Cam", cd)
sc.collection.objects.link(cam)
sc.camera = cam
cam.location = (3.4, -4.4, R + 0.9)
tgt = Vector((-0.2, 0.6, R + 3.2))
cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
cd.dof.focus_distance = (heads[0].location.lerp(heads[1].location, 0.5) - cam.location).length

# --- glow in the compositor (the reference's soft bloom); Blender 5 keeps it in a node group ------------------
try:
    ng = bpy.data.node_groups.new("Comp", "CompositorNodeTree")
    ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    sc.compositing_node_group = ng
    rl = ng.nodes.new("CompositorNodeRLayers")
    out = ng.nodes.new("NodeGroupOutput")
    gl = ng.nodes.new("CompositorNodeGlare")
    for k, v in (("Type", "Bloom"), ("Quality", "High")):
        if k in gl.inputs:
            gl.inputs[k].default_value = v
    for k, v in (("Threshold", 0.5), ("Strength", 0.9), ("Size", 0.7)):
        if k in gl.inputs:
            gl.inputs[k].default_value = v
    if hasattr(gl, "glare_type"):
        gl.glare_type = "BLOOM"
    ng.links.new(rl.outputs["Image"], gl.inputs["Image"])
    ng.links.new(gl.outputs["Image"], out.inputs[0])
except Exception as ex:
    print("glare skipped:", ex)

sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("LOOKDEV", OUT)
