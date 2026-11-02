"""Mönster: which one comes next? Pure Python."""
SHAPES = ["circle", "square", "triangle", "star"]
COLORS = ["red", "blue", "green", "yellow"]
UNITS = [
    ["a", "b"],                # stage 0: red blue red blue ?
    ["a", "a", "b"],           # stage 1: AAB / ABB
    ["a", "b", "c"],           # stage 2: ABC
    ["a", "b", "a", "c"],      # stage 3: ABAC
]


def make_tasks(stage, rng, size=8):
    stage = min(stage, len(UNITS) - 1)
    tasks = []
    while len(tasks) < size:
        unit = list(rng.choice([UNITS[stage]] + ([["a", "b", "b"]] if stage == 1 else [])))
        names = sorted(set(unit))
        kinds = ["color", "shape"] if stage < 2 else ["color", "shape", "both"]
        kind = rng.choice(kinds)
        if kind == "color":
            sym = dict(zip(names, rng.sample(COLORS, len(names)))); fix = rng.choice(SHAPES)
            item = {n: (fix, sym[n]) for n in names}
        elif kind == "shape":
            sym = dict(zip(names, rng.sample(SHAPES, len(names)))); fix = rng.choice(COLORS)
            item = {n: (sym[n], fix) for n in names}
        else:
            shapes, cols = rng.sample(SHAPES, len(names)), rng.sample(COLORS, len(names))
            item = {n: (shapes[i], cols[i]) for i, n in enumerate(names)}
        length = len(unit) * 2 + (1 if len(unit) < 4 else 0)         # about two repeats are shown, then the question
        seq = [unit[i % len(unit)] for i in range(length + 1)]
        shown, answer = [item[s] for s in seq[:-1]], item[seq[-1]]
        options = [answer] + [item[n] for n in names if item[n] != answer]
        extra = [(s, c) for s in SHAPES for c in COLORS if (s, c) not in options and (kind != "color" or s == answer[0]) and (kind != "shape" or c == answer[1])]
        rng.shuffle(extra)
        while len(options) < 3:
            options.append(extra.pop())
        options = options[:3] if answer in options[:3] else [answer] + options[1:3]
        rng.shuffle(options)
        tasks.append({"shown": shown, "answer": answer, "choices": options, "right": options.index(answer)})
    return tasks