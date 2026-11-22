# Hero 3D Shorts: lessons (read before every video, add after every video)

Owner, 21 Nov 2026: "train yourself better and better every video… exceptional, not only good."
Every lesson here came from a real mistake. The fix is in the code; the check is in `tools/hero_gate.py`.

## The routine (every video, every laptop session)
1. **Facts first** – every claim from a published source, in `script.json` → `facts` and `sources`. Model estimates say "may have" / "about".
2. **Script as a story** – a "you" problem → fix chain or one surprising true statement as the hook; one closing question, nothing after it.
3. **Narrate** (main/wiw: GitHub E2; hi: laptop Swara) → `hero_slow.py` to the speed band → `hero_gate.py <name> voice` must PASS.
4. **Timings** (`timings.py`) → render → compose → `hero_gate.py <name> video` must PASS.
5. **Look at it**: a contact sheet at every cut + mid-shot. Check: subject in frame from the first frame, nothing off-screen, nothing on the captions, the picture matches the words.
6. Only then `hero_publish.py` (private, scheduled, one a day per channel).
7. Add any new problem below.

## Voice and pronunciation
- "T. rex" was read as "T." + pause + "rex" → `voice.clean` turns a lone capital + full stop into "T-rex".
- Numbers: the listener writes "40%" and "8"; it used to count them as dropped words and fell back to the female voice → digits count as words. **In scripts, write tricky numbers as words** ("thirty-four thousand five hundred").
- Hindi years: check by sound (उनसठ = 59, उनहत्तर = 69) – a big model "corrected" 1959 to 1969.
- Hindi English loanwords in Latin letters are heard back in Devanagari → the gate compares Hindi **by sound** (`listen.skeleton`).
- The big listener invents English translations of Hinglish unless `condition_on_previous_text=False`.
- Prefer plain Hindi in the opening line ("बारिश", "गाड़ियां"): "Monsoon … cars" opening came out garbled.
- Speed bands: English 170–200 wpm, Hindi 160–195. Raw E2 runs 207–249 → always slow with `hero_slow.py` (0.80–0.88).

## Captions
- Doubling = YouTube showing an uploaded caption track over the burned-in captions → no caption track on any channel.
- Keep the channel's own phrase lines and wording; only size changed (80%). Never re-chunk into 2-word cards.
- Graphics stay above y = 800 of 1920; labels shrink to fit the width.

## Cuts and timing
- Word-counting placed cuts up to 0.9 s late (worst in Hindi) → cuts on each scene's **first three spoken words**. Gate: every cut within 0.25 s.
- Never use "does the file exist" to wait for a render if an old copy of that file can exist (an old mp4 started a job early).

## 3D
- Quaternius FBX actions key the object (×3 scale) → strip object channels; FBX skins import with alpha 0.
- Running shots: the camera follows at a distance that suits the animal's size (`cam_dist`) – a fixed camera opened on empty road.
- Small animals need a known object beside them (the baby next to a car wheel), filmed from adult eye height.
- Teeth / offset pieces: turn first, then place (rotating after placing swung the teeth off the jaw).
- A crash only reads from above (the folding car visibly shortens).
- Hooks must show the action on frame 1 (cars already in view, the animal already big).
- Film look (Cycles) for day/dusk shots: 40 denoised samples, no motion blur (≈2× faster), real-sky HDRI.

## Records and uploads
- The bot's daily save rewrote whole history files and dropped laptop-made entries → `json_guard` restores entries the remote has.
- Replace a scheduled video by unscheduling the old one (stays private) and uploading the new one in the same slot; delete old copies only when the owner says so.
- Never push a workflow without validating its YAML first.

## 22 Nov 2026
- **Hindi = Devanagari.** Daily Hindi scripts came out as Hindi in English letters or whole English sentences (the voice reads Latin letters with an English accent) → `writer.hindi_script_issues` sends them back; English only as single words, at most 3 in a row.
- **On-screen labels are language too.** Hindi videos had English phrase labels ("water gets between tyre and road") → `compose.HI_LABELS`: every label in Hindi, drawn by libass in the Hindi font (PIL cannot shape Devanagari).
- The cut matcher must read the script the way the voice read it (`voice.clean`: "T. rex" → "T-rex"), or it silently falls back to word counting.
- Two captions overlapped for 0.06 s → `_no_overlap` ends each caption at the next one's start.
- Gate false alarms are bugs too: British/American spelling, "onto"/"on to", digits vs number words, Latin vs Devanagari spelling of the same English word (compare Hindi by sound).
- Patches written through the shell turned `\n` and `\b` into real control characters twice → write patch scripts to files; parse-check (`ast.parse`) after every code patch.
- Hook shots: a big face on frame 1 beats a wide shot with a small animal at the edge.
- Gates passing is not the video being right: a roaring body sweeping through a close camera made a skeleton jumble, and an x-ray shot opened on a dark skin blob. Only looking at frames catches these → the frame check is compulsory; close x-ray shots use the idle action and start already in x-ray (`xr_start`).
- Toon look (HERO_QUALITY=toon): ~1 s a frame vs ~4–5 s film; outline width must be set in metres (divide by the object's scale) or it vanishes; lift and saturate the model's linear colours or everything turns grey.

## 22 Nov 2026 (evening): council rounds 5–6 and the Apatosaurus tail
- **Hide, don't delete.** Both advisors: deleting low performers does not help the algorithm and loses watch time. Rule:
  under 150 views AND under 40% viewed after a week, or wrong language → PRIVATE. 2D bot off everywhere (publish.make_2d).
- **Make the picture match the number.** The tail_whip template measures the tail tip's speed in the scene frame by
  frame and tunes the swing until it equals the paper's figure (32.7 m/s, Conti et al. 2022). A 71° swing does it.
- **Fact-checking finds better stories.** "Supersonic tail" (1997) vs "33 m/s, a car on the highway" (2022) is a
  myth-vs-model story with a built-in everyday comparison. Always read the newest paper before scripting the famous claim.
- **Latin names in Hindi narration:** Swara reads "Apatosaurus" as "aparosorus". Write the SPOKEN form in Devanagari,
  tested by listening (अपैटोसॉरस comes back as "apatosaurus"); captions show what is spoken. Keep the Latin in the title.
- The small Hindi listener's "phrase missing" was false again; the medium model (CPU int8 works when CUDA libs are
  missing) heard every word. Always confirm with the medium model before re-voicing.
- T. rex skeleton parts (hip plates, skull) do not fit other animals: per-shot bone_groups keep only TAIL + SPINE.
- **A vertical frame is narrow:** a 62 m see-saw became a thin strip. Shrink the set (equal arms, short car platform,
  cars stacked as a tower so the count reads as layers), then mix close-ups of each end with the wide levelling shot.
- **Units are part of accuracy:** US viewers hear "tonnes" as "tons" (short tons, 0.907 t). English = pounds/mph,
  Hindi = टन/km/h, with separate specs so the on-screen numbers match what is said.
- Held the first Hindi weight render (subject too small, frame 1 no payoff) and re-rendered; never upload "good enough".

## 23 Nov 2026: the first long films
- **A book, not stitched Shorts** (owner): one story spine, chapter cards, varied chapter lengths, a question carried
  through, the climax longest. Council rounds 7-8 shaped both films; ChatGPT's suggested ending ("its descendants")
  was itself wrong and was rejected; Gemini caught a real maths slip (30 vs 33.2 km/h). Ask, but check the answers.
- **Long-film timing traps:** (1) the voice timeline summed MP3-header durations: a few hundredths per clip drifted a
  7-minute film by 4-6 s; now each clip's decoded samples are counted (voice._exact_dur). (2) scenes.json from
  counting words drifts when the voice service splits words differently (numbers, Latin); timings.py's first-three-
  words match is the truth, so run it BEFORE the gate. (3) one whisper pass over a long file drops 30 s chunks; the
  gate now hears each scene on its own slice.
- **One render, two languages:** render each shot ~15% longer than the longer language needs; compose takes the first
  frames each language needs (frames dir is an argument). Saves ~8 h per film.
- **Landscape without redesign:** graphics drawn on the tall canvas, scaled into a left side panel; chapter cards and
  source lines drawn by libass in the channel font (Hindi shapes correctly); logo top right; output 2560x1440.
- **The picture must show the claim:** a "43 km/h with reaction time" line needs a scene that models reaction time
  (brake_compare react_s), not the same-instant scene with a different label.
- Spot-render one frame of every NEW shot before an 8-hour render (Sue's skull was far away and not yet in x-ray).
