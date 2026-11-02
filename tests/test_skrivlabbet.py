"""Run: python3 tests/test_skrivlabbet.py   (no pygame needed)"""
import os, random, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "rootfs", "overlay", "usr", "share", "kidsos", "games"))
from kidsgames.skrivlabbet import content as C

games = os.path.join(os.path.dirname(__file__), "..", "rootfs", "overlay", "usr", "share", "kidsos", "games", "assets")
voices = {f[:-4] for f in os.listdir(os.path.join(games, "voices", "sv"))}
images = {f[:-4] for f in os.listdir(os.path.join(games, "images"))}

assert len(set(C.LETTER_ORDER)) == len(C.LETTER_ORDER)
for ch in C.LETTER_ORDER:
    assert ch in C.LETTERS, ch                      # every taught letter has a sound clip and a word
    assert C.letter_sound_id(ch) in voices, ch
    assert C.letter_name_id(ch) in voices, ch
    p = C.LETTERS[ch]["pic"]
    assert p is None or p in images, p
for w in C.WORDS:
    assert w["voice"] in voices and w["pic"] in images, w
    assert all(c.isalpha() for c in w["text"]), w
    assert all(ch in C.LETTERS or ch in "wq" for ch in w["text"]), w   # letters the keyboard shows
missing = C.clip_ids_used() - voices
assert not missing, missing
# a keyboard key exists for every letter in every word
keys = set("".join(C.ROWS))
for w in C.WORDS:
    assert set(w["text"]) <= keys, w
assert C.unlocked_letters(0) == C.LETTER_ORDER[:6] and len(C.unlocked_letters(99)) == len(C.LETTER_ORDER)
r = C.letter_round(0, random.Random(1))
assert len(r) == 10 and set(r) <= set(C.unlocked_letters(0)) and all(a != b for a, b in zip(r, r[1:])), r
wr = C.word_round(random.Random(2))
assert len(wr) == 8 and len({w["text"] for w in wr}) == 8 and {w["mode"] for w in wr} == {"copy", "sound"}
assert C.name_letters("Hans Othén") == list("hansothén") and C.key_matches("A", "a") and not C.key_matches("", "a")
print("skrivlabbet:", len(C.WORDS), "words,", len(C.LETTERS), "letters: OK; name here:", C.child_name())