# Growth and monetisation strategy, 13 Nov 2026

## How this was studied
- **YouTube Data API scan:** the top 50 videos of the last 120 days in each of 20 niches, 1,000 videos in all. For every channel behind them: creation date, subscribers, total views and number of uploads.
- **Deep dive:** the last 50 uploads of 14 channels less than 13 months old. Measured: posting rate, length, the spread of views, and the titles of the hits and the flops.
- **Visual check:** YouTube's own preview frames, taken at ¼, ½ and ¾ of each video, for six of those channels.
- **Our own analytics:** the last 28 days.
- **Web research:** RPM by niche and country, the Partner Program (YPP) rules for 2027, the inauthentic-content policy, income outside YouTube, and free image and map sources. The key claims were checked on YouTube's own pages.

## 1. Where we stand
- **Size:** 6 public Shorts in 3 days, about 4,800 views and 3 subscribers.
- **Traffic:** 95% of views come from the Shorts feed; 53% of viewers are in the US.
- **The real problem is retention.** On average, viewers saw 53% (eyes) and 36% (onion) of each video. YouTube widens distribution only when people watch to the end.
- **Watch hours read 0 for a structural reason:** Shorts views never count toward watch hours.

## 2. The rules we have to play by (official)
- **Until 31 Jan 2027:** 1,000 subscribers, plus either 4,000 long-form watch hours in 12 months or 10M Shorts views in 90 days.
- **From 01 Feb 2027:**
  - **New channels** need 8,000 watch hours or 20M Shorts views.
  - **Channels already in YPP** earn from Shorts only while they have 10M Shorts views in the last 90 days. Long-form earnings are not affected.
  - Sources: [YouTube blog](https://blog.youtube/news-and-events/youtube-partner-program-updates-2027-new-opportunities-earn/), [Help 72851](https://support.google.com/youtube/answer/72851).
- **Copyright claims on longer Shorts:** a Short over 1 minute with any active Content ID claim is blocked worldwide ([Help 15424877](https://support.google.com/youtube/answer/15424877)). Stock footage gets wrongful claims, so we stay at 60 seconds or less.
- **The inauthentic-content policy** (July 2025) is fatal to channels that are mass-produced, templated or slideshow-like. In Jan 2026, about 16 AI-slop channels were wiped. Each of our videos needs a distinct idea, a real narrative and visible variety.

## 3. What the winners do differently

| What | Winners | Us now |
|---|---|---|
| Visuals | One illustrated or animated scene per line, filling the whole screen: stylised 3D (The Why Side, Infinite Desk), flat 2D (MapLore), maps (World Ji Ke) | Stock clips; landscape ones boxed over a blur (**fixed 13 Nov, cb0e1e2**) |
| Topic | Hidden engineering of everyday objects, danger scenarios, how machines work, the evolution of inventions | Food and body trivia |
| Title | 4–8 words, concrete, one object or moment, usually no emojis | Fact titles with 2 emojis |
| Hook | Puts the viewer in a situation | States a fact or question |
| Posting rate | 2–6 a week, each a strong idea. Infinite Desk: about 2 a week and 1.25M median views. Zero Theory: about 1 a day and 19k median. | 3 a day |
| Length | 30–45 s gets the most views; 60–90 s gets twice the likes per view | 40–54 s |
| Countdown | None of them uses one | "Pause and guess" in every video |
| Languages | Infinite Desk runs a dubbed Spanish twin (194k subscribers) | English only |

Hits are lopsided. The Why Side's median video gets 103k views, but its best got 16M. Each video is a lottery ticket, and quality raises the odds.

## 4. Money
- **Long-form RPM, Education & Science:** $10.22 median, the highest of 13 niches ([AIR, Oct 2026](https://air.io/en/air-data-findings/youtube-monetization-statistics-2026)).
- **Shorts RPM:** $0.02–1.48, about 3–14% of long-form.
- **By country:** US CPM about $14.67 against India about $0.74. Spanish and German pay more than Hindi.
- **Conclusion:** Shorts bring reach, and long-form brings watch hours and money.

## 5. Plan (status updated 13 Nov 2026, evening: the user said yes to every step)
1. **Done (13 Nov):**
   - full-screen crop around the subject
   - real NASA and Commons footage
   - research lessons in every script (data/research.json)
   - premise audit and script lint
   - a voice swap that actually swaps
   - board drift
2. **Illustrated scenes: BUILT (agents/illustrate.py), switches on with the keys.** Model: FLUX.2 [klein] 4B, Apache 2.0, at 864x1536 (about 140 neurons each, so about 60 a day free; 25 at most for the weekly video). Still needed from the user: create a free Cloudflare account and save its account ID and API token as GitHub secrets (CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_API_TOKEN). The free tier makes about 100–230 FLUX schnell images a day, and FLUX schnell is Apache 2.0. Every scene would be drawn in one consistent stylised style, never photo-real, and the picture judge would check each image for accuracy.
3. **A weekly long-form video: already built (studio.py weekly, Saturdays 10 AM ET); first run 14 Nov 2026.** (8–10 min, 16:9) on the same researched topics. This builds watch hours toward YPP and earns the high long-form RPM.
4. **Fewer, better Shorts: DONE.** 2 a day (12:00 and 19:00 ET) from 13 Nov. Titles now 4–8 concrete words ending in ONE face emoji (Zack D. Films, below); topics widened to hidden engineering and how machines work (new series "How Things Work").
5. **Countdown experiment: RUNNING.** Half the Shorts keep "Pause and guess... 3-2-1", half ask the question plainly. analyst.experiment() names the winner automatically (data/experiments.json); the daily report shows the score.
6. **Second channel, geography and maps: the map engine is BUILT (agents/maps.py) and already used in the main channel for "where on Earth" lines.** The channel itself needs the user to create it (a Brand Account channel) and sign it in. Background: Natural Earth data is public domain, so maps drawn by code are 100% accurate. The niche's median is 3.6M views, and World Ji Ke has 88k subscribers after 6 months.
7. **Spanish: titles and teasers are now translated on every upload (es, pt, de, fr, hi).** The user should also turn on YouTube auto-dubbing (27 languages, a Studio setting), or later a dubbed Spanish twin channel using Kokoro's Spanish voices.
8. **Off-YouTube income:** free PDF diagram packs; sponsors such as Brilliant or CuriosityStream after about 10k subscribers. Facebook and Snapchat payouts in India are invite-only or unclear, and TikTok is banned in India.

## 6. What we will not do
- re-cut TV, film or game footage (Explain Station, The Ranking Dude)
- photo-real AI imagery
- several near-identical channels
- automated comments on other channels
- kids content (lowest RPM, and the main crackdown target)

## 7. What only the user can do (accounts and settings)
1. **Cloudflare (for illustrations), about 5 minutes:**
   - Sign up free at dash.cloudflare.com.
   - Copy the Account ID (shown on the Workers AI page).
   - Create an API token with the "Workers AI" template (read and edit).
   - In GitHub, go to sitesh2003/yt-studio → Settings → Secrets and variables → Actions → New repository secret, and add CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN.
   - The next production run uses them by itself.
2. **Auto-dubbing:** in YouTube Studio, go to Settings → Upload defaults → Advanced settings and make sure automatic dubbing is allowed.
3. **Geography channel (when ready):** create a second channel on the same Google account (a Brand Account). The code side then needs its own sign-in token secret.

## 8. Zack D. Films check (13 Nov 2026, the user's request)
YouTube Data API. Last 100 uploads, 23 Oct - 13 Nov 2026, plus preview frames of the top 4.
- **Size:** created 07 Jun 2021; 29.7M subscribers, 83 billion views, 4,215 videos.
- **Posting rate:** about 5 uploads a day.
- **Views:** median 8.6M per video; lowest 250k (a video a few hours old); top 50.2M ("Why Dobermans Have Cropped Ears").
- **Length:** median 35 s (21-89 s); hits and flops are the same length.
- **Titles:** median 7 plain words, and EVERY title ends with ONE face emoji that shows the feeling (worried, thinking, surprised). No hashtags, few question marks.
- **Formats:**
  - why or how about animals and the body ("How Horseflies Bite You")
  - "What If" worked out with real numbers ("What If Humans Had Hummingbird Hearts")
  - practical "How To" ("How To Find Tiny Things You Dropped")
  - short dramatised stories, labelled "(fiction)" when made up
- **Visuals:** every line is its own custom 3D-animated shot that shows the words literally:
  - x-ray cutaways (a heart inside the chest, veins inside a leg)
  - extreme close-ups (a horsefly's mouthparts on skin)
  - 3D people reacting
  - small white captions near the middle
- **Production:** a large studio. A secondary source says 50+ staff, about 30 of them 3D animators (unverified). Tutorials copying the look use Character Creator / iClone / Blender and AI voices.

**What we take:**
- one face emoji at the end of every title
- "What If" and "How it gets you" formats, both worked out with real science
- 30-45 s, one literal picture per line

**What we cannot copy for free:** custom 3D animation of every line. Our nearest honest equivalents are real footage, exact maps and checked drawings.

## 9. Meanwhile Mayank check (13 Nov 2026, the user's request)
YouTube Data API, all 27 uploads, plus preview frames of the top 3 and "How We Are Still Alive?".
- **Growth:** created 16 Oct 2026, and under 4 weeks later has 65.4K subscribers and 22M views from 27 videos. The fastest start in all our research.
- **Shorts vs long videos:** median Short 292K views; top 5.8M ("Saap Katne Par Ye Sab Kyon?"). Its 3 long videos (7-9 min) flopped, with 3K-14K views each.
- **Length:** Shorts run 2-3 minutes (median 147 s). They are long because each one tells a documentary-style story.
- **Language:** Hinglish narration and titles; a question title plus 😳 plus a block of hashtags (#shorts #facts #documentary #science).
- **Topics:** health fears and myths people face, told as "what really happens in your body":
  - snake bite, tetanus, rabies, HIV, radiation
  - TB, dengue, AQI and pollution
  - comment counts are high (922 on the AQI video)
- **"How We Are Still Alive?" (677K views, 922 comments):**
  - **The question:** if AQI 300 is deadly, how is Delhi alive at 1,000+?
  - **The answer:** dose. A whole severe day's PM2.5 is about 4-6 mg, lighter than a grain of rice, and AQI is a warning, not a death meter.
  - **Why it works:** one surprising number that settles a fear everyone shares.
- **Visuals:** one dramatic, museum-like still per line, with a slow move. Examples:
  - anatomical models (lungs, a skull on a stand, a heart)
  - a "WANTED" poster for a virus
  - a polaroid evidence board
  - an Indian street scene

  Each scene carries a bold 2-4 word HEADLINE top-left, the key word in an accent colour (e.g. "FIRST / LOCKJAW"), instead of word-by-word captions.

**What we can take:**
- **Stakes topics:** fears and myths about the body and dangers, answered with one surprising true number. For US viewers, for example:
  - the rusty-nail tetanus myth
  - rattlesnake-bite myths
  - bats and rabies
  - carbon monoxide
  - ticks

  Facts only from CDC, WHO or NIH-level sources; never treatment advice beyond "get medical help now".
- **Scene headlines:** a big keyword headline per scene, the museum-object look (objects, not mechanisms: exactly what our drawings and a Blender anatomy model can do).
- **Longer Shorts for story topics (90-150 s):** only with visuals that cannot draw a copyright claim, because a Short over 1 minute with any claim is blocked worldwide.
- **A Hinglish twin channel:**
  - **For:** Kokoro has Hindi voices, and this channel shows the market moves fast.
  - **Against:** India pays roughly 1/20 of US rates per view.
- **Long videos:** his flopped too. This confirms one a week for us, not two.

## 10. The user's "EVER THOUGHT WHY" playlist, 4 new Shorts (14 Nov 2026)
| Short | Views (by 14 Nov) | Channel | What it is |
|---|---|---|---|
| Jensen Huang's Affair Rocks NVIDIA | 849K in 1 day | Afterhour Theory (7 videos, 12.7K subs) | simple 3D stick-figure cartoon telling a real person's life story |
| Electronegativity in 60 Seconds (ICSE Class 10) | 386 | Score With Science | clean animated textbook infographic |
| Linked List Explained in 60 Seconds | 205 | the_web_brain | neon coding animation, clickbait thumbnail |
| Theoretical Yield (Hinglish, Ch-28) | 154 | Zovik: Chem | beautiful 3D molecule renders |

**Lessons:**
1. **Polished visuals do not bring reach on their own.** Zovik's 3D renders are excellent and got 154 views. The textbook and syllabus topics (ICSE, DSA, chapter numbers) are search content for students, not feed content.
2. **The feed rewards a story or a surprise with stakes.** A stick-figure cartoon got 849K because it is a human story.
3. **Our format matches the winners:** a curiosity contrast (Explain Station's tuna Short, 8.9M) or a story, never a lesson.

**What we take:** a "TRUE SCIENCE STORY" format (real, documented discoveries and people).

**What we will not do:** gossip or scandal about real living people. We could not verify that story, and it is a defamation and misinformation risk.

## 11. A student channel: research (14 Nov 2026)
**Method:**
- YouTube Data API: the top 50 videos of the last 120 days in each of 16 student niches (771 videos, 418 channels).
- A deep pass on the last 50 uploads of 9 young channels.
- Frames from the 3 strongest.

**Median views of the top videos by niche:**
- maths tricks 2.76M (54% are Shorts)
- history explained 2.23M
- class 10 science 737K and class 12 physics 722K (mostly multi-hour Indian coaching lectures)
- biology concept 602K (58% are Shorts)
- JEE physics 587K
- physics concept 155K
- chemistry 114K
- AP US 18K
- coding concept 108 (dead as Shorts)

**What wins and what does not:**
- **Coaching (PW, Vedantu, Prashant Kirad):** huge, but built on teachers' faces and multi-hour lectures. Not automatable.
- **Textbook "concept" Shorts are weak:**
  - Career Guide With PREM, "Force vs Pressure, Class 10": median 8K
  - Zovik, Score With Science: about 200 views
- **Mass AI-3D anatomy channels are weak:** AiEngineer median 8.7K, Nature Discovery 3.2K, daudvoice 1.7K.
- **The winners frame a concept as curiosity:**
  - Siddharth Choudhary, physics mind-benders: median 534K, 566K subs in 6 months, but face-driven.
  - eSaral Science, Hindi 3D medical: median 56K, top 15.7M ("Kidney transplant mein purani kidney ka kya karte hain?").
  - 3D Eye, engineering 3D: median 206K, top 41.7M.
  - Myst Editz, maths tricks: 15-24 s, about 5 a day, median 143K, 231K subs in 11 months. Its visuals reuse someone's footage, and its tricks are often presented without the "why".

**Conclusion:** the student channel that can be automated AND accurate is visual maths and concepts drawn by code.
- **Tool:** Manim Community Edition (MIT licence, the engine behind 3Blue1Brown's style), which renders every step from code, so every number is computed and always right.
- **Format, 20-45 s:**
  1. the trick or surprising fact
  2. one worked example drawn step by step
  3. WHY it works in one visual line of school maths
  4. a "try this one" question for the comments
- **Topics:**
  - mental maths methods
  - visual proofs (Pythagoras, why the area of a circle is pi r squared, why negative times negative is positive)
  - probability puzzles (the birthday paradox, Monty Hall)
  - geometry, plus physics concepts drawn as vectors, waves and orbits
- **Honesty edge:** say when a viral trick only works for special numbers.
- **Audience:** English for global school and early-college students, with auto-dubbing for Hindi and Spanish. Syllabus tags in the description, never "Chapter 28" in the title.
- **Needs from the user:** create the channel (a Brand Account) and sign it in.

## 12. Open tools for more accurate videos and stories (14 Nov 2026)
Rule for all of them: the picture is COMPUTED from real data or drawn by code, so it cannot be wrong
the way a generated picture can.

**Pictures drawn by code**
| Need | Tool | Licence | Use |
|---|---|---|---|
| Maths, physics diagrams | Manim Community | MIT | step-by-step animation, every number computed |
| Charts of real numbers | matplotlib (or Manim graphs) | BSD-style | animated charts from real datasets |
| 3D science scenes | Blender (bpy) | GPL (output is ours) | anatomy, objects, orbits |
| Scientific 3D (fields, molecules, terrain) | PyVista / VTK | MIT / BSD | correct 3D shapes from data |
| Molecules | RDKit + PubChem | BSD + free API | true structures from the chemical database |
| Space | Skyfield + NASA JPL Horizons | MIT + free API | real planet and moon positions |
| Physics demos | MuJoCo | Apache 2.0 | simulated falls, pendulums and collisions with real physics |
| Maps | Natural Earth (in use) | public domain | exact borders |
| Web-style animation (option) | Motion Canvas | MIT | needs a headless browser |

**Facts and numbers**
- OpenAlex (in use), Europe PMC (abstracts and open full text), Semantic Scholar (free API), arXiv, Crossref: papers.
- Wikidata (CC0): checkable structured facts (dates, people, places); Wikipedia: only via its cited references.
- Our World in Data (CC BY): curated datasets with sources.
- WHO Global Health Observatory (OData API): health statistics.
- NASA, JPL, NOAA, USGS (earthquakes) APIs: live and official numbers.
- PubChem: chemical facts.

**Real archive pictures for TRUE SCIENCE STORIES**
- Wikimedia Commons (in use): historical photos with licences.
- Smithsonian Open Access (CC0; free api.data.gov key).
- Library of Congress free-to-use images.
- Internet Archive / Prelinger Archives: public-domain films.
- NASA archive (in use).

**Quality checks**
- **faster-whisper (MIT):** transcribe the finished voice and compare it with the script. This catches skipped or mispronounced words before upload.
- **WhisperX (BSD-2):** word-exact timing, to prove captions and scene cuts line up with the voice.

**Suggested order:**
1. Manim (student channel, plus diagrams for the main channel)
2. faster-whisper voice check
3. Wikidata plus archives for story videos
4. real-data charts
5. molecules and space

## 13. Production upgrades: research and what was built (14 Nov 2026)
The question: what else, free and open, makes the videos more rigorous and makes them feel made by a
person? A research pass covered speech, animation, asset libraries, finishing and checks. CPU figures
for the newer speech models are estimates; time any of them on a runner before relying on it.

**Built today**
| What | How | Why |
|---|---|---|
| Natural narration | one sentence at a time; trimmed to the speech; 0.45 s after a full stop, ~0.6 s after a question, up to 0.85 s at a scene change or before a reveal; no breath sounds | sounds like a person reading aloud, not one breathless run (user, 14 Nov) |
| Asking voice | questions read slower, last words raised ~3/4 semitone (same length, captions stay exact); exclamations a touch brighter | the tone change a person makes when asking |
| Listening check (QA 6) | faster-whisper (MIT, CPU) transcribes the final audio; a wrong number or a flipped negative ("can't" heard as "can") holds the video | captions come from the script, so a mis-spoken line used to look right |
| Finishing pass | voice cleaned and compressed, mix levelled to -14 LUFS, music ducked under the voice, light film grain under the captions | the cheap touches of a hand edit |
| Retraction filter | OpenAlex `is_retracted:false` | never cite a retracted paper |
| Second channel | Why It Works (@whyitworksstem), same engine, own settings/memory/bank/sign-in | students, all subjects + new research |
| Weekly lane | the weekly has its own queue and adds its episode on top of the latest saved state | run #3 was bumped from the queue on 14 Nov |

**Next, in order** (all free; adopt = proven fit, try = time it first)
1. Kinetic captions from real word timings (stable-ts / faster-whisper word stamps): adopt.
2. Tesseract OCR of sampled frames: on-screen numbers and spelling checked against the script: adopt.
3. Science archives with clear licences: Smithsonian Open Access (CC0), ESA/Hubble/Webb (CC BY),
   NASA Images, NOAA/USGS (public domain), Servier Medical Art (CC BY), Our World in Data (CC BY data,
   redrawn by us), RCSB PDB / PubChem (molecules): adopt.
4. `pip install bpy` (newer Blender) + Molecular Nodes for molecules, Grease Pencil for a hand-drawn
   look; PyMOL (apt) for quick protein renders: adopt for the student channel.
5. PyVista (fields, flows) and matplotlib animation (real-data charts): adopt.
6. J/L cuts and CC0 scene-change sounds (Freesound API needs a free key from the owner): adopt.
7. Crossref retraction data + PubMed E-utilities + Google Fact Check Tools as extra checks: adopt.
8. Chatterbox-Turbo (MIT, emotion dial) for the weekly episode only, if a runner renders 60 s in
   under ~10 minutes: try.
9. Motion Canvas / HyperFrames (HTML to video) for typography scenes: try.

**Rejected, and why**: F5-TTS (weights non-commercial), Piper (archived, GPL fork, robotic), Dia and
Orpheus (GPU only in practice), Parler-TTS (too slow on CPU), Supertonic (archived), Remotion (paid
above 3 people), Revideo (unmaintained), python-lottie (AGPL), Free Music Archive (mostly
non-commercial). Music has no free API with safe licences: a small CC0/CC-BY set is downloaded by hand
once and kept in assets/music.

## 14. Growth, licences and fresh research: second pass (14 Nov 2026)
Several sources are secondary; official pages are linked in the commit history of this section.

**The biggest risk: YouTube's "inauthentic content" rule** (since 15 Jul 2025). It is aimed at
mass-produced, template-like videos. AI help is allowed with "considerable human input".
- Built today (agents/variety.py): near-duplicate topics dropped (zebra stripes had been made
  twice), hooks that open like most recent ones rewritten, title openings varied.
- What only the owner can add, and what helps most: a short human look at each week's videos (a
  10-minute review of the bank, a changed title or a pinned comment in your own words). Real human
  input is what the rule asks for; it cannot be automated honestly.

**Partner Programme from 01 Feb 2027 for new applicants:** 1,000 subscribers + 8,000 watch hours or
20M Shorts views in 90 days. Why It Works will apply under the new bar, so its long-form watch time
will matter more than Shorts views: plan a weekly long video for it once it has 3+ weeks of Shorts.

**Built today:** exact English captions from the narrator's timings (agents/subtitles.py; 400 quota
units per video, a failure never stops a publish); a 180-concept map for Why It Works
(channels/wiw_concepts.json, names only).

**Already in place (checked):** Shorts → weekly-episode line in every answer comment; series
playlists; chapters; translated titles; auto-dubbing.

**Next, buildable:**
1. bioRxiv/medRxiv `/pubs` (prefers preprints later published in a journal) and arXiv (labelled
   "preprint, not peer-reviewed") as fresh-research feeds for Why It Works.
2. Instagram Reels through the Graph API (free; needs an Instagram professional account and a Meta
   app, which only the owner can create), then Facebook Reels.
3. Misconception openers from the AAAS Project 2061 item bank (free login; owner signs up).
4. Europe PMC / Semantic Scholar for "is this preprint now published?" and follow-up papers.

**Owner steps that unlock more reach (whenever convenient):**
- Apply for the TikTok Content Posting API audit (public posting needs it; takes days to weeks).
- Create an Instagram professional account + Meta developer app for Reels.
- In Studio, by hand (no API exists): the Shorts "related video" link, Test & Compare thumbnails.

**Do not use on a monetised channel:** PhET simulations (moving to non-commercial), GeoGebra and Desmos
(non-commercial terms), CK-12 and most LibreTexts pages, newer OpenStax books (CC BY-NC-SA), syllabus
text or figures (copyright; topic names are fine), EurekAlert text (journalist terms).

## 15. Ideas, research, media and what works now: four-way research + live tests (14 Nov 2026, evening)
Four research passes ran in parallel; every source adopted below was then called live from this PC
before it was built. Secondary claims are marked in the commit messages.

### Built tonight
| Area | What | Source and licence |
|---|---|---|
| Ideas | real questions people asked: top-voted questions on 8 Stack Exchange sites per channel | question titles as ideas only (CC BY-SA text never copied); 300 calls/day keyless |
| Ideas | this week's science headlines | ScienceDaily (headline use allowed with credit), Phys.org; headlines as ideas only |
| Ideas (student) | newest Frontiers for Young Minds articles | peer-reviewed, written for ages 8-15, CC BY 4.0; the paper becomes the cited source |
| Ideas | exam season: an EXAM TRAP topic in the 6 weeks before CBSE (16 Feb 2027), AP (03 May 2027), GCSE (May 2027) | dates from the boards |
| Demand | topics ranked by the median daily readers of their Wikipedia article (planner names the article) | Wikimedia pageviews, open data |
| Rigour | the fact-checker compares claims with the lead of the subject's Wikipedia article | reference only, never shown |
| Footage | iNaturalist: the exact species, research-grade, CC0/CC BY, credited | per-photo licence filter |
| Footage | Wellcome Collection: anatomy, medicine, microscopy; PDM/CC BY only | CC BY-NC skipped |
| Format | VIRAL CLAIM, CHECKED (main channel) | fact-check channels were among the fastest-growing Shorts of 2026 |
| Packaging | Why It Works titles: no emoji, no all-caps, 30-55 characters | AIR study of 18,080 channels (correlational): emoji and caps hurt trust in education |
| Plumbing | every OpenAlex call uses OPENALEX_API_KEY when set | keyless = 1,000 credits/day per (shared) runner address since Feb 2026 |

### Tested and rejected
- Semantic Scholar TLDR: works, but its licence is non-commercial.
- Wikipedia "top articles" as an idea feed: almost all celebrities; used for demand instead.
- Physics Stack Exchange "hot": mostly graduate-level; "top votes" on many sites is far better.
- Internet Archive Prelinger: licences mixed per item, footage old; not worth it yet.
- Reddit (paid/approval-only since Nov 2025, non-commercial free tier), Google "People also ask"
  (scraping), pytrends (archived), Pollinations (no clear commercial rights), Recraft free tier
  (non-commercial), Free Music Archive (API closed), BBC Sound Effects (non-commercial), PhET,
  GeoGebra, Desmos, Cochrane text, Science News Explores text, IUCN API (commercial use forbidden).

### Next (ranked)
1. Arrows and highlights timed to the narration on drawn scenes (signalling: d = 0.38 in learning
   studies; Noetel et al. 2022 meta-review).
2. Reply-to-comment Shorts: the best viewer question each week becomes a Short (the "viewer requests"
   list already collects them).
3. Wikipedia "On this day" + Wikidata dates for anniversary hooks (CC0 data).
4. Wikidata SPARQL, JPL SSD, PubChem, USDA FoodData Central, AnAge for checking specific numbers
   (lifespans, masses, distances, nutrients) against databases, not just the model.
5. Europe PMC full text (CC BY/CC0 only) for richer briefs and conflict-of-interest checks.
6. ESO (CC BY 4.0, visible credit) and Met/Rijksmuseum (CC0) as image sources; BHL illustrations
   via Flickr (needs a free Flickr key).
7. Icons for diagrams from Apache/MIT/CC0 sets (Material Symbols, Tabler, Phosphor, Health Icons).
8. Experiments to run with the Analytics API (engaged views, average % viewed): a 1-2 s "Guess?" pause
   before answers; length bands (<25 s, 35-50 s, 60-90 s); question vs statement titles.

### Owner steps that unlock more (free)
1. **OpenAlex API key (most important):** sign up at openalex.org, copy the key, add GitHub secret
   `OPENALEX_API_KEY`. Without it the sources step can run out of its daily allowance.
2. Stack Exchange key (stackapps.com, raises 300 to 10,000 calls a day): secret `STACKEXCHANGE_KEY`
   (already wired: add the secret and it is used).
3. Music: pick 5-10 tracks you like from Incompetech (CC BY 4.0) or Kenney (CC0) and put the MP3s in
   assets/music; the mix already ducks music under the voice. Taste is yours to choose.
4. In Studio by hand: Shorts "related video" links, Test & Compare, the Quiz/Poll stickers on a few
   Shorts (no API exists for any of these).

### Code-drawn visuals added tonight (all rendered here and checked by eye)
The first Why It Works video ("negative times negative") had to use stock footage for a maths idea,
so six new computed animation types were added. In every one, the model only chooses and labels; the
numbers, shapes and geometry come from code or data, and a check refuses anything it cannot verify.
| Type | Draws | Accuracy guard |
|---|---|---|
| Equation | a worked example line by line, result in yellow | every arithmetic line is evaluated; all numbers must be said |
| NumberLine | jumps along a marked line | every number said; every landing inside the range |
| Graph | a curve from a formula (doubling, inverse square, waves) | safe maths only, real across the range, constants said |
| Circuit | battery (+ long, - short), resistor/bulb/LED, moving charges | direction stated and labelled (conventional vs electrons) |
| Molecule | the real 3D molecule, face-on, gently rocking | geometry from PubChem; the model only names it |
| Cycle | 3-5 stages round a ring with arrows | only for lines about something that repeats |
The student channel can use up to 5 per video; the main channel 2.
