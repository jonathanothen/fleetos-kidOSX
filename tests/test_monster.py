"""Run: python3 tests/test_monster.py   (no pygame needed)"""
import os, random, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "rootfs", "overlay", "usr", "share", "kidsos", "games"))
from kidsgames.monster import logic as L
for stage in range(4):
    for seed in range(200):
        for t in L.make_tasks(stage, random.Random(seed)):
            assert len(t["choices"]) == 3 and len(set(t["choices"])) == 3, t
            assert t["choices"][t["right"]] == t["answer"]
            unit = L.UNITS[min(stage, 3)]
            assert len(t["shown"]) >= len(unit) * 2, t
            # the answer really continues the row: it equals the item one full unit before it (period check)
            full = t["shown"] + [t["answer"]]
            ok = any(all(full[i] == full[i % p] for i in range(len(full))) for p in (2, 3, 4))
            assert ok, (stage, full)
print("monster: OK")