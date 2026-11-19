# SnapPrompt AI — prompt feed

Public feed of new and trending AI photo-editing prompts for the
[SnapPrompt AI](https://github.com/Zahirul064/snap_prompt_ai) Android app.

The app downloads `feed.json` about once a day (a plain HTTPS GET; nothing
about the user is sent), adds new commands to its library with a "New"
badge and shows a notification listing them. Users can turn this off in
Settings. A scheduled task adds new trending prompts every week.

App URL: `https://raw.githubusercontent.com/Zahirul064/snapprompt-feed/main/feed.json`

## Files

| File | Purpose |
| --- | --- |
| `items.json` | Hand-written entries (edit this) |
| `feed.json` | Generated file the app reads (do not edit by hand) |
| `tool/build_feed.py` | Builds `feed.json`, validates every rule the app enforces, bumps `feed_version` |
| `tool/bundled_names.txt` | Names already in the app's bundled library (must not be reused) |
| `tool/categories.txt` | The 12 category ids the app knows |
| `UPDATING.md` | Monthly update procedure |

## Adding prompts

1. Add an entry to `items.json` (id `feed_...`, name `/CamelCase`, one of the 12 categories, EN + BN text, tags, `added_on`).
2. `python3 tool/build_feed.py`
3. Commit `items.json` and `feed.json` together. CI runs `--check`.

## Rules the app enforces

- `format` = `snapprompt-feed`, `format_version` 1, integer `feed_version` that increases on every change.
- Ids match `^feed_[a-z0-9_]{2,60}$`; names match `^/[A-Za-z0-9]{2,40}$` and must be unique (also against bundled names).
- Text fields up to 4000 characters; 1–20 tags; at most 1000 commands; file up to 1 MB.
- The app never lets the feed change built-in or user-made commands; broken entries are skipped.
- Removing an entry from the feed does not remove it from phones that already have it.
