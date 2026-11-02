"""Mattelek: fill in the calculation. Run: python3 -m kidsgames.mattelek  (add --window to test in a window)."""
import json
import os
import random

import pygame

from kidsgames.core.app import COLORS, WHITE, Game, Scene, button, draw_object, main_guard
from kidsgames.core.progress import Progress
from kidsgames.mattelek import generators

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "levels.json"), encoding="utf-8") as _f:
    CFG = json.load(_f)

PIPS = {1: [(1, 1)], 2: [(0, 0), (2, 2)], 3: [(0, 0), (1, 1), (2, 2)], 4: [(0, 0), (2, 0), (0, 2), (2, 2)],
        5: [(0, 0), (2, 0), (1, 1), (0, 2), (2, 2)], 6: [(0, 0), (2, 0), (0, 1), (2, 1), (0, 2), (2, 2)]}
KEYS = {getattr(pygame, "K_%d" % i): i for i in range(10)}
KEYS.update({getattr(pygame, "K_KP%d" % i): i for i in range(10)})
TILE_COLORS = ["pink", "violet", "green", "blue"]


def grid_positions(n, area, per_row=5):
    """Centres and radius for n objects in rows of `per_row`, fitted into the pygame.Rect `area`."""
    rows = max(1, (n + per_row - 1) // per_row)
    cols = min(n, per_row) or 1
    cell = min(area.w / cols, area.h / rows)
    r = int(cell * 0.38)
    pos = []
    for i in range(n):
        row, col = divmod(i, per_row)
        in_row = min(per_row, n - row * per_row)
        x0 = area.centerx - (in_row - 1) * cell / 2
        y0 = area.centery - (rows - 1) * cell / 2
        pos.append((int(x0 + col * cell), int(y0 + row * cell)))
    return pos, r


class Menu(Scene):
    def enter(self, game):
        super().enter(game)
        game.voice.say(["say_hello", "say_choose_game"])
        w, h = game.w, game.h
        self.tiles = []
        tw, th = int(w * 0.36), int(h * 0.5)
        for i, lv in enumerate(CFG["levels"]):
            x = int(w / 2 + (i - 0.5 * (len(CFG["levels"]) - 1)) * (tw + w * 0.04) - tw / 2)
            self.tiles.append((pygame.Rect(x, int(h * 0.3), tw, th), lv, TILE_COLORS[i % 4]))

    def event(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for r, lv, _c in self.tiles:
                if r.collidepoint(e.pos):
                    self.game.go(Round(lv))
        if e.type == pygame.KEYDOWN and e.key in KEYS and KEYS[e.key] < len(self.tiles) + 1 and KEYS[e.key] > 0:
            self.game.go(Round(self.tiles[KEYS[e.key] - 1][1]))

    def draw(self, surf):
        g = self.game
        g.text("Mattelek", g.h * 0.12, COLORS["soft"], center=(g.w // 2, g.h * 0.14))
        for i, (r, lv, c) in enumerate(self.tiles):
            button(g, r, "", COLORS[c])
            g.text(str(i + 1), r.h * 0.45, WHITE, center=(r.centerx, r.y + r.h * 0.38))
            g.text(lv["title"], r.h * 0.12, WHITE, center=(r.centerx, r.y + r.h * 0.78))


class Round(Scene):
    def __init__(self, level):
        self.level = level

    def enter(self, game):
        super().enter(game)
        self.progress = Progress(window=CFG["mastery"]["window"], needed=CFG["mastery"]["needed"])
        skills, focus = self.progress.focus(self.level["skills"])
        self.rng = random.Random()
        self.tasks = generators.make_round(skills, focus, self.rng, CFG["round_size"])
        self.results = []                          # True = right at the first try
        self.index = -1
        self.next_task()

    # ---- flow ----
    def next_task(self):
        self.index += 1
        if self.index >= len(self.tasks):
            self.progress.add_sticker("lv%d" % self.level["id"])
            self.progress.save()
            self.game.go(Reward(self.results))
            return
        self.task = self.tasks[self.index]
        self.group_rects = []
        self.entry, self.wrong, self.state, self.timer, self.hint, self.picked = "", 0, "ask", 0.0, False, None
        self.game.redraw = True
        self.game.voice.say(self.task["say"])
        self.layout()

    def layout(self):
        g = self.game
        self.pad = []
        if self.task["kind"] != "pick":
            n = 11
            bw = min(int(g.h * 0.13), int(g.w / (n + 1)))
            x0 = (g.w - n * bw - (n - 1) * 8) // 2
            y = int(g.h * 0.84)
            for i, label in enumerate(list("1234567890") + ["<"]):
                self.pad.append((pygame.Rect(x0 + i * (bw + 8), y, bw, bw), label))

    def submit(self, value):
        t = self.task
        right = (value == t["answer"])
        if right:
            self.results.append(self.wrong == 0)
            self.progress.record(t["skill"], self.wrong == 0)
            self.state, self.timer = "right", 0.0
            self.game.voice.say(["say_correct_%d" % self.rng.randint(1, 4)])
        else:
            self.wrong += 1
            self.entry, self.picked = "", None
            if self.wrong == 1:
                self.game.voice.say(["say_retry_%d" % self.rng.randint(1, 2)])
            elif self.wrong == 2:
                self.hint = True
                ids = ["say_hint_objects"] + [generators._num(i) for i in range(1, min(t["answer"], 12) + 1)] \
                    if t["kind"] in ("count", "equation", "tenframe") else ["say_retry_2"]
                self.game.voice.say(ids)
            else:
                self.results.append(False)
                self.progress.record(t["skill"], False)
                self.hint, self.state, self.timer = True, "reveal", 0.0
                self.game.voice.say([generators._num(t["answer"])] if t["kind"] != "pick" else [])

    def press_digit(self, d):
        if self.state != "ask" or self.task["kind"] == "pick":
            return
        self.entry = (self.entry + str(d))[-2:]
        want = str(self.task["answer"])
        if len(self.entry) >= len(want):
            self.submit(int(self.entry))

    # ---- events ----
    def event(self, e):
        if self.state != "ask":
            return
        if e.type == pygame.KEYDOWN:
            if e.key in KEYS:
                if self.task["kind"] == "pick":
                    if 1 <= KEYS[e.key] <= len(self.task["visual"]["groups"]):
                        self.picked = KEYS[e.key] - 1
                        self.submit(self.picked)
                else:
                    self.press_digit(KEYS[e.key])
            elif e.key == pygame.K_BACKSPACE:
                self.entry = self.entry[:-1]
            elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and self.entry:
                self.submit(int(self.entry))
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if self.task["kind"] == "pick":
                for i, r in enumerate(self.group_rects):
                    if r.collidepoint(e.pos):
                        self.picked = i
                        self.submit(i)
            else:
                for r, label in self.pad:
                    if r.collidepoint(e.pos):
                        if label == "<":
                            self.entry = self.entry[:-1]
                        else:
                            self.press_digit(label)

    @property
    def animated(self):
        return self.state in ("right", "reveal")

    def update(self, dt):
        if self.state in ("right", "reveal"):
            self.timer += dt
            wait = 0.9 if self.state == "right" else 2.2
            if self.timer > wait and not self.game.voice.busy:
                self.next_task()

    # ---- drawing ----
    def draw(self, surf):
        g, t = self.game, self.task
        for i in range(len(self.tasks)):           # progress dots
            col = COLORS["good"] if i < len(self.results) and self.results[i] else (
                COLORS["soft"] if i < len(self.results) else COLORS["panel"])
            pygame.draw.circle(surf, col, (int(g.w * 0.05 + i * g.w * 0.03), int(g.h * 0.05)), int(g.h * 0.016))
        area = pygame.Rect(int(g.w * 0.06), int(g.h * 0.1), int(g.w * 0.88), int(g.h * 0.44))
        getattr(self, "draw_" + t["kind"])(surf, area)
        if t["kind"] == "equation":
            self.draw_tokens(surf)
        for r, label in self.pad:
            button(g, r, label, COLORS["blue"] if label != "<" else COLORS["orange"], size=r.h * 0.6)
        if self.state == "right":
            draw_object(surf, "star", g.w // 2, int(g.h * 0.55), int(g.h * 0.1))

    def draw_groups(self, surf, area, clickable=False):
        v, g = self.task["visual"], self.game
        groups = v["groups"]
        k = len(groups)
        self.group_rects = []
        for i, grp in enumerate(groups):
            cell = pygame.Rect(area.x + i * area.w // k, area.y, area.w // k, area.h).inflate(-g.w * 0.03, 0)
            self.group_rects.append(cell)
            border = COLORS["soft"] if self.picked == i else COLORS["panel"]
            pygame.draw.rect(surf, COLORS["panel"], cell, border_radius=24)
            if self.state == "reveal" and clickable and i == self.task["answer"]:
                border = COLORS["good"]
            if clickable:
                pygame.draw.rect(surf, border, cell, 6, border_radius=24)
                g.text(str(i + 1), g.h * 0.05, (150, 160, 210), topleft=(cell.x + 14, cell.y + 6))
            if grp["shown"] or self.hint:
                pos, r = grid_positions(grp["n"], cell.inflate(-20, -50))
                for j, (x, y) in enumerate(pos):
                    crossed = self.task["visual"].get("cross", 0) and j >= grp["n"] - v["cross"]
                    draw_object(surf, v["obj"], x, y, r, crossed=bool(crossed))
                    if self.hint and self.task["kind"] in ("count",):
                        g.text(str(j + 1), r * 0.9, WHITE, center=(x, y + r * 1.25))
            else:
                g.text("?", cell.h * 0.6, COLORS["soft"], center=cell.center)

    def draw_count(self, surf, area):
        v = self.task["visual"]
        if v.get("dice"):
            n = v["groups"][0]["n"]
            side = int(area.h * 0.8)
            face = pygame.Rect(0, 0, side, side)
            face.center = area.center
            pygame.draw.rect(surf, WHITE, face, border_radius=side // 6)
            for cx, cy in PIPS[n]:
                pygame.draw.circle(surf, (40, 40, 60), (face.x + int(side * (0.22 + 0.28 * cx)),
                                                          face.y + int(side * (0.22 + 0.28 * cy))), side // 11)
        else:
            self.draw_groups(surf, area)
            self.draw_entry_box(surf, pygame.Rect(0, int(self.game.h * 0.58), self.game.w, int(self.game.h * 0.18)))
        if v.get("dice"):
            self.draw_entry_box(surf, pygame.Rect(0, int(self.game.h * 0.58), self.game.w, int(self.game.h * 0.18)))

    def draw_pick(self, surf, area):
        v, g = self.task["visual"], self.game
        self.draw_groups(surf, area, clickable=True)
        if "big_number" in v:
            g.text(str(v["big_number"]), g.h * 0.2, COLORS["soft"], center=(g.w // 2, int(g.h * 0.7)))
        elif self.task["say"][0] in ("say_more", "say_fewer"):
            g.text("fler" if self.task["say"][0] == "say_more" else "färre", g.h * 0.16, COLORS["soft"],
                   center=(g.w // 2, int(g.h * 0.7)))

    def draw_tenframe(self, surf, area):
        v, g = self.task["visual"], self.game
        cell = int(min(area.w / 5, area.h / 2) * 0.9)
        x0, y0 = area.centerx - cell * 5 // 2, area.centery - cell
        for i in range(10):
            r = pygame.Rect(x0 + (i % 5) * cell, y0 + (i // 5) * cell, cell, cell)
            pygame.draw.rect(surf, COLORS["panel"], r.inflate(-6, -6), border_radius=10)
            pygame.draw.rect(surf, (150, 160, 210), r.inflate(-6, -6), 3, border_radius=10)
            if i < v["filled"]:
                draw_object(surf, v["obj"], r.centerx, r.centery, int(cell * 0.32))
        self.draw_entry_box(surf, pygame.Rect(0, int(g.h * 0.58), g.w, int(g.h * 0.18)))

    def draw_numline(self, surf, area):
        v, g = self.task["visual"], self.game
        nums = v["numbers"]
        y = area.centery
        step = area.w / (len(nums) + 0.5)
        pygame.draw.line(surf, WHITE, (area.x, y), (area.right, y), 6)
        for i, n in enumerate(nums):
            x = int(area.x + step * (i + 0.75))
            pygame.draw.line(surf, WHITE, (x, y - 24), (x, y + 24), 6)
            if i == v["hole"] and self.state != "reveal":
                box = pygame.Rect(0, 0, int(step * 0.7), int(step * 0.7))
                box.center = (x, y - int(step * 0.55))
                pygame.draw.rect(surf, COLORS["panel"], box, border_radius=14)
                pygame.draw.rect(surf, COLORS["soft"], box, 5, border_radius=14)
                g.text(self.entry or "?", box.h * 0.6, COLORS["soft"], center=box.center)
            else:
                g.text(str(n), step * 0.45, COLORS["soft"] if i == v["hole"] else WHITE,
                       center=(x, y - int(step * 0.55)))

    def draw_equation(self, surf, area):
        self.draw_groups(surf, area)

    def draw_tokens(self, surf):
        g = self.game
        size = g.h * 0.16
        gap = size * 0.5
        parts = []
        for tok in self.task["tokens"]:
            if tok == "_":
                parts.append(("box", size * 1.2))
            else:
                parts.append((tok, g.fonts.get(size).size(tok)[0]))
        total = sum(w for _, w in parts) + gap * (len(parts) - 1)
        x = (g.w - total) / 2
        cy = int(g.h * 0.67)
        for tok, w in parts:
            if tok == "box":
                box = pygame.Rect(int(x), int(cy - size * 0.55), int(w), int(size * 1.1))
                right = self.state in ("right", "reveal")
                pygame.draw.rect(surf, COLORS["panel"], box, border_radius=16)
                pygame.draw.rect(surf, COLORS["good"] if right else COLORS["soft"], box, 6, border_radius=16)
                shown = str(self.task["answer"]) if right else self.entry
                g.text(shown, size, COLORS["good"] if right else WHITE, center=box.center)
            else:
                g.text(tok, size, WHITE, center=(int(x + w / 2), cy))
            x += w + gap

    def draw_entry_box(self, surf, band):
        g = self.game
        size = g.h * 0.14
        box = pygame.Rect(0, 0, int(size * 1.6), int(size * 1.15))
        box.center = band.center
        right = self.state in ("right", "reveal")
        pygame.draw.rect(surf, COLORS["panel"], box, border_radius=16)
        pygame.draw.rect(surf, COLORS["good"] if right else COLORS["soft"], box, 6, border_radius=16)
        shown = str(self.task["answer"]) if right else self.entry
        g.text(shown, size, COLORS["good"] if right else WHITE, center=box.center)


class Reward(Scene):
    animated = True

    def __init__(self, results):
        self.results = results

    def enter(self, game):
        super().enter(game)
        self.t = 0.0
        game.voice.say(["say_well_done_round", "say_sticker"])

    def update(self, dt):
        self.t += dt

    def event(self, e):
        if self.t > 2.0 and e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            self.game.go(Menu())

    def draw(self, surf):
        g = self.game
        good = sum(self.results)
        draw_object(surf, "star", g.w // 2, int(g.h * 0.42), int(g.h * (0.22 + 0.01 * (self.t % 1.0))))
        g.text("Bra jobbat!", g.h * 0.12, COLORS["soft"], center=(g.w // 2, int(g.h * 0.8)))
        g.text("%d av %d direkt" % (good, len(self.results)), g.h * 0.06, WHITE, center=(g.w // 2, int(g.h * 0.9)))


def run(windowed):
    game = Game("Mattelek", windowed)
    game.go(Menu())
    game.run()


if __name__ == "__main__":
    main_guard(run)
