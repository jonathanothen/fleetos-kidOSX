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


def add_gap(rng, top=10):
    """The blank can be the result, the second or the first number, or the sum comes first: 7 = 4 + _."""
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


def _equation(skill, tokens, answer, groups, rng, say, cross=0):
    return {"kind": "equation", "skill": skill, "tokens": tokens, "answer": answer, "say": say,
            "visual": {"groups": [{"n": n, "shown": shown} for n, shown in groups], "obj": _obj(rng),
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
