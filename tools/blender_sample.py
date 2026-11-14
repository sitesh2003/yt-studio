"""Blender test (14 Nov 2026): can GitHub's machines (no graphics card) render a 3D shot fast enough?
Run: blender -b -P tools/blender_sample.py -- <engine> <out_dir>
Builds a simple lit scene (a smooth planet with a ring and a moon) with an orbiting camera, renders
30 frames at 1080x1920 and writes frame timing to <out_dir>/<engine>.json."""
import json, math, os, sys, time

import bpy

engine, out = sys.argv[sys.argv.index("--") + 1:][:2]
os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, 100
sc.frame_start, sc.frame_end = 1, 30
sc.render.engine = {"eevee": "BLENDER_EEVEE", "workbench": "BLENDER_WORKBENCH", "cycles": "CYCLES"}[engine]
if engine == "cycles":
    sc.cycles.samples = 16
    sc.cycles.device = "CPU"
    try:
        sc.cycles.use_denoising = True
    except Exception:
        pass


def mat(name, rgb, rough=0.6):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    m.diffuse_color = (*rgb, 1)
    return m


bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, radius=1.6)
planet = bpy.context.object
bpy.ops.object.shade_smooth()
planet.data.materials.append(mat("planet", (0.85, 0.55, 0.25)))
bpy.ops.mesh.primitive_torus_add(major_radius=2.6, minor_radius=0.08)
ring = bpy.context.object
ring.rotation_euler = (math.radians(70), 0, math.radians(15))
ring.data.materials.append(mat("ring", (0.9, 0.85, 0.7)))
bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=0.35, location=(3.4, -1.0, 1.2))
bpy.ops.object.shade_smooth()
bpy.context.object.data.materials.append(mat("moon", (0.7, 0.7, 0.75)))
bpy.ops.object.light_add(type="SUN", location=(5, -5, 6))
bpy.context.object.data.energy = 4
world = bpy.data.worlds.new("w")
sc.world = world
world.color = (0.01, 0.015, 0.04)
bpy.ops.object.camera_add()
cam = bpy.context.object
sc.camera = cam
cam.data.lens = 35
for f in range(1, 31):                              # camera orbits a quarter turn
    a = math.radians(-30 + 3 * f)
    cam.location = (9 * math.sin(a), -9 * math.cos(a), 2.5)
    d = -cam.location.normalized() if hasattr(cam.location, "normalized") else None
    cam.rotation_euler = (math.radians(78), 0, a)
    cam.keyframe_insert("location", frame=f)
    cam.keyframe_insert("rotation_euler", frame=f)
sc.render.image_settings.file_format = "PNG"
sc.render.filepath = os.path.join(out, f"{engine}_####")
t = time.time()
bpy.ops.render.render(animation=True)
sec = time.time() - t
json.dump({"engine": engine, "frames": 30, "seconds": round(sec, 1), "per_frame": round(sec / 30, 2),
           "blender": bpy.app.version_string}, open(os.path.join(out, f"{engine}.json"), "w"))
print(f"{engine}: {sec:.1f}s for 30 frames ({sec / 30:.2f}s per frame)")
