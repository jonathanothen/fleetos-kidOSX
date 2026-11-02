"""Memory (the game folder is called minne): turn cards, match a picture with its word. Pure Python."""
from kidsgames.skrivlabbet.content import WORDS

PAIRS = [3, 4, 6, 8]            # per difficulty stage: 6, 8, 12 and 16 cards
COLS = {3: 3, 4: 4, 6: 4, 8: 4}


def make_board(stage, rng):
    n = PAIRS[min(stage, len(PAIRS) - 1)]
    pool = [w for w in WORDS if w["level"] == "C1"] if stage == 0 else list(WORDS)
    picks, firsts = [], set()
    for w in rng.sample(pool, len(pool)):            # different first letters: easier to tell the words apart
        if w["text"][0] not in firsts:
            picks.append(w)
            firsts.add(w["text"][0])
        if len(picks) == n:
            break
    cards = []
    for i, w in enumerate(picks):
        cards.append({"pair": i, "kind": "pic", "word": w})
        cards.append({"pair": i, "kind": "word", "word": w})
    rng.shuffle(cards)
    return cards


def is_match(a, b):
    return a is not b and a["pair"] == b["pair"] and a["kind"] != b["kind"]