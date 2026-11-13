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

## 5. Plan
1. **Done (13 Nov):**
   - full-screen crop around the subject
   - real NASA and Commons footage
   - research lessons in every script (data/research.json)
   - premise audit and script lint
   - a voice swap that actually swaps
   - board drift
2. **Illustrated scenes (needs the user):** create a free Cloudflare account and save its account ID and API token as GitHub secrets (CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_API_TOKEN). The free tier makes about 100–230 FLUX schnell images a day, and FLUX schnell is Apache 2.0. Every scene would be drawn in one consistent stylised style, never photo-real, and the picture judge would check each image for accuracy.
3. **A weekly long-form video** (8–10 min, 16:9) on the same researched topics. This builds watch hours toward YPP and earns the high long-form RPM.
4. **Fewer, better Shorts** once illustration works: 1–2 a day.
5. **Experiment:** drop the countdown in half the videos for a week and compare average view percentage. This is waiting for the user's yes, because the countdown is their idea.
6. **Second channel, geography and maps:** Natural Earth data is public domain, so maps drawn by code are 100% accurate. The niche's median is 3.6M views, and World Ji Ke has 88k subscribers after 6 months.
7. **Spanish:** turn on YouTube auto-dubbing (27 languages, a Studio setting), or later a dubbed Spanish twin channel using Kokoro's Spanish voices.
8. **Off-YouTube income:** free PDF diagram packs; sponsors such as Brilliant or CuriosityStream after about 10k subscribers. Facebook and Snapchat payouts in India are invite-only or unclear, and TikTok is banned in India.

## 6. What we will not do
- re-cut TV, film or game footage (Explain Station, The Ranking Dude)
- photo-real AI imagery
- several near-identical channels
- automated comments on other channels
- kids content (lowest RPM, and the main crackdown target)
