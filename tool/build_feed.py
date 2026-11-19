#!/usr/bin/env python3
"""Builds and validates feed.json for the SnapPrompt AI app.

Usage:
    python3 tool/build_feed.py            # rebuild feed.json from items.json
    python3 tool/build_feed.py --check    # validate only

items.json holds the hand-written entries: id, name, category, titles,
descriptions, core instruction (EN/BN), tags, identity flag and the date it
was added. This script appends the identity sentence and the category
closing exactly like the app's bundled library, checks every rule the app
enforces, and bumps feed_version when the content changed.
"""
import datetime
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
ITEMS = ROOT / "items.json"
FEED = ROOT / "feed.json"

IDENTITY_EN = ("Keep every person's face, facial structure, features, natural skin tone "
               "and identity exactly the same; do not beautify, reshape or replace the face.")
IDENTITY_BN = ("প্রত্যেক মানুষের মুখ, মুখের গঠন, বৈশিষ্ট্য, স্বাভাবিক ত্বকের রং ও পরিচয় হুবহু একই রাখুন; "
               "মুখ সুন্দর করা, আকৃতি বদলানো বা প্রতিস্থাপন করবেন না।")

# Same closings as the bundled library (tool/build_commands.py in the app).
CLOSINGS = {
    'photo_enhancement': ('Do not add, remove or restyle anything. Keep the result realistic, with no over-sharpened or plastic look, at the original aspect ratio.',
        'কিছু যোগ, বাদ বা নতুন করে সাজাবেন না। ফলাফল বাস্তবসম্মত রাখুন, অতিরিক্ত শার্প বা প্লাস্টিকের মতো ভাব ছাড়া, মূল অনুপাতে।'),
    'color_correction': ('Do not change the scene, composition or any object. Keep the result a realistic photo at the original aspect ratio.',
        'দৃশ্য, কম্পোজিশন বা কোনো বস্তু বদলাবেন না। ফলাফল মূল অনুপাতে বাস্তবসম্মত ছবি রাখুন।'),
    'face_restoration': ('Do not change the background, clothing or composition. Keep natural skin texture, with no plastic or airbrushed look.',
        'ব্যাকগ্রাউন্ড, পোশাক বা কম্পোজিশন বদলাবেন না। ত্বকের স্বাভাবিক টেক্সচার রাখুন, প্লাস্টিকের মতো বা এয়ারব্রাশ করা ভাব ছাড়া।'),
    'background_editing': ('Keep the main subject completely unchanged, with clean natural edges around hair and fine details, and match the lighting so the result looks like a real photograph.',
        'মূল বিষয় সম্পূর্ণ অপরিবর্তিত রাখুন, চুল ও সূক্ষ্ম ডিটেইলের চারপাশে পরিষ্কার স্বাভাবিক প্রান্তসহ, এবং আলো মিলিয়ে নিন যাতে ফলাফল আসল ছবির মতো দেখায়।'),
    'passport_id': ("Use even lighting with no shadows on the face or background and keep the image in sharp focus. Do not retouch or alter the person's appearance or expression.",
        'সমান আলো ব্যবহার করুন, মুখে বা ব্যাকগ্রাউন্ডে কোনো ছায়া ছাড়া, এবং ছবি শার্প ফোকাসে রাখুন। ব্যক্তির চেহারা বা অভিব্যক্তি রিটাচ বা পরিবর্তন করবেন না।'),
    'portrait_professional': ("Keep it a believable photograph with natural skin texture, and do not change the person's age, body shape or expression.",
        'এটি যেন স্বাভাবিক ত্বকের টেক্সচারসহ বিশ্বাসযোগ্য ছবি থাকে, এবং ব্যক্তির বয়স, শরীরের গড়ন বা অভিব্যক্তি বদলাবেন না।'),
    'old_photo_restoration': ("Do not invent new details or modernise clothing, hairstyles or the setting. Keep the photo's original character and aspect ratio.",
        'নতুন কোনো ডিটেইল বানাবেন না এবং পোশাক, চুলের স্টাইল বা পরিবেশ আধুনিক করবেন না। ছবির আসল বৈশিষ্ট্য ও অনুপাত বজায় রাখুন।'),
    'creative_effects': ('Keep the original composition and keep the main subject clearly recognisable.',
        'মূল কম্পোজিশন বজায় রাখুন এবং মূল বিষয় যেন স্পষ্টভাবে চেনা যায়।'),
    'object_person_editing': ('Leave everything else in the photo exactly as it is, and make the edit seamless, with matching light, shadow, texture and perspective.',
        'ছবির বাকি সবকিছু হুবহু যেমন আছে তেমন রাখুন এবং এডিটটি নিখুঁত করুন; আলো, ছায়া, টেক্সচার ও পার্সপেক্টিভ যেন মিলে যায়।'),
    'social_media': ('Keep the main subject sharp and well placed inside the frame, with no important part cropped out.',
        'মূল বিষয় শার্প ও ফ্রেমের ভেতরে ভালো জায়গায় রাখুন; কোনো গুরুত্বপূর্ণ অংশ যেন কাটা না পড়ে।'),
    'resolution_printing': ('Do not change the content, colors or look of the photo.',
        'ছবির বিষয়বস্তু, রং বা লুক বদলাবেন না।'),
    'body_composition': ('Keep the result natural and anatomically correct, and do not change faces, clothing or the setting.',
        'ফলাফল স্বাভাবিক ও শারীরিক গঠনের দিক থেকে সঠিক রাখুন এবং মুখ, পোশাক বা পরিবেশ বদলাবেন না।'),
}

ID_RE = re.compile(r"^feed_[a-z0-9_]{2,60}$")
NAME_RE = re.compile(r"^/[A-Za-z0-9]{2,40}$")
MAX_TEXT = 4000


def fail(message):
    print(f"ERROR: {message}")
    sys.exit(1)


def load_lines(name):
    return {line.strip() for line in (ROOT / "tool" / name).read_text(encoding="utf-8").splitlines() if line.strip()}


def build_commands(items):
    bundled = {n.lower() for n in load_lines("bundled_names.txt")}
    categories = load_lines("categories.txt")
    ids, names, commands = set(), set(), []
    for item in items:
        where = item.get("id", "?")
        if not ID_RE.match(item["id"]):
            fail(f"{where}: id must match {ID_RE.pattern}")
        if not NAME_RE.match(item["name"]):
            fail(f"{where}: bad name {item['name']}")
        if item["id"] in ids:
            fail(f"{where}: duplicate id")
        if item["name"].lower() in names:
            fail(f"{where}: duplicate name")
        if item["name"].lower() in bundled:
            fail(f"{where}: {item['name']} already exists in the app's bundled library")
        if item["category_id"] not in categories:
            fail(f"{where}: unknown category {item['category_id']}")
        if item["category_id"] not in CLOSINGS:
            fail(f"{where}: add a closing for {item['category_id']} in CLOSINGS")
        ids.add(item["id"])
        names.add(item["name"].lower())

        close_en, close_bn = CLOSINGS[item["category_id"]]
        identity = bool(item.get("identity_sensitive", True))
        core_en, core_bn = item["instruction_en"].strip(), item["instruction_bn"].strip()
        prompt_en = " ".join([core_en] + ([IDENTITY_EN] if identity else []) + [close_en])
        prompt_bn = " ".join([core_bn] + ([IDENTITY_BN] if identity else []) + [close_bn])
        for label, text in (("prompt_en", prompt_en), ("prompt_bn", prompt_bn)):
            if len(text) > MAX_TEXT:
                fail(f"{where}: {label} longer than {MAX_TEXT}")
        tags = item.get("tags", [])
        if not tags or len(tags) > 20 or any(not t.strip() or len(t) > 40 for t in tags):
            fail(f"{where}: 1-20 tags, each 1-40 characters")
        datetime.date.fromisoformat(item["added_on"])

        commands.append({
            "id": item["id"],
            "name": item["name"],
            "title_en": item["title_en"],
            "title_bn": item["title_bn"],
            "category_id": item["category_id"],
            "description_en": item["description_en"],
            "description_bn": item["description_bn"],
            "prompt_en": prompt_en,
            "prompt_bn": prompt_bn,
            "instruction_en": core_en,
            "instruction_bn": core_bn,
            "tags": tags,
            "identity_sensitive": identity,
            "is_popular": bool(item.get("is_popular", False)),
            "added_on": item["added_on"],
            "trend_note": item.get("trend_note", ""),
        })
    if len(commands) > 1000:
        fail("the app reads at most 1000 commands")
    return commands


def main():
    check_only = "--check" in sys.argv
    items = json.loads(ITEMS.read_text(encoding="utf-8"))["items"]
    commands = build_commands(items)

    previous = json.loads(FEED.read_text(encoding="utf-8")) if FEED.exists() else None
    if check_only:
        if previous is None or previous["commands"] != commands:
            fail("feed.json is out of date: run python3 tool/build_feed.py")
        print(f"OK: feed_version {previous['feed_version']}, {len(commands)} commands")
        return

    version = previous["feed_version"] if previous else 0
    if previous is None or previous["commands"] != commands:
        version += 1
    feed = {
        "format": "snapprompt-feed",
        "format_version": 1,
        "feed_version": version,
        "updated_at": datetime.date.today().isoformat(),
        "commands": commands,
    }
    if previous is not None and previous["commands"] == commands:
        feed["updated_at"] = previous["updated_at"]
    FEED.write_text(json.dumps(feed, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"feed.json: feed_version {version}, {len(commands)} commands")


if __name__ == "__main__":
    main()
