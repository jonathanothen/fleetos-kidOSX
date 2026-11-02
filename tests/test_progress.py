"""Run: python3 tests/test_progress.py   (no pygame needed)"""
import os, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "rootfs", "overlay", "usr", "share", "kidsos", "games"))
from kidsgames.core.progress import Progress

path = os.path.join(tempfile.mkdtemp(), "p.json")
p = Progress(path=path)
assert p.unlocked("g", 2, 3) == 0 and p.done("g", 0) == 0
p.finish_round("g", 0, 2, 3); assert p.unlocked("g", 2, 3) == 0 and p.done("g", 0) == 1
p.finish_round("g", 0, 2, 3); assert p.unlocked("g", 2, 3) == 1                      # two rounds on level 0 opens level 1
for _ in range(5): p.finish_round("g", 0, 2, 3)                                       # practising an old level changes nothing
assert p.unlocked("g", 2, 3) == 1 and p.done("g", 0) == 7
p.finish_round("g", 1, 2, 3); assert p.unlocked("g", 2, 3) == 1
p.finish_round("g", 1, 2, 3); assert p.unlocked("g", 2, 3) == 2
for lv in (2, 3):
    for _ in range(3): p.finish_round("g", lv, 2, 3)
assert p.unlocked("g", 2, 3) == 3                                                     # never above the top
assert len(p.data["stickers"]) >= 12
assert Progress(path=path).unlocked("g", 2, 3) == 3                                   # survives a restart
old = Progress(path=os.path.join(tempfile.mkdtemp(), "o.json")); old.data["games"] = {"minne": {"rounds": 5}}
assert old.unlocked("minne", 1, 3) == 3                                              # saves from the old round counter
old2 = Progress(path=os.path.join(tempfile.mkdtemp(), "o2.json")); old2.data["games"] = {"minne": {"rounds": 5}}
assert old2.unlocked("minne", 2, 3) == 2
print("progress: OK")