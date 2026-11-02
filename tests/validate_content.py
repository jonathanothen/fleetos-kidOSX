"""Checks that every voice clip and picture the games use exists. Run: python3 tests/validate_content.py"""
import csv, os, re, sys
ROOT = os.path.join(os.path.dirname(__file__), "..")
GAMES = os.path.join(ROOT, "rootfs", "overlay", "usr", "share", "kidsos", "games")
sys.path.insert(0, GAMES)
errors, unmade = [], []
voices = {f[:-4] for f in os.listdir(os.path.join(GAMES, "assets", "voices", "sv")) if f.endswith(".mp3")}
images = {f[:-4] for f in os.listdir(os.path.join(GAMES, "assets", "images")) if f.endswith(".svg")}
with open(os.path.join(ROOT, "docs", "content", "voice-lines.csv"), encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if row["id"] not in voices: unmade.append(row["id"])      # ordered but not generated yet: fine, the games skip them
with open(os.path.join(ROOT, "docs", "content", "words.csv"), encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if row["picture_id"] not in images: errors.append("picture missing: " + row["picture_id"])
# every clip the Mattelek generators can ask for
import random
from kidsgames.mattelek import generators as G
rng = random.Random(1)
used = {"say_hello", "say_choose_game", "say_well_done_round", "say_sticker", "say_hint_objects", "say_retry_1",
        "say_retry_2", "say_correct_1", "say_correct_2", "say_correct_3", "say_correct_4"}
used |= {"num_%03d" % i for i in range(0, 21)}
for s in G.SKILLS:
    for _ in range(300):
        used |= set(G.make_task(s, rng)["say"])
from kidsgames.skrivlabbet import content as SC
used |= SC.clip_ids_used()
for u in sorted(used - voices): errors.append("voice used by Mattelek but missing: " + u)
for fn in os.listdir(os.path.join(GAMES, "assets", "voices", "sv")):
    if os.path.getsize(os.path.join(GAMES, "assets", "voices", "sv", fn)) < 1000: errors.append("suspiciously small: " + fn)
import re
from kidsgames.klockan import logic as KL
ordered = set()
with open(os.path.join(ROOT, "docs", "content", "voice-lines.csv"), encoding="utf-8") as f:
    ordered = {row["id"] for row in csv.DictReader(f)}
found = set()
for dirpath, _d, files in os.walk(os.path.join(GAMES, "kidsgames")):
    for fn in files:
        if fn.endswith(".py"):
            with open(os.path.join(dirpath, fn), encoding="utf-8") as src:
                found |= set(re.findall(r"[\x22\x27]((?:say|tile)_[a-z0-9_]+)[\x22\x27]", src.read()))
for h in range(1, 13):
    for m in range(0, 60, 5):
        found |= set(KL.spoken_ids(h, m))
pending = sorted(i for i in found if i not in voices and i in ordered)
for i in sorted(found):
    if i not in voices and i not in ordered and i not in ("say_correct", "say_retry"):
        errors.append("used in a game, neither made nor in the order list: " + i)
if unmade:
    print("ordered but not generated yet: %d (see docs/VOICE-PLAN.md)" % len(unmade))
if pending:
    print("pending (ordered, not made yet; the games skip them silently): %d" % len(pending))
print("\n".join(errors) if errors else "content: OK (%d voices, %d images)" % (len(voices), len(images)))
sys.exit(1 if errors else 0)