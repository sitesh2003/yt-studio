"""Render once, publish many (27 Nov 2026).
    python tools/blender/hero/reuse_shots.py <name> <src_name>
Every shot in research/hero/<name>/spec.json that carries "src" (its index in <src_name>) is hardlinked from
renders/<src_name>/s<src>.mp4 to renders/<name>/s<k>.mp4 when that clip is long enough (compose holds up to
15 frames). Shots whose new narration outruns the old clip are printed as RENDER k, to be rendered fresh.
"""
import json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
name, src_name = sys.argv[1], sys.argv[2]
R = ROOT.parent / "yt-studio-assets" / "renders"
spec = json.loads((ROOT / "research" / "hero" / name / "spec.json").read_text(encoding="utf-8"))
out = R / name
out.mkdir(parents=True, exist_ok=True)


def frames(p):
    if p.is_dir():
        return len(list(p.glob("*.png")))
    if p.exists():
        r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=nb_frames",
                            "-of", "csv=p=0", str(p)], capture_output=True, text=True)
        return int(r.stdout.strip() or 0)
    return 0


todo, linked = [], 0
for k, sh in enumerate(spec["shots"]):
    n = int(round(sh.get("render_seconds", sh["seconds"]) * 30))
    dst = out / f"s{k}.mp4"
    if (out / f"s{k}").is_dir() and frames(out / f"s{k}") >= n:
        continue
    if "src" not in sh:
        todo.append(k); continue
    clip = R / src_name / f"s{sh['src']}.mp4"
    m = frames(clip)
    if m + 15 >= n:
        if dst.exists() and frames(dst) != m:
            dst.unlink()
        if not dst.exists():
            os.link(clip, dst)
        linked += 1
    else:
        if dst.exists():
            dst.unlink()
        todo.append(k)
        print(f"RENDER {k} (src {sh['src']}: {m} frames, needs {n})")
print(f"linked {linked}, to render {len(todo)}")
(out / "_render_list.txt").write_text(" ".join(map(str, todo)), encoding="utf-8")
