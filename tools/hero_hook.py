"""Cold-open hook for an already-made Short (council 28 Nov 2026: frame 1 = the strongest frame, already moving).

    python tools/hero_hook.py <name> <hook_shot> [variants...]

Shot 0 of <name> (and <name>_hi, plus any extra variants that share the render, e.g. popcorn_wiw) becomes a copy
of shot <hook_shot>, the Short's most striking moment, at shot 0's own length, label and timing; the narration
is untouched (use this only when the first spoken line already breaks the myth in a few words).
Writes the new specs (old ones kept as spec_prehook.json) and renders/<name>_hook/ with s1..sN hardlinked from
renders/<name>/ and the list file for the one shot to render:
    bash tools/blender/hero/render_list.sh <name>_hook micro.py   (spec: research/hero/<name>_hook/spec.json)
then compose each variant against renders/<name>_hook.
"""
import copy, json, os, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
H = ROOT / "research" / "hero"
R = ROOT.parent / "yt-studio-assets" / "renders"
name, k = sys.argv[1], int(sys.argv[2])
variants = [name, name + "_hi"] + sys.argv[3:]

for v in variants:
    p = H / v / "spec.json"
    if not p.exists():
        continue
    spec = json.loads(p.read_text(encoding="utf-8"))
    bak = H / v / "spec_prehook.json"
    if not bak.exists():
        shutil.copy(p, bak)
    spec = json.loads(bak.read_text(encoding="utf-8"))
    s0, hook = spec["shots"][0], copy.deepcopy(spec["shots"][k])
    for key in ("seconds", "render_seconds", "event_seconds", "overlay", "label", "source"):
        if key in s0:
            hook[key] = s0[key]
        else:
            hook.pop(key, None)
    hook["hook_of"] = k
    spec["shots"][0] = hook
    p.write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{v}: shot 0 is now a cold open of shot {k} ({hook['kind']})")

# the render: shot 0 fresh, the rest reused
en = json.loads((H / name / "spec.json").read_text(encoding="utf-8"))
(H / f"{name}_hook").mkdir(exist_ok=True)
(H / f"{name}_hook" / "spec.json").write_text(json.dumps(en, indent=2, ensure_ascii=False), encoding="utf-8")
out = R / f"{name}_hook"
out.mkdir(exist_ok=True)
for i in range(1, len(en["shots"])):
    src, dst = R / name / f"s{i}.mp4", out / f"s{i}.mp4"
    if not dst.exists():
        os.link(src, dst)
(out / "_render_list.txt").write_text("0", encoding="utf-8")
print("render list: shot 0 ->", out)
