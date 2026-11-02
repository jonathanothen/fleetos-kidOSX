"""Run: python3 tests/test_parihop.py   (no pygame needed)"""
import os, random, sys
games = os.path.join(os.path.dirname(__file__), "..", "rootfs", "overlay", "usr", "share", "kidsos", "games")
sys.path.insert(0, games)
from kidsgames.parihop import logic as L

voices = {f[:-4] for f in os.listdir(os.path.join(games, "assets", "voices", "sv"))}
images = {f[:-4] for f in os.listdir(os.path.join(games, "assets", "images"))}
for rounds in (0, 1, 2, 3, 6):
    for seed in range(50):
        r = L.make_round(rounds, random.Random(seed))
        assert len(r) == 8 and len({t["answer"]["text"] for t in r}) == 8
        for t in r:
            ch = t["choices"]
            assert len(ch) == L.choices_for(rounds) and ch[t["right"]] is t["answer"]
            assert len({w["text"] for w in ch}) == len(ch) and len({w["text"][0] for w in ch}) == len(ch)
            for w in ch:
                assert w["voice"] in voices and w["pic"] in images, w
assert L.choices_for(0) == 2 and L.choices_for(2) == 3 and L.choices_for(50) == 4
print("parihop: OK")