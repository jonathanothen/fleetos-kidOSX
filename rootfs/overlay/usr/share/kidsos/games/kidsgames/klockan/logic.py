"""Klockan: read an analog clock. Pure Python."""
MINUTES = [[0], [0, 30], [0, 15, 30, 45], list(range(0, 60, 5))]      # allowed minutes per difficulty stage


def fmt(h, m):
    return "%d:%02d" % (h, m)


def hand_angles(h, m):
    """Angles in degrees clockwise from 12 o'clock: (hour hand, minute hand)."""
    return ((h % 12) + m / 60.0) * 30.0, m * 6.0


PARTS = {5: "say_clock_fem_over", 10: "say_clock_tio_over", 15: "say_clock_kvart_over", 20: "say_clock_tjugo_over",
         25: "say_clock_fem_i_halv", 30: "say_clock_halv", 35: "say_clock_fem_over_halv", 40: "say_clock_tjugo_i",
         45: "say_clock_kvart_i", 50: "say_clock_tio_i", 55: "say_clock_fem_i"}


def spoken_ids(h, m):
    """Voice clips that say the time like a Swede does: 3:30 = "halv fyra", 3:45 = "kvart i fyra"."""
    nxt = h % 12 + 1
    if m == 0:
        return ["say_clock_is", "num_%03d" % h]
    hour = nxt if m >= 25 else h                   # from "fem i halv" the next hour is named
    return ["say_clock_is", PARTS[m], "num_%03d" % hour]


def make_tasks(stage, rng, size=8):
    stage = min(stage, len(MINUTES) - 1)
    mins = MINUTES[stage]
    n_choices = 3 if stage < 3 else 4
    tasks, last = [], None
    while len(tasks) < size:
        h, m = rng.randint(1, 12), rng.choice(mins)
        if (h, m) == last:
            continue
        wrong = set()
        while len(wrong) < n_choices - 1:
            if rng.random() < 0.5:
                cand = (rng.randint(1, 12), m)                    # another hour, same minutes
            else:
                cand = (h, rng.choice(mins if len(mins) > 1 else [0]))   # same hour, other minutes
                if len(mins) == 1:
                    cand = (rng.randint(1, 12), 0)
            if cand != (h, m):
                wrong.add(cand)
        choices = [(h, m)] + sorted(wrong)
        rng.shuffle(choices)
        tasks.append({"h": h, "m": m, "choices": choices, "right": choices.index((h, m))})
        last = (h, m)
    return tasks