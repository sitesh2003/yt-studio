# YT Studio

A team of agents that runs a YouTube Shorts channel for a US audience, on free tools only.

| Agent | Job | Free tool |
|---|---|---|
| Trends | Finds the fastest-growing Shorts in your niche in the US, last 30 days | YouTube Data API key |
| Writer | Picks new topics, writes hook, script, titles, description, tags, fact list | Gemini API (free tier) |
| Voice | American neural voice with exact word timings | Edge TTS (no key) |
| Visuals | Vertical stock clips for every scene | Pexels API |
| Editor | Cuts to the voice, word-by-word captions, music, thumbnail | FFmpeg + Pillow |
| Publisher | Uploads and schedules at US prime time (12:00 / 15:00 / 19:00 ET) | YouTube API (OAuth) |
| Community | Drafts replies to new comments in your voice | YouTube API + Gemini |
| Analyst | Reads your real retention numbers and teaches the writer | YouTube Analytics API |

## Setup (once, about 20 minutes)

1. Copy `.env.example` to `.env`.
2. Get the free keys and paste them into `.env`:
   - Gemini: https://aistudio.google.com/apikey
   - Pexels: https://www.pexels.com/api/
   - YouTube Data API key: Google Cloud console, new project, enable "YouTube Data API v3", Credentials, API key.
3. For uploading: in the same project enable "YouTube Analytics API" too, set up the OAuth consent screen
   (External, add yourself as a test user), create an OAuth client of type **Desktop app**, download the
   JSON and save it here as `client_secret.json`. The first upload opens your browser once to sign in.
4. Put a few royalty-free tracks in `assets/music/` (YouTube Audio Library is free). Optional.
5. Test with no keys: `.venv\Scripts\python studio.py demo`

**Important:** YouTube locks videos uploaded through a new, unaudited API project to *private*. Until
Google approves the free audit (search "YouTube API Services audit and quota extension form"), use
review mode and upload the finished `final.mp4` yourself in YouTube Studio. It takes two minutes.

## Daily use

```
.venv\Scripts\python studio.py daily      # makes today's video(s) and queues them
.venv\Scripts\python studio.py queue      # what is waiting; open each review.html
.venv\Scripts\python studio.py approve <job>
.venv\Scripts\python studio.py comments   # drafts in data/reply_drafts.json; set "approved": true, then --post
.venv\Scripts\python studio.py learn      # after 5+ videos have data
```

`config.json` controls the niche, voice, caption style, posting slots and modes.
`publish.mode`: `review` (default) or `auto`. `community.mode`: `draft` (default) or `auto`.

To run it every day at 9 PM IST, run once in a terminal:
`schtasks /Create /SC DAILY /ST 21:00 /TN "YT Studio daily" /TR "\"%CD%\run_daily.bat\""`
