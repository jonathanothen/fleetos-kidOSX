"""Skrivlabbet logic without pygame (so it can be tested anywhere)."""
import json
import os
import pwd
import random

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "content.json"), encoding="utf-8") as _f:
    DATA = json.load(_f)

LETTER_ORDER = DATA["letter_order"]
LETTERS = DATA["letters"]
WORDS = DATA["words"]
ROWS = ["qwertyuiopå", "asdfghjklöä", "zxcvbnm"]          # Swedish keyboard, letter rows only
NAME_IDS = {"å": "let_aa", "ä": "let_ae", "ö": "let_oe"}


def letter_name_id(ch):
    """Voice clip with the NAME of the letter (ess, a, å ...), or None if there is none."""
    if ch in NAME_IDS:
        return NAME_IDS[ch]
    return "let_" + ch if "a" <= ch <= "z" else None


def letter_sound_id(ch):
    return LETTERS[ch]["sound"] if ch in LETTERS else letter_name_id(ch)


def unlocked_letters(rounds_done):
    """Letters are introduced gradually: 6 to start with, 3 more after every finished round."""
    return LETTER_ORDER[: min(len(LETTER_ORDER), 6 + 3 * rounds_done)]


def letter_round(rounds_done, rng, size=10):
    """Letters to find. The newest ones come up more often; the same letter never twice in a row."""
    avail = unlocked_letters(rounds_done)
    newest = avail[-3:]
    out = []
    while len(out) < size:
        ch = rng.choice(newest) if rng.random() < 0.5 else rng.choice(avail)
        if not out or ch != out[-1]:
            out.append(ch)
    return out


def child_name(uid=None):
    """First name of the signed-in account (the child's name from the setup wizard); falls back to the user name."""
    try:
        p = pwd.getpwuid(os.getuid() if uid is None else uid)
        first = p.pw_gecos.split(",")[0].split()
        return (first[0] if first else p.pw_name).strip()
    except KeyError:
        return "Barn"


def name_letters(name):
    return [c for c in name.lower() if c.isalpha()]


def word_round(rng, size=8):
    """Short words (C1) first in the round, then the longer ones (C2); half are copied, half written by sound."""
    short = [w for w in WORDS if w["level"] == "C1"]
    longer = [w for w in WORDS if w["level"] != "C1"]
    picks = rng.sample(short, min(3, len(short))) + rng.sample(longer, size - min(3, len(short)))
    return [dict(w, mode="copy" if i < size // 2 else "sound") for i, w in enumerate(picks)]


def key_matches(unicode_char, target):
    return bool(unicode_char) and unicode_char.lower() == target


def clip_ids_used():
    ids = {"say_find_letter", "say_press_letter", "say_type_word", "say_type_name", "say_type_copy",
           "say_letter_next", "say_correct_1", "say_correct_2", "say_correct_3", "say_correct_4",
           "say_retry_1", "say_retry_2", "say_well_done_round", "say_sticker", "say_hello", "say_choose_game"}
    for ch in LETTER_ORDER:
        for cid in (letter_name_id(ch), letter_sound_id(ch)):
            if cid:
                ids.add(cid)
    for w in WORDS:
        ids.add(w["voice"])
    return ids