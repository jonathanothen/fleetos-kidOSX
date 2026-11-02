"""Run: python3 tests/test_mattelek.py   (no pygame needed)"""
import os, random, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "rootfs", "overlay", "usr", "share", "kidsos", "games"))
from kidsgames.mattelek import generators as G
from kidsgames.core.progress import Progress


def check_task(t):
    v = t["visual"] if "visual" in t else {}
    if t["kind"] == "equation":
        toks = t["tokens"]
        assert toks.count("_") == 1 and "=" in toks, toks
        # evaluate: substitute the answer and check the equation is true
        s = " ".join(toks).replace("_", str(t["answer"])).replace("=", "==")
        assert eval(s), (toks, t["answer"])
        assert 0 <= t["answer"] <= 20
    for grp in v.get("groups", []):
        assert 0 <= grp.get("ghost_n", 0) <= grp["n"]
    if t["skill"] in ("add_gap", "add_gap20", "friends10"):
        assert sum(g.get("ghost_n", 0) for g in v["groups"]) == t["answer"], t     # the dashed objects ARE the answer
    if t["skill"] == "sub_gap20":
        grp = v["groups"][0]
        total = grp["n"]
        assert grp.get("ghost_n", 0) == t["answer"] or total == t["answer"], t   # dashed ones, or count them all
    if t["skill"] == "friends10":
        s = " ".join(t["tokens"]).replace("_", str(t["answer"]))
        assert "10" in t["tokens"] or sum(int(x) for x in t["tokens"] if x.isdigit()) >= 10
    if t["skill"] == "doubles":
        assert t["answer"] == 2 * int(t["tokens"][0]) and t["tokens"][0] == t["tokens"][2]
    if t["skill"] == "plus10":
        assert "10" in t["tokens"]
    if t["kind"] == "pick":
        sizes = [g["n"] for g in v["groups"]]
        assert 0 <= t["answer"] < len(sizes) and len(set(sizes)) == len(sizes), sizes
        if t["say"][0] == "say_more": assert sizes[t["answer"]] == max(sizes)
        if t["say"][0] == "say_fewer": assert sizes[t["answer"]] == min(sizes)
        if "big_number" in v: assert sizes[t["answer"]] == v["big_number"]
    if t["kind"] == "count":
        assert t["answer"] == v["groups"][0]["n"] and 1 <= t["answer"] <= 10
    if t["kind"] == "tenframe":
        assert t["answer"] + v["filled"] == 10
    if t["kind"] == "numline":
        assert v["numbers"][v["hole"]] == t["answer"] and 0 <= min(v["numbers"]) and max(v["numbers"]) <= 20


def main():
    rng = random.Random(7)
    for s in G.SKILLS:
        for _ in range(500):
            check_task(G.make_task(s, rng))
    # same seed -> same tasks
    a = [t["sig"] for t in G.make_round(["count", "dice"], "dice", random.Random(3))]
    b = [t["sig"] for t in G.make_round(["count", "dice"], "dice", random.Random(3))]
    assert a == b and len(a) == 10
    for i in range(1, len(a)): assert a[i] != a[i - 1], a
    # mastery flow
    p = Progress(path=os.path.join(tempfile.mkdtemp(), "p.json"))
    sk = ["count", "dice", "match"]
    assert p.focus(sk) == (["count"], "count")
    for _ in range(10): p.record("count", True)
    assert p.focus(sk) == (["count", "dice"], "dice")
    for _ in range(10): p.record("dice", i % 2 == 0 and False)      # all wrong -> not mastered
    assert p.focus(sk)[1] == "dice"
    p.save(); assert Progress(path=p.path).mastered("count")
    print("mattelek: OK")


main()