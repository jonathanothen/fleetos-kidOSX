"""Saved progress (no pygame). One JSON file per user; written atomically so a power cut cannot corrupt it."""
import json
import os

DEFAULT_PATH = os.path.join(os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share")),
                            "kidsos", "progress.json")


class Progress:
    def __init__(self, path=DEFAULT_PATH, window=10, needed=8):
        self.path, self.window, self.needed = path, window, needed
        self.data = {"skills": {}, "stickers": []}
        try:
            with open(path, encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                self.data.update(loaded)
        except (OSError, ValueError):
            pass

    def record(self, skill, first_try_ok):
        hist = self.data["skills"].setdefault(skill, [])
        hist.append(bool(first_try_ok))
        del hist[:-self.window]

    def mastered(self, skill):
        hist = self.data["skills"].get(skill, [])
        return len(hist) >= self.window and sum(hist) >= self.needed

    def focus(self, skills):
        """Return (unlocked skills, the skill being learned). The first not yet mastered skill is the focus."""
        for i, s in enumerate(skills):
            if not self.mastered(s):
                return skills[: i + 1], s
        return list(skills), skills[-1]          # everything mastered: keep practising, all of it

    # ---- levels of the simple games (Memory, Klockan, Lyssna, Para ihop, Mönster) ----
    def _game(self, game):
        return self.data.setdefault("games", {}).setdefault(game, {"rounds": 0})

    def unlocked(self, game, per, top):
        """Highest level (0..top) the child has reached. A level opens when the one before it has been played `per` times.
        Saves from the older version (only a round counter) are converted."""
        g = self._game(game)
        if "unlocked" not in g:
            g["unlocked"] = min(top, g.get("rounds", 0) // per)
        return min(top, g["unlocked"])

    def done(self, game, level):
        """How many rounds have been played at this level."""
        return self._game(game).get("done", {}).get(str(level), 0)

    def finish_round(self, game, level, per, top):
        """Count a finished round at `level`, give a sticker and open the next level when this was the highest one reached."""
        g = self._game(game)
        reached = self.unlocked(game, per, top)
        g["rounds"] = g.get("rounds", 0) + 1
        d = g.setdefault("done", {})
        d[str(level)] = d.get(str(level), 0) + 1
        if level == reached and d[str(level)] >= per and level < top:
            g["unlocked"] = level + 1
        self.add_sticker(game)
        self.save()
    def add_sticker(self, name):
        self.data["stickers"].append(name)

    def save(self):
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            tmp = self.path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False)
            os.replace(tmp, self.path)
        except OSError:
            pass                                 # never crash a child's game because the disk is full
