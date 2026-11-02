"""Mönster: look at the row and pick what comes next. Run: python3 -m kidsgames.monster [--window]"""
import math
import random

import pygame

from kidsgames.core.app import LevelSelect, COLORS, WHITE, Game, Reward, Scene, draw_dots, draw_object, main_guard
from kidsgames.core.progress import Progress
from kidsgames.monster import logic

PAL = {"red": (229, 72, 77), "blue": (30, 136, 229), "green": (26, 160, 90), "yellow": (255, 200, 40)}


def draw_shape(surf, shape, color, cx, cy, r):
    col = PAL[color]
    if shape == "circle":
        pygame.draw.circle(surf, col, (cx, cy), r)
    elif shape == "square":
        pygame.draw.rect(surf, col, (cx - r, cy - r, 2 * r, 2 * r), border_radius=int(r * 0.2))
    elif shape == "triangle":
        pygame.draw.polygon(surf, col, [(cx, cy - r), (cx + r, cy + r * 0.85), (cx - r, cy + r * 0.85)])
    else:
        pts = [(cx + (r if i % 2 == 0 else r * 0.45) * math.cos(-math.pi / 2 + i * math.pi / 5),
                cy + (r if i % 2 == 0 else r * 0.45) * math.sin(-math.pi / 2 + i * math.pi / 5)) for i in range(10)]
        pygame.draw.polygon(surf, col, pts)


PER, TOP = 2, 3
LABELS = ["Två i rad", "Tre i rad", "Tre olika", "Fyra i rad"]


def select():
    return LevelSelect("monster", LABELS, PER, Round)


class Round(Scene):
    def __init__(self, level=0):
        self.level = level

    def enter(self, game):
        super().enter(game)
        self.progress = Progress()
        self.rng = random.Random()
        self.tasks = logic.make_tasks(self.level, self.rng)
        self.results, self.index = [], -1
        self.next_task()

    def next_task(self):
        self.index += 1
        if self.index >= len(self.tasks):
            self.progress.finish_round("monster", self.level, PER, TOP)
            self.game.go(Reward(self.results, select))
            return
        self.task = self.tasks[self.index]
        self.state, self.timer, self.wrong, self.bad, self.hint = "ask", 0.0, 0, set(), False
        g = self.game
        n = len(self.task["choices"])
        side = int(g.h * 0.22)
        x0 = g.w / 2 - (n * side + (n - 1) * g.w * 0.04) / 2
        self.cards = [pygame.Rect(int(x0 + i * (side + g.w * 0.04)), int(g.h * 0.64), side, side) for i in range(n)]
        if self.index == 0:
            g.voice.say(["say_what_next"])
        g.redraw = True

    @property
    def animated(self):
        return self.state != "ask" or self.hint

    def submit(self, i):
        if i == self.task["right"]:
            self.results.append(self.wrong == 0)
            self.state, self.timer = "right", 0.0
            self.game.voice.say([self.game.voice.variant("say_correct", self.rng, 8)])
        else:
            self.wrong += 1
            self.bad.add(i)
            self.hint = self.wrong >= 2
            if self.wrong >= 3:
                self.results.append(False)
                self.state, self.timer = "reveal", 0.0
            else:
                self.game.voice.say([self.game.voice.variant("say_retry", self.rng, 4)])

    def event(self, e):
        if self.state == "ask" and e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i, r in enumerate(self.cards):
                if r.collidepoint(e.pos) and i not in self.bad:
                    self.submit(i)

    def update(self, dt):
        if self.state in ("right", "reveal"):
            self.timer += dt
            if self.timer > 1.0 and not self.game.voice.busy:
                self.next_task()

    def draw(self, surf):
        g, t = self.game, self.task
        draw_dots(g, self.results, len(self.tasks))
        n = len(t["shown"]) + 1
        step = min(g.w * 0.88 / n, g.h * 0.2)
        x0 = g.w / 2 - step * n / 2
        cy = int(g.h * 0.33)
        for i, (s, c) in enumerate(t["shown"]):
            draw_shape(surf, s, c, int(x0 + step * (i + 0.5)), cy, int(step * 0.36))
        q = pygame.Rect(0, 0, int(step * 0.8), int(step * 0.8))
        q.center = (int(x0 + step * (n - 0.5)), cy)
        pygame.draw.rect(surf, COLORS["panel"], q, border_radius=16)
        pygame.draw.rect(surf, COLORS["soft"], q, 5, border_radius=16)
        if self.state in ("right", "reveal"):
            draw_shape(surf, t["answer"][0], t["answer"][1], q.centerx, q.centery, int(step * 0.32))
        else:
            g.text("?", q.h * 0.7, COLORS["soft"], center=q.center)
        pulse = int(pygame.time.get_ticks() / 350) % 2 == 0
        for i, r in enumerate(self.cards):
            border = (200, 90, 90) if i in self.bad else COLORS["panel"]
            if self.state in ("right", "reveal") and i == t["right"]:
                border = COLORS["good"]
            elif self.hint and i == t["right"] and pulse:
                border = COLORS["soft"]
            pygame.draw.rect(surf, (80, 85, 130) if i in self.bad else COLORS["panel"], r, border_radius=24)
            pygame.draw.rect(surf, border, r, 7, border_radius=24)
            s, c = t["choices"][i]
            draw_shape(surf, s, c, r.centerx, r.centery, int(r.w * 0.32))
        if self.state == "right":
            draw_object(surf, "star", g.w - int(g.h * 0.14), int(g.h * 0.2), int(g.h * 0.09))


def run(windowed):
    game = Game("Mönster", windowed)
    game.go(select())
    game.run()


if __name__ == "__main__":
    main_guard(run)