# The 3D plan: great 3D, made to be shared (24 Nov 2026)

Owner: "the channel should be very great — great 3D modelling, great 3D animation, and people should share it,
so cool that they love to share it." Everything is made on the laptop (RTX 4050 6 GB, 16 GB RAM).

## 1. Two looks, both procedural in Blender (no AI video, no reused footage)
| Look | For | What makes it pro |
|---|---|---|
| **Micro world** (tools/blender/lookdev/micro_world.py) | body, cells, molecules, germs | glowing organic proteins (subsurface + noise emission), real structures (13-protofilament microtubule…), bokeh particles, f/0.35 depth of field, bloom, Cycles OptiX |
| **Big world** (tools/blender/hero/shots.py) | dinosaurs, physics, cars | stylised low-poly world, film lighting, x-ray views, sims; upgrade with depth of field, bloom, rim light |

Bar: the reference Shorts in the EVER THOUGHT WHY playlist (newest: the kinesin video). A look is "ready" only
when a contact sheet of ours, side by side with the reference, does not lose (see show-only-finished-quality).

## 2. Every video is built to be passed on
- `share` block in every script (myth, truth, one line ≤ 22 words), gated by `hero_gate.py <name> script`.
- Open on what everyone believes, hand over the PROOF (a number, a model, a fossil), say the line plainly.
- A human-scale comparison in each video (the reference's best trick): "if this protein were your size, it
  would be running at X km/h", "this much DNA would reach the Moon". Numbers checked against sources.
- One closing question. Never beg for likes or shares. The viewer is made clever, nobody is made small.

## 3. Cadence the laptop can carry
- A Short: ~1–1.5 h film-quality render, shared by English and Hindi (render once, two voices).
- Target: 1 new 3D Short a day on main + its Hindi version; Why It Works weekly; a long film every 2 weeks
  (~15 h render, run overnight).
- Renders resume after a crash; count frames per shot before every cut. After upload, frames are packed
  into per-shot mp4s (tools: archive_frames) so the disk never fills (it was at 12.7 GB free on 24 Nov).

## 4. All local
- English voice: Chatterbox on the laptop GPU (.venv-voice), Hindi: Edge Swara. GitHub only answers comments
  and saves stats.

## 5. First Micro-world series (each fact checked before scripting)
1. ATP synthase — the spinning motor that makes your energy.
2. A red blood cell's trip round the body.
3. How fast a nerve signal really travels.
4. A white blood cell chasing a bacterium.
5. How 2 m of DNA fits in every cell.

## 6. Judge by shares
`channel_stats()` → `shares_per_1k`. Each week: which topics people passed on; make more of those.
