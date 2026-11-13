# How the channel repairs itself

Every fault met while building this channel is listed here with how the cloud **sees** it and what it
**does** about it. No person is needed for any of them. Each fault it catches is also saved to
`data/lessons.json`, and the writer reads those lessons before every new script, so a mistake is
made once at most.

| Fault | How it is seen | What the cloud does |
|---|---|---|
| GitHub skips a planned production run | Health agent compares the planned times in `daily.yml` with GitHub's run list, every 2 hours | Notes it in the email and STATUS.md, and starts a catch-up run if the bank is short |
| A production run fails or runs out of time | Same run list (failure / cancelled / timed out) | Catch-up run; 95-minute budget so the report always goes out |
| A wrong video reaching the channel at all | Every finished video is audited (with a second opinion) BEFORE it enters the bank | Only audited videos wait in the bank (GitHub 'video-bank' release); the publisher uploads just the next day's 3 slots, so nothing on YouTube ever needs deleting |
| Not enough videos ready ahead | Video bank counted from YouTube itself | Each run tops the bank up to 2 days (6 videos), within about 5 uploads a day of free quota; if it holds less than a day, the health agent starts a production run straight away (at most every 3 hours) |
| Ubuntu's download server hangs (FFmpeg) | Install step | FFmpeg comes from PyPI; apt is only the back-up, both with time limits |
| Pixabay says "too many requests" | HTTP 429 | Waits and retries; one failed download only affects that scene |
| Free AI model busy or retired | 503 / 429 / 404 | Rotates through the model list with patient retries |
| Microsoft voice refuses | NoAudioReceived | Retries, then two back-up voices |
| A claim cannot be confirmed | Fact-checker (2 rounds of fixes) | Cuts or replaces the unconfirmed claims and checks again; only if that fails is the topic skipped, **before** any voice or footage is made |
| Title or first line overstates | Fact-checker checks the title and hook hardest | Rewrites them true before anything is built |
| Footage does not match the words | Footage judge scores every clip; quality reviewer looks at a frame of each scene | Re-picks those scenes up to 2 times, and thinks of **new search words** for scenes with no good match |
| Pixabay has nothing for a specific plant, animal or food (krill, wasabi, salmon fry) | Footage search | Also searches Wikimedia Commons, Openverse (millions of openly licensed photos) and the NASA image library, keeping only public-domain, CC0 and CC BY (credited in the description; never share-alike, non-commercial or no-derivatives) |
| Nothing on any stock site shows the moment (what happens inside the tongue, the apple, the tree) | Footage judge finds no good match | The AI draws an explainer diagram (free, rendered here) that builds up on screen in stages like a teacher at a board; a separate check must agree it is accurate and a 12-year-old would understand it; up to 3 per video |
| One or two scenes still have nothing after every search | Footage scores after the 2 repairs | Holds the strongest neighbouring shot a little longer instead of losing the whole video, then re-checks |
| The reviewer mistakes our own corner logo for a brand | Reviewer prompt | The reviewer is told the corner mark is the channel's logo |
| A false line is found after upload | Last accuracy audit of every waiting video, before it goes public, then a SECOND independent check that must agree (and must confirm the correction) before anything is deleted or learned | Deletes the never-public video, saves the exact wrong line and the truth, and remakes it first in the next run (max 2 tries) |
| A title or description is overstated after upload | Same audit | Rewrites them in place on YouTube |
| The free AI answers in an unexpected shape (a list instead of an object) | Every AI answer passes one shape check | Read either way; topic picking retries instead of ending the run |
| A video takes off | Views 3x the channel median (1,000+) | Makes a sequel the next day |
| "Pause and guess" said twice (maple syrup, 12 Nov) | Every script, before the voice | Kept once, straight before "three, two, one"; extra countdowns removed |
| The market moves | Weekly study of the top 20 science Shorts + our own numbers | data/playbook.json rewritten: formats, hooks, length (30-50 s); the writer follows it |
| A drawn explainer is wrong or unreadable | A separate picture check on every diagram and board | Redrawn up to twice, else real footage is used |
| A script repeats itself, runs long, or gives the answer before the countdown | A lint pass on every script | Rewritten once before the fact-check |
| A video's premise or contrast is false ("X sticks, Y slides off") | The last audit checks the premise first | Not banked; a corrected remake is queued |
| A banked video is found wrong later | data/pull.json, read before every publish | Deleted from the bank, remake queued |
| A run queued behind another starts from old state and its save erases newer work | Every workflow checks out the latest main when it starts, not the queued commit | Nothing to repair: the stale copy never exists |
| No real footage shows a line exactly (score under 8) | Once Cloudflare keys exist, an illustration is drawn and a separate vision check scores it (0 for anything scientifically wrong, any lettering, or a photo look) | Used only if it passes (7+) AND beats the footage; daily cap of 60 keeps it free, 25 of them at most for the weekly video |
| A line is about where something is on Earth | The writer marks it "map" | Drawn from Natural Earth data (exact shapes); a place not in the data falls back to footage |
| Is the countdown helping or hurting? | Half the Shorts have it, half ask the question plainly (data/experiments.json) | After 8+ of each, public 2+ days, the arm with the higher average view percentage (5+ points ahead, or the leader at 15 each) becomes the rule |
| Viewers outside the US see an English title | Every upload | Title and teaser translated into Spanish, Portuguese, German, French and Hindi (credits stay as written) |
| New comments | Every 2 hours | Short, warm replies; the answer to each closing question is posted when the video goes public |

What still needs a person: creating accounts (Instagram, Facebook), signing in, and anything that
touches a password or a payment.
