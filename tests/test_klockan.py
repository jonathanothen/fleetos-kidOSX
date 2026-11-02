"""Run: python3 tests/test_klockan.py   (no pygame needed)"""
import os, random, sys
games = os.path.join(os.path.dirname(__file__), "..", "rootfs", "overlay", "usr", "share", "kidsos", "games")
sys.path.insert(0, games)
from kidsgames.klockan import logic as L
voices = {f[:-4] for f in os.listdir(os.path.join(games, "assets", "voices", "sv"))}
for stage in range(4):
    for seed in range(100):
        ts = L.make_tasks(stage, random.Random(seed))
        assert len(ts) == 8
        for t in ts:
            assert t["m"] in L.MINUTES[stage] and 1 <= t["h"] <= 12 and ("num_%03d" % t["h"]) in voices
            assert (t["h"], t["m"]) == t["choices"][t["right"]] and len(set(t["choices"])) == len(t["choices"]) >= 3
assert L.hand_angles(3, 0) == (90.0, 0.0) and L.hand_angles(6, 30) == (195.0, 180.0) and L.hand_angles(12, 15)[1] == 90.0
assert L.fmt(3, 5) == "3:05"
assert L.spoken_ids(3, 0) == ["say_clock_is", "num_003"]
assert L.spoken_ids(3, 30) == ["say_clock_is", "say_clock_halv", "num_004"]            # halv fyra
assert L.spoken_ids(3, 45) == ["say_clock_is", "say_clock_kvart_i", "num_004"]       # kvart i fyra
assert L.spoken_ids(3, 15) == ["say_clock_is", "say_clock_kvart_over", "num_003"]
assert L.spoken_ids(12, 45)[-1] == "num_001" and L.spoken_ids(12, 30)[-1] == "num_001"   # twelve wraps around to one
assert L.spoken_ids(3, 25)[-1] == "num_004" and L.spoken_ids(3, 35)[-1] == "num_004"
for m in range(0, 60, 5):
    L.spoken_ids(7, m)
print("klockan: OK")