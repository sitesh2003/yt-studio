"""Look v2 (28 Nov 2026): step 1 of the council's 3D order (research/council/2026-11-28.md).

Opt-in per spec or per shot with  "look": "v2"  so every older spec renders exactly as before.
What it does, after a scene is built:
  1. render quality: EEVEE ray tracing + fast GI (contact shadows and bounce light), soft jittered shadows,
     more samples, restrained motion blur, AgX tone mapping so bright glows roll off instead of clipping;
  2. lighting: the scene's brightest area light becomes the KEY (soft shadow), and a cool RIM light behind the
     subject and a weak warm BOUNCE from below are added, placed from the camera's first-frame view;
  3. world: the flat background colour becomes a soft vertical gradient (gives shiny surfaces something to reflect);
  4. surfaces: every lit material gets micro detail - roughness that varies across the surface and a fine bump,
     scaled to the size of the object that wears it (emission-only and see-through materials are left alone).
Materials for anatomy-first models (chitin, insect wing, skin, keratin, bone) live here too.
"""
import math

import bpy
from mathutils import Vector


def _set(obj, **kw):
    for k, v in kw.items():
        if obj is not None and hasattr(obj, k):
            try:
                setattr(obj, k, v)
            except Exception as ex:
                print("look: skip", k, ex)


# ---------------------------------------------------------------- 1. render quality
def render_quality(SC, preview=False, blur=0.3):
    e = SC.eevee
    _set(e, use_raytracing=True, ray_tracing_method="SCREEN", use_fast_gi=True, fast_gi_method="GLOBAL_ILLUMINATION",
         fast_gi_quality=0.5, fast_gi_distance=0.0, use_shadows=True, shadow_ray_count=2, shadow_step_count=8,
         shadow_resolution_scale=1.0, taa_render_samples=16 if preview else 48, clamp_surface_indirect=10.0)
    _set(getattr(e, "ray_tracing_options", None), resolution_scale="2", use_denoise=True, trace_max_roughness=0.5)
    _set(SC.render, use_motion_blur=blur > 0, motion_blur_shutter=blur)
    try:
        SC.view_settings.view_transform = "AgX"
        looks = [i.identifier for i in SC.view_settings.bl_rna.properties["look"].enum_items]
        for want in ("AgX - Punchy", "AgX - Medium High Contrast"):
            if want in looks:
                SC.view_settings.look = want
                break
    except Exception as ex:
        print("look: tone mapping kept", ex)


# ---------------------------------------------------------------- 2. lighting
def _cam_view(SC):
    cam = SC.camera
    SC.frame_set(SC.frame_start)
    c = cam.matrix_world.translation.copy()
    fwd = (cam.matrix_world.to_quaternion() @ Vector((0, 0, -1))).normalized()
    dist = cam.data.dof.focus_distance or 10.0
    if cam.data.dof.focus_object:
        dist = (cam.data.dof.focus_object.matrix_world.translation - c).length
    return c, fwd, max(dist, 0.5)


def _area(name, loc, at, energy, rgb, size):
    ld = bpy.data.lights.new(name, "AREA")
    ld.energy, ld.color, ld.size = energy, rgb, size
    _set(ld, use_shadow=True, use_shadow_jitter=True, shadow_jitter_overblur=10.0)
    lo = bpy.data.objects.new(name, ld)
    bpy.context.scene.collection.objects.link(lo)
    lo.location = loc
    lo.rotation_euler = (Vector(at) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return lo


def light_rig(SC, rim=1.0, bounce=0.18):
    lights = [o for o in SC.objects if o.type == "LIGHT"]
    c, fwd, dist = _cam_view(SC)
    subj = c + fwd * dist
    up = Vector((0, 0, 1))
    right = fwd.cross(up).normalized() if abs(fwd.z) < 0.95 else Vector((1, 0, 0))
    key = max(lights, key=lambda o: o.data.energy, default=None)
    if key is None:                        # no light at all: make a key, 45 degrees left and above the camera
        key = _area("Key", subj - fwd * dist - right * dist + up * dist, subj, 900 * dist ** 2 / 25, (1.0, 0.95, 0.88),
                    dist * 0.6)
    for o in lights:
        _set(o.data, use_shadow=True, use_shadow_jitter=True)
    k = key.data
    k.size = max(getattr(k, "size", 1.0), dist * 0.35)          # a large source = soft, believable shadow edges
    dk = max((key.matrix_world.translation - subj).length, 0.1)
    # irradiance at the subject ~ energy / distance^2, so each added light is set RELATIVE to what the key delivers
    per = k.energy / dk ** 2

    def at_subject(loc, ratio):
        return per * ratio * (Vector(loc) - subj).length ** 2

    # rim: behind the subject, opposite side to the key, above - draws the silhouette out of a dark ground
    side = 1 if (key.matrix_world.translation - subj).dot(right) < 0 else -1
    rl = subj + fwd * dist * 0.9 + right * side * dist * 0.8 + up * dist * 0.6
    _area("Rim", rl, subj, at_subject(rl, 0.9 * rim), (0.85, 0.92, 1.0), dist * 0.25)
    # bounce: weak, warm, from below the camera - lifts the shadow side like light off a floor
    bl = subj - fwd * dist * 0.6 - up * dist * 0.7
    _area("Bounce", bl, subj, at_subject(bl, bounce), (1.0, 0.82, 0.62), dist * 0.9)


# ---------------------------------------------------------------- 3. world gradient
def world_gradient(SC, lift=1.8):
    w = SC.world
    if not w or not w.use_nodes:
        return
    nt = w.node_tree
    bg = nt.nodes.get("Background")
    if not bg or bg.inputs["Color"].is_linked:
        return
    if nt.animation_data and nt.animation_data.action:        # an animated background colour: leave it alone
        return
    col = list(bg.inputs["Color"].default_value)[:3]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    rp = nt.nodes.new("ShaderNodeValToRGB")
    rp.color_ramp.elements[0].position = 0.3
    rp.color_ramp.elements[0].color = (*[x * 0.45 for x in col], 1)
    rp.color_ramp.elements[1].position = 0.85
    rp.color_ramp.elements[1].color = (*[min(1.0, x * lift + 0.004) for x in col], 1)
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = -1.0
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], rp.inputs["Fac"])
    nt.links.new(rp.outputs["Color"], bg.inputs["Color"])


# ---------------------------------------------------------------- 4. micro detail on every lit material
def _size_of(m):
    best = 0.0
    for o in bpy.data.objects:
        if o.type in ("MESH", "META", "CURVE") and any(s.material == m for s in o.material_slots):
            best = max(best, max(o.dimensions) if max(o.dimensions) > 0 else 0.0)
    return best or 1.0


def micro_detail(m, scale=None, bump=0.12, rough_spread=0.18):
    if not m.use_nodes or m.get("look_v2"):
        return
    nt = m.node_tree
    b = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if b is None:
        return
    if b.inputs["Alpha"].default_value < 0.6 or b.inputs["Transmission Weight"].default_value > 0.5:
        return                              # glass, wings, x-ray shells: keep them clean
    base = b.inputs["Base Color"].default_value
    if not b.inputs["Base Color"].is_linked and max(base[:3]) > 0.5 and b.inputs["Emission Strength"].default_value > 1.5:
        return                              # pure glow
    m["look_v2"] = 1
    size = scale or 40.0 / _size_of(m)      # ~40 detail cells across the object
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (size, size, size)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    # roughness that varies across the surface (real surfaces are never one even sheen)
    if not b.inputs["Roughness"].is_linked:
        r0 = b.inputs["Roughness"].default_value
        n1 = nt.nodes.new("ShaderNodeTexNoise")
        n1.inputs["Scale"].default_value = 0.35
        n1.inputs["Detail"].default_value = 4
        nt.links.new(mp.outputs["Vector"], n1.inputs["Vector"])
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs["To Min"].default_value = max(0.02, r0 - rough_spread)
        mr.inputs["To Max"].default_value = min(1.0, r0 + rough_spread)
        nt.links.new(n1.outputs["Fac"], mr.inputs["Value"])
        nt.links.new(mr.outputs["Result"], b.inputs["Roughness"])
    # fine bump, chained in front of whatever bump the material already has
    n2 = nt.nodes.new("ShaderNodeTexVoronoi")
    n2.inputs["Scale"].default_value = 3.0
    nt.links.new(mp.outputs["Vector"], n2.inputs["Vector"])
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = bump
    bp.inputs["Distance"].default_value = 0.02
    nt.links.new(n2.outputs["Distance"], bp.inputs["Height"])
    if b.inputs["Normal"].is_linked:
        prev = b.inputs["Normal"].links[0].from_socket
        nt.links.new(prev, bp.inputs["Normal"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])


def apply(SC, preview=False, shot=None):
    shot = shot or {}
    render_quality(SC, preview, shot.get("blur", 0.3))
    if shot.get("rig", True):
        light_rig(SC, shot.get("rim", 1.0), shot.get("bounce", 0.18))
    if shot.get("gradient", True):
        world_gradient(SC)
    for m in list(bpy.data.materials):
        if m.users:
            micro_detail(m)
    print("look v2 applied")


# ---------------------------------------------------------------- materials for anatomy-first models
def _principled(name):
    m = bpy.data.materials.get(name)
    if m:
        return m, None
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    return m, m.node_tree.nodes["Principled BSDF"]


def _coord(nt, scale, stretch=(1, 1, 1)):
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = tuple(scale * s for s in stretch)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    return mp.outputs["Vector"]


def chitin(name, rgb, scale_size=60.0, film=0.0):
    """Insect cuticle covered in tiny flat scales: dark, glossy coat, scale-pattern bump, optional thin-film sheen."""
    m, b = _principled(name)
    if b is None:
        return m
    nt = m.node_tree
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = 0.42
    b.inputs["Coat Weight"].default_value = 0.55
    b.inputs["Coat Roughness"].default_value = 0.18
    b.inputs["Sheen Weight"].default_value = 0.25
    if film:
        b.inputs["Thin Film Thickness"].default_value = film
    v = nt.nodes.new("ShaderNodeTexVoronoi")
    v.feature = "F1"
    v.inputs["Scale"].default_value = scale_size
    nt.links.new(_coord(nt, 1.0, (1, 0.45, 1)), v.inputs["Vector"])      # scales are longer than wide
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.35
    bp.inputs["Distance"].default_value = 0.004
    nt.links.new(v.outputs["Distance"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    m["look_v2"] = 1
    return m


def insect_wing(name, vein_scale=6.0, veins=True):
    """Transparent membrane with dark veins and the interference colours real insect wings show
    (Shevtsova et al. 2011, PNAS 108:668 - wing interference patterns from membrane thickness)."""
    m, b = _principled(name)
    if b is None:
        return m
    nt = m.node_tree
    b.inputs["Base Color"].default_value = (0.85, 0.88, 0.92, 1)
    b.inputs["Roughness"].default_value = 0.08
    b.inputs["Transmission Weight"].default_value = 0.85
    b.inputs["IOR"].default_value = 1.56
    co = _coord(nt, 1.0)
    thick = nt.nodes.new("ShaderNodeTexNoise")                 # membrane thickness wanders: 250-700 nm
    thick.inputs["Scale"].default_value = 3.0
    nt.links.new(co, thick.inputs["Vector"])
    tmr = nt.nodes.new("ShaderNodeMapRange")
    tmr.inputs["To Min"].default_value, tmr.inputs["To Max"].default_value = 250.0, 700.0
    nt.links.new(thick.outputs["Fac"], tmr.inputs["Value"])
    nt.links.new(tmr.outputs["Result"], b.inputs["Thin Film Thickness"])
    if not veins:                         # the model draws real veins as geometry
        b.inputs["Alpha"].default_value = 0.4
        try:
            m.surface_render_method = "BLENDED"
            m.use_backface_culling = False
        except Exception:
            pass
        m["look_v2"] = 1
        return m
    vein = nt.nodes.new("ShaderNodeTexVoronoi")                # veins: the edges between long cells
    vein.feature = "DISTANCE_TO_EDGE"
    vein.inputs["Scale"].default_value = vein_scale
    vm = nt.nodes.new("ShaderNodeMapping")
    vm.inputs["Scale"].default_value = (2.5, 0.6, 1.0)
    nt.links.new(co, vm.inputs["Vector"])
    nt.links.new(vm.outputs["Vector"], vein.inputs["Vector"])
    vr = nt.nodes.new("ShaderNodeMapRange")
    vr.inputs["From Max"].default_value = 0.04
    vr.inputs["To Min"].default_value, vr.inputs["To Max"].default_value = 0.95, 0.35   # vein = solid, cell = clear
    nt.links.new(vein.outputs["Distance"], vr.inputs["Value"])
    nt.links.new(vr.outputs["Result"], b.inputs["Alpha"])
    inv = nt.nodes.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    nt.links.new(vr.outputs["Result"], inv.inputs[1])
    tw = nt.nodes.new("ShaderNodeMath")
    tw.operation = "MULTIPLY"
    tw.inputs[1].default_value = 1.4
    nt.links.new(inv.outputs[0], tw.inputs[0])
    nt.links.new(tw.outputs[0], b.inputs["Transmission Weight"])
    try:
        m.surface_render_method = "BLENDED"
        m.use_backface_culling = False
    except Exception:
        pass
    m["look_v2"] = 1
    return m


def skin(name, tone=(0.62, 0.42, 0.33), unit_cm=1.0):
    """Human skin: real subsurface scattering (red travels furthest, ~1 mm), pores, fine creases, soft sheen."""
    m, b = _principled(name)
    if b is None:
        return m
    nt = m.node_tree
    b.inputs["Base Color"].default_value = (*tone, 1)
    b.inputs["Subsurface Weight"].default_value = 1.0
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.2)
    b.inputs["Subsurface Scale"].default_value = 0.12 * unit_cm          # ~1.2 mm in a 1-unit-per-cm scene
    b.inputs["Sheen Weight"].default_value = 0.3                        # fine hairs
    b.inputs["Coat Weight"].default_value = 0.12                        # skin oil
    b.inputs["Coat Roughness"].default_value = 0.35
    co = _coord(nt, 1.0 / unit_cm)
    pores = nt.nodes.new("ShaderNodeTexVoronoi")
    pores.inputs["Scale"].default_value = 25.0
    nt.links.new(co, pores.inputs["Vector"])
    crease = nt.nodes.new("ShaderNodeTexWave")
    crease.inputs["Scale"].default_value = 3.0
    crease.inputs["Distortion"].default_value = 9.0
    crease.inputs["Detail"].default_value = 3.0
    nt.links.new(co, crease.inputs["Vector"])
    mix = nt.nodes.new("ShaderNodeMath")
    mix.operation = "MULTIPLY_ADD"
    mix.inputs[1].default_value = 0.4
    nt.links.new(crease.outputs["Fac"], mix.inputs[0])
    nt.links.new(pores.outputs["Distance"], mix.inputs[2])
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.22
    bp.inputs["Distance"].default_value = 0.01 * unit_cm
    nt.links.new(mix.outputs[0], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    rn = nt.nodes.new("ShaderNodeTexNoise")
    rn.inputs["Scale"].default_value = 2.0
    nt.links.new(co, rn.inputs["Vector"])
    rr = nt.nodes.new("ShaderNodeMapRange")
    rr.inputs["To Min"].default_value, rr.inputs["To Max"].default_value = 0.38, 0.6
    nt.links.new(rn.outputs["Fac"], rr.inputs["Value"])
    nt.links.new(rr.outputs["Result"], b.inputs["Roughness"])
    m["look_v2"] = 1
    return m


def keratin(name, rgb=(0.09, 0.09, 0.1), striate=30.0):
    """Beak and claw: dense keratin with fine lengthwise growth lines, a little gloss."""
    m, b = _principled(name)
    if b is None:
        return m
    nt = m.node_tree
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = 0.32
    b.inputs["Coat Weight"].default_value = 0.35
    b.inputs["Subsurface Weight"].default_value = 0.15
    w = nt.nodes.new("ShaderNodeTexNoise")
    w.inputs["Scale"].default_value = striate
    w.inputs["Detail"].default_value = 6
    nt.links.new(_coord(nt, 1.0, (1, 0.06, 1)), w.inputs["Vector"])   # stretched along the beak's length
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.2
    nt.links.new(w.outputs["Fac"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    m["look_v2"] = 1
    return m


def bone(name, rgb=(0.86, 0.8, 0.68)):
    """Bone: ivory, porous, a little translucent at thin edges."""
    m, b = _principled(name)
    if b is None:
        return m
    nt = m.node_tree
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = 0.55
    b.inputs["Subsurface Weight"].default_value = 0.35
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.7, 0.45)
    b.inputs["Subsurface Scale"].default_value = 0.05
    v = nt.nodes.new("ShaderNodeTexVoronoi")
    v.inputs["Scale"].default_value = 40.0
    nt.links.new(_coord(nt, 1.0), v.inputs["Vector"])
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.18
    nt.links.new(v.outputs["Distance"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    m["look_v2"] = 1
    return m
