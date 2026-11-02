"""Task generators for Mattelek. Pure Python (no pygame) so they can be tested anywhere.

A task is a plain dict:
  skill    name of the skill (see levels.json)
  kind     how the screen shows it: count | pick | numline | tenframe | equation
  say      voice clip ids spoken when the task appears
  answer   int (typed answer) or int index of the right group (pick tasks)
  tokens   equation as list of strings, "_" is the blank (equation tasks)
  visual   what is drawn above the equation / question
  sig      short string that identifies the task (to avoid repeating the same one twice in a row)
Every random choice goes through the rng that is passed in, so a seed gives the same tasks.
"""
import random

OBJECTS = ("ball", "star", "apple")


def _num(n):
    return "num_%03d" % n


def _obj(rng):
    return rng.choice(OBJECTS)


def count(rng, lo=1, hi=10, dice=False):
    n = rng.randint(lo, hi)
    vis = {"groups": [{"n": n, "shown": True}], "obj": _obj(rng)}
    if dice and n <= 6:
        vis["dice"] = True
    return {"kind": "count", "answer": n, "visual": vis, "say": ["say_how_many"],
            "sig": "count%d%s" % (n, "d" if vis.get("dice") else "")}


def dice(rng):
    return dict(count(rng, 1, 6, dice=True), skill="dice")


def match(rng):
    """Say a number; pick the group that has that many objects."""
    n = rng.randint(1, 9)
    others = rng.sample([x for x in range(1, 11) if x != n], 2)
    sizes = others + [n]
    rng.shuffle(sizes)
    obj = _obj(rng)
    return {"kind": "pick", "answer": sizes.index(n), "say": [_num(n)],
            "visual": {"groups": [{"n": s, "shown": True} for s in sizes], "obj": obj, "big_number": n},
            "sig": "match%d-%s" % (n, "".join(map(str, sizes)))}


def more(rng):
    """Which group has more (or fewer) objects?"""
    a, b = rng.sample(range(1, 11), 2)
    want_more = rng.random() < 0.7
    right = 0 if (a > b) == want_more else 1
    return {"kind": "pick", "answer": right, "say": ["say_more" if want_more else "say_fewer"],
            "visual": {"groups": [{"n": a, "shown": True}, {"n": b, "shown": True}], "obj": _obj(rng)},
            "sig": "more%d-%d-%s" % (a, b, want_more)}


def numline(rng):
    """A short stretch of the number line with one number missing: What is missing?"""
    start = rng.randint(0, 14)
    length = 6
    hole = rng.randint(1, length - 2)
    nums = list(range(start, start + length))
    return {"kind": "numline", "answer": nums[hole], "say": ["say_missing"],
            "visual": {"numbers": nums, "hole": hole},
            "sig": "nl%d-%d" % (start, hole)}


def tenframe(rng):
    k = rng.randint(0, 9)
    return {"kind": "tenframe", "answer": 10 - k, "say": ["say_ten_frame"],
            "visual": {"filled": k, "obj": _obj(rng)},
            "sig": "tf%d" % k}


def add_res(rng, top=10):
    a = rng.randint(1, top - 1)
    b = rng.randint(1, top - a)
    return _equation("add_res", ["%d" % a, "+", "%d" % b, "=", "_"], a + b, [(a, True), (b, True)], rng,
                     [_num(a), "say_op_plus", _num(b), "say_op_equals"])


def sub_res(rng, top=10):
    a = rng.randint(2, top)
    b = rng.randint(1, a - 1)
    return _equation("sub_res", ["%d" % a, "-", "%d" % b, "=", "_"], a - b, [(a, True)], rng,
                     [_num(a), "say_op_minus", _num(b), "say_op_equals"], cross=b)


def add_gap(rng, top=10, total=None):
    """The blank can be the result, the second or the first number, or the sum comes first: 7 = 4 + _.
    total=10 gives the number friends of ten (4 + _ = 10)."""
    if total:
        a = rng.randint(1, total - 1)
        b = total - a
    else:
        a = rng.randint(1, top - 1)
        b = rng.randint(1, top - a)
    c = a + b
    form = rng.choice(("b", "a", "rev_b", "rev_a"))
    if form == "b":
        toks, ans, groups = ["%d" % a, "+", "_", "=", "%d" % c], b, [(a, True), (b, False)]
    elif form == "a":
        toks, ans, groups = ["_", "+", "%d" % b, "=", "%d" % c], a, [(a, False), (b, True)]
    elif form == "rev_b":
        toks, ans, groups = ["%d" % c, "=", "%d" % a, "+", "_"], b, [(a, True), (b, False)]
    else:
        toks, ans, groups = ["%d" % c, "=", "_", "+", "%d" % b], a, [(a, False), (b, True)]
    return _equation("add_gap", toks, ans, groups, rng, ["say_fill_missing"])


def sub_gap(rng, top=20):
    """a - _ = c, _ - b = c, and the same with the result first (c = a - _)."""
    a = rng.randint(2, top)
    b = rng.randint(1, a - 1)
    c = a - b
    form = rng.choice(("b", "a", "rev_b", "rev_a"))
    if form == "b":
        toks, ans = ["%d" % a, "-", "_", "=", "%d" % c], b
    elif form == "a":
        toks, ans = ["_", "-", "%d" % b, "=", "%d" % c], a
    elif form == "rev_b":
        toks, ans = ["%d" % c, "=", "%d" % a, "-", "_"], b
    else:
        toks, ans = ["%d" % c, "=", "_", "-", "%d" % b], a
    # Take away an unknown amount: a objects, b of them dashed (to count). Unknown start: c left + b crossed out.
    if form in ("b", "rev_b"):
        groups = [{"n": a, "shown": True, "ghost_n": b}]
        cross = 0
    else:
        groups = [{"n": a, "shown": True, "ghost_n": 0}]
        cross = b
    return _equation("sub_gap", toks, ans, groups, rng, ["say_fill_missing"], cross=cross)


def doubles(rng):
    a = rng.randint(1, 10)
    return _equation("doubles", ["%d" % a, "+", "%d" % a, "=", "_"], 2 * a, [(a, True), (a, True)], rng,
                     [_num(a), "say_op_plus", _num(a), "say_op_equals"])


def plus10(rng):
    a = rng.randint(1, 10)
    toks = ["%d" % a, "+", "10", "=", "_"] if rng.random() < 0.5 else ["10", "+", "%d" % a, "=", "_"]
    first, second = (a, 10) if toks[0] != "10" else (10, a)
    return _equation("plus10", toks, a + 10, [(first, True), (second, True)], rng,
                     [_num(first), "say_op_plus", _num(second), "say_op_equals"])


def _group(n, known):
    """An unknown number is drawn as n dashed outlines the child counts (never just a question mark)."""
    return {"n": n, "shown": True, "ghost_n": 0 if known else n}


def _equation(skill, tokens, answer, groups, rng, say, cross=0):
    return {"kind": "equation", "skill": skill, "tokens": tokens, "answer": answer, "say": say,
            "visual": {"groups": [g if isinstance(g, dict) else _group(*g) for g in groups], "obj": _obj(rng),
                       "cross": cross},
            "sig": skill + "".join(tokens)}


SKILLS = {
    "count": lambda rng: dict(count(rng), skill="count"),
    "dice": dice,
    "match": lambda rng: dict(match(rng), skill="match"),
    "more": lambda rng: dict(more(rng), skill="more"),
    "numline": lambda rng: dict(numline(rng), skill="numline"),
    "tenframe": lambda rng: dict(tenframe(rng), skill="tenframe"),
    "add_res": add_res,
    "sub_res": sub_res,
    "add_gap": add_gap,
    # level 2: up to 20
    "friends10": lambda rng: dict(add_gap(rng, total=10), skill="friends10"),
    "doubles": doubles,
    "add20": lambda rng: dict(add_res(rng, top=20), skill="add20"),
    "sub20": lambda rng: dict(sub_res(rng, top=20), skill="sub20"),
    "plus10": plus10,
    "add_gap20": lambda rng: dict(add_gap(rng, top=20), skill="add_gap20"),
    "sub_gap20": lambda rng: dict(sub_gap(rng, 20), skill="sub_gap20"),
}


def make_task(skill, rng):
    t = SKILLS[skill](rng)
    t["skill"] = skill
    return t


def make_round(skills, focus, rng, size=10, focus_share=0.7):
    """`skills` = the skills unlocked so far, `focus` = the one being learned now (mostly that one)."""
    tasks, last = [], None
    for _ in range(size):
        for _try in range(20):                    # avoid the exact same task twice in a row
            s = focus if (rng.random() < focus_share or len(skills) == 1) else rng.choice(skills)
            t = make_task(s, rng)
            if t["sig"] != last:
                break
        last = t["sig"]
        tasks.append(t)
    return tasks


def answer_text(task):
    if task["kind"] == "pick":
        return str(task["answer"] + 1)
    return str(task["answer"])


if __name__ == "__main__":
    r = random.Random(1)
    for s in SKILLS:
        print(s, make_task(s, r)["sig"])
