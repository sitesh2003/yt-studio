# The arsenal: one toolkit for accurate Shorts, long videos and the student channel (14 Nov 2026)

## Idea
Every scene asks "what is the most ACCURATE way to show this line?" and a router sends it to the
right engine. Computed pictures (maps, charts, Manim, molecules, orbits) come first because they
cannot be wrong; real footage and archive photos come next; drawings come last and only for single
objects. Every engine is free and open, runs on GitHub with the laptop off, and is checked.

## The scene router (shared by every format)
| The line is about... | Engine | Status |
|---|---|---|
| where something is | map from Natural Earth data | BUILT |
| a number, a trend, a comparison | animated chart from real data (Our World in Data, WHO, NASA, USGS) | to build |
| how something works, maths, forces, waves | Manim diagram, every step computed | to build (stage 1) |
| a molecule or substance | RDKit structure from PubChem | to build |
| planets, moons, orbits | Skyfield / JPL Horizons positions drawn true | to build |
| a real person or historical moment | archive photo (Commons, Smithsonian CC0, Library of Congress, NASA) | partly (Commons, NASA) |
| an animal, nature, an action | real footage (Pixabay, NASA, Commons video) | BUILT |
| a single object | checked drawing (FLUX.2 klein 4B, yes/no questions twice) | BUILT |
| body anatomy in 3D | Blender with the Z-Anatomy model | later (prototype) |

## Checks every video passes
| Check | How | Status |
|---|---|---|
| Facts | 2-round fact check and premise audit | BUILT |
| Sources | open papers kept only if their abstract supports the claim | BUILT |
| Pictures | vision check of each scene; yes/no questions for drawings | BUILT |
| Voice | faster-whisper transcribes the finished voice and compares it with the script (skipped or misread words) | to build |
| Sync | word timings drive captions and cuts; WhisperX can prove alignment | partly |
| Freeze, black, length | ffmpeg checks | BUILT |

## Long videos (8-12 min, 16:9): how they become "proper"
1. **One question per episode**, researched first: 5-10 open papers and official sources gathered BEFORE writing (not after), so the script is built on what the sources say.
2. **Chapters of 60-120 s.** Each chapter has its own mini-mystery, a reveal, and "how we know" (the paper or the experiment, named on screen).
3. **Mixed visuals through the router.** A long video needs variety to hold attention; the router gives a map, then a chart, then footage, then a Manim diagram, all accurate.
4. **On-screen source cards:** a small "Source: Author et al., year" card when a key fact is shown; full list in the description.
5. **Pacing:** a visual change every 4-8 s, chapter titles, a recap at the end, and the "Ever thought why" question for the comments.
6. **Checks per chapter,** so one weak chapter is repaired without losing the whole episode.
7. **Cadence:** 1 a week until 3 episodes hold viewers 3+ minutes, then 2 (section 9: Mayank's long videos flopped; ours must earn the second slot).

## Build order
1. **Manim engine:** sample renders on GitHub, timing measured; then the router sends "how it works" lines to it. Serves the main Shorts, long videos and the student channel.
2. **faster-whisper voice check.**
3. **Chart engine** (real datasets) and **archive photos** (Smithsonian CC0, Library of Congress) for True Science Stories.
4. **Long-video rebuild:** research-first script, chapters, router visuals, source cards, chapter checks.
5. **Molecules, space,** then the **Blender** anatomy prototype.
6. **Student channel,** once the user creates it: Manim-first, same checks.
