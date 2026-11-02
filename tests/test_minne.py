"""Run: python3 tests/test_minne.py   (no pygame needed)"""
import os, random, sys
games = os.path.join(os.path.dirname(__file__), "..", "rootfs", "overlay", "usr", "share", "kidsos", "games")
sys.path.insert(0, games)
from kidsgames.minne import logic as L
voices = {f[:-4] for f in os.listdir(os.path.join(games, "assets", "voices", "sv"))}
images = {f[:-4] for f in os.listdir(os.path.join(games, "assets", "images"))}
for stage in range(4):
    for seed in range(40):
        b = L.make_board(stage, random.Random(seed))
        assert len(b) == 2 * L.PAIRS[stage], len(b)
        pairs = {}
        for c in b:
            pairs.setdefault(c["pair"], []).append(c)
            assert c["word"]["voice"] in voices and c["word"]["pic"] in images
        assert all(len(v) == 2 and {x["kind"] for x in v} == {"pic", "word"} for v in pairs.values())
        assert len({c["word"]["text"][0] for c in b}) == len(b) // 2        # every word starts with another letter
        for a in b:
            assert sum(1 for x in b if L.is_match(a, x)) == 1
assert L.is_match({"pair": 1, "kind": "pic"}, {"pair": 1, "kind": "word"}) and not L.is_match({"pair": 1, "kind": "pic"}, {"pair": 2, "kind": "word"})
print("minne: OK")