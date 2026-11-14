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
