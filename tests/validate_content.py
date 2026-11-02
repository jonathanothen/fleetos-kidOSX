"""Checks that every voice clip and picture the games use exists. Run: python3 tests/validate_content.py"""
import csv, os, re, sys
ROOT = os.path.join(os.path.dirname(__file__), "..")
GAMES = os.path.join(ROOT, "rootfs", "overlay", "usr", "share", "kidsos", "games")
sys.path.insert(0, GAMES)
errors = []
voices = {f[:-4] for f in os.listdir(os.path.join(GAMES, "assets", "voices", "sv")) if f.endswith(".mp3")}
images = {f[:-4] for f in os.listdir(os.path.join(GAMES, "assets", "images")) if f.endswith(".svg")}
with open(os.path.join(ROOT, "docs", "content", "voice-lines.csv"), encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if row["id"] not in voices: errors.append("voice missing: " + row["id"])
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
for u in sorted(used - voices): errors.append("voice used by Mattelek but missing: " + u)
for fn in os.listdir(os.path.join(GAMES, "assets", "voices", "sv")):
    if os.path.getsize(os.path.join(GAMES, "assets", "voices", "sv", fn)) < 1000: errors.append("suspiciously small: " + fn)
print("\n".join(errors) if errors else "content: OK (%d voices, %d images)" % (len(voices), len(images)))
sys.exit(1 if errors else 0)