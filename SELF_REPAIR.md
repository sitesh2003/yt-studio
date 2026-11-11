# How the channel repairs itself

Every fault met while building this channel is listed here with how the cloud **sees** it and what it
**does** about it. No person is needed for any of them. Each fault it catches is also saved to
`data/lessons.json`, and the writer reads those lessons before every new script, so a mistake is
made once at most.

| Fault | How it is seen | What the cloud does |
|---|---|---|
| GitHub skips a planned production run | Health agent compares the planned times in `daily.yml` with GitHub's run list, every 2 hours | Notes it in the email and STATUS.md, and starts a catch-up run if the bank is short |
| A production run fails or runs out of time | Same run list (failure / cancelled / timed out) | Catch-up run; 95-minute budget so the report always goes out |
| Not enough videos ready ahead | Video bank counted from YouTube itself | Each run tops the bank up to 2 days (6 videos), within about 5 uploads a day of free quota |
| Ubuntu's download server hangs (FFmpeg) | Install step | FFmpeg comes from PyPI; apt is only the back-up, both with time limits |
| Pixabay says "too many requests" | HTTP 429 | Waits and retries; one failed download only affects that scene |
| Free AI model busy or retired | 503 / 429 / 404 | Rotates through the model list with patient retries |
| Microsoft voice refuses | NoAudioReceived | Retries, then two back-up voices |
| A claim cannot be confirmed | Fact-checker (2 rounds of fixes) | Cuts or replaces the unconfirmed claims and checks again; only if that fails is the topic skipped, **before** any voice or footage is made |
| Title or first line overstates | Fact-checker checks the title and hook hardest | Rewrites them true before anything is built |
| Footage does not match the words | Footage judge scores every clip; quality reviewer looks at a frame of each scene | Re-picks those scenes up to 2 times, and thinks of **new search words** for scenes with no good match |
| One or two scenes still have nothing after every search | Footage scores after the 2 repairs | Holds the strongest neighbouring shot a little longer instead of losing the whole video, then re-checks |
| The reviewer mistakes our own corner logo for a brand | Reviewer prompt | The reviewer is told the corner mark is the channel's logo |
| A false line is found after upload | Last accuracy audit of every waiting video, before it goes public | Deletes the never-public video, saves the exact wrong line and the truth, and remakes it first in the next run (max 2 tries) |
| A title or description is overstated after upload | Same audit | Rewrites them in place on YouTube |
| A video takes off | Views 3x the channel median (1,000+) | Makes a sequel the next day |
| New comments | Every 2 hours | Short, warm replies; the answer to each closing question is posted when the video goes public |

What still needs a person: creating accounts (Instagram, Facebook), signing in, and anything that
touches a password or a payment.
