"""How fast can a machine render a 3D Short frame? (19 Nov 2026)
    blender -b --factory-startup --python tools/blender/speed_test.py -- ENGINE [PERCENT]
ENGINE: EEVEE | WORKBENCH | CYCLES. PERCENT: resolution percentage of 1080x1920 (default 100).
Prints one RESULT line. Used on the laptop (RTX 4050: EEVEE 0.65 s a frame) and on GitHub's free machines."""
import bpy, time, math, sys, os, tempfile
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
eng = args[0] if args else "EEVEE"
pct = int(args[1]) if len(args) > 1 else 100
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = {"EEVEE": "BLENDER_EEVEE", "WORKBENCH": "BLENDER_WORKBENCH"}.get(eng, "CYCLES")
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, pct
sc.render.image_settings.file_format = "PNG"
if eng == "CYCLES":
    sc.cycles.device = "CPU"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for t in ("OPTIX", "CUDA"):
        try:
            prefs.compute_device_type = t
            prefs.get_devices()
            if any(d.type == t for d in prefs.devices):
                for d in prefs.devices:
                    d.use = True
                sc.cycles.device = "GPU"
                break
        except Exception:
            pass
    sc.cycles.samples = 32
    sc.cycles.use_denoising = True
# a room, a character (capsule body + sphere head), 40 props, sun + area light
bpy.ops.mesh.primitive_plane_add(size=20)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 6, 3)); bpy.context.object.scale = (10, 0.2, 6)
for i in range(40):
    bpy.ops.mesh.primitive_cube_add(size=0.5, location=(math.sin(i) * 4, math.cos(i * 1.3) * 3, 0.25))
bpy.ops.mesh.primitive_cylinder_add(radius=0.35, depth=1.2, location=(0, 0, 0.9))
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.45, location=(0, 0, 1.9), segments=48, ring_count=24)
bpy.ops.object.light_add(type="SUN", location=(3, -3, 8)); bpy.context.object.data.energy = 3
bpy.ops.object.light_add(type="AREA", location=(-2, -3, 4)); bpy.context.object.data.energy = 400
bpy.ops.object.camera_add(location=(0, -7, 2.2), rotation=(math.radians(85), 0, 0)); sc.camera = bpy.context.object
out = tempfile.gettempdir()
times = []
for f in range(6):
    sc.camera.location.x = f * 0.1
    sc.render.filepath = os.path.join(out, f"bl_{eng}_{pct}_{f}.png")
    t = time.time(); bpy.ops.render.render(write_still=True); times.append(time.time() - t)
dev = sc.cycles.device if eng == "CYCLES" else "-"
print("RESULT %s %d%% device=%s: first %.2fs, then %.2fs a frame" % (eng, pct, dev, times[0], sum(times[1:]) / 5))
