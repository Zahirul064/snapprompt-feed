# Weekly update procedure

Used by the scheduled task (and by hand).

1. Research: search the web for AI photo-editing prompt trends popular **now** (focus on the last 7 days; trends from the last 30 days that the feed does not cover yet also count)
   (ChatGPT Images, Gemini / Nano Banana, Instagram, TikTok, Pinterest, X, news and blog round-ups).
   Prefer trends mentioned by several independent sources.
2. Pick 3–6 trends that are **photo edits of the user's own photo**, not already in
   `tool/bundled_names.txt` or `items.json`, and safe:
   - no nudity or sexualised edits, no minors in adult themes, no celebrity look-alikes or
     impersonation, no copyrighted characters or brand logos, no fake documents/IDs,
     no political or hateful content, no deceptive "real photo" claims.
3. Write each entry **in your own words** (never copy a prompt verbatim from a source):
   a single clear instruction in English and natural Bangladeshi-style Bangla.
   Set `identity_sensitive: true` when a person's face must stay the same.
   `added_on` = today, `trend_note` = short source/trend note.
4. `python3 tool/build_feed.py` then `python3 tool/build_feed.py --check`.
5. Commit `items.json` + `feed.json` with a message like `Feed: add N trending prompts (YYYY-MM-DD)`
   and push to `main`.
6. If nothing new and safe is found, change nothing.
