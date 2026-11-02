"""Para ihop: match a word to its picture. Pure Python (testable without pygame)."""
import random

from kidsgames.skrivlabbet.content import WORDS


def choices_for(rounds_done):
    """2 choices at first, up to 4 as the child plays more rounds."""
    return 2 + min(2, rounds_done // 2)


def make_round(rounds_done, rng, size=8):
    """size tasks: {"answer": word, "choices": [words], "right": index of the answer}. Early rounds use the short words."""
    n = choices_for(rounds_done)
    pool = [w for w in WORDS if w["level"] == "C1"] if rounds_done == 0 else list(WORDS)
    answers = rng.sample(pool, min(size, len(pool)))
    while len(answers) < size:
        answers.append(rng.choice(WORDS))
    tasks = []
    for ans in answers:
        # distractors start with another letter, so they are easy to tell apart by sight
        others = [w for w in WORDS if w["text"] != ans["text"]]
        rng.shuffle(others)
        ch, used = [], {ans["text"][0]}
        for w in others:                          # every choice starts with a different letter
            if w["text"][0] not in used:
                ch.append(w)
                used.add(w["text"][0])
            if len(ch) == n - 1:
                break
        ch.append(ans)
        rng.shuffle(ch)
        tasks.append({"answer": ans, "choices": ch, "right": ch.index(ans)})
    return tasks