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
