"""Klockan: what time is it? Pick the right digital time for the clock. Run: python3 -m kidsgames.klockan [--window]"""
import math
import random

import pygame

from kidsgames.core.app import LevelSelect, COLORS, WHITE, Game, Reward, Scene, button, draw_dots, draw_object, main_guard
from kidsgames.core.progress import Progress
from kidsgames.klockan import logic

COLS = ["blue", "violet", "orange", "green"]


PER, TOP = 2, 3
LABELS = ["Hela timmar", "Halvtimme", "Kvart", "Fem minuter"]


def select():
    return LevelSelect("klockan", LABELS, PER, Round)


class Round(Scene):
    def __init__(self, level=0):
        self.level = level

    def enter(self, game):
        super().enter(game)
        self.progress = Progress()
        self.stage = self.level
        self.rng = random.Random()
        self.tasks = logic.make_tasks(self.stage, self.rng)
        self.results, self.index = [], -1
        self.next_task()

    def next_task(self):
        self.index += 1
        if self.index >= len(self.tasks):
            self.progress.finish_round("klockan", self.level, PER, TOP)
            self.game.go(Reward(self.results, select))
            return
        self.task = self.tasks[self.index]
        self.state, self.timer, self.wrong, self.bad, self.hint = "ask", 0.0, 0, set(), False
        n = len(self.task["choices"])
        g = self.game
        bw = int(min(g.w * 0.2, (g.w * 0.9 - (n - 1) * g.w * 0.02) / n))
        x0 = g.w / 2 - (n * bw + (n - 1) * g.w * 0.02) / 2
        g.voice.say(["say_what_time"])
        self.btns = [pygame.Rect(int(x0 + i * (bw + g.w * 0.02)), int(g.h * 0.78), bw, int(g.h * 0.16)) for i in range(n)]
        g.redraw = True

    @property
    def animated(self):
        return self.state != "ask" or self.hint

    def submit(self, i):
        t = self.task
        if i == t["right"]:
            self.results.append(self.wrong == 0)
            self.state, self.timer = "right", 0.0
            ids = logic.spoken_ids(t["h"], t["m"]) + [self.game.voice.variant("say_correct", self.rng, 8)]
            self.game.voice.say(ids)
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
            for i, r in enumerate(self.btns):
                if r.collidepoint(e.pos) and i not in self.bad:
                    self.submit(i)

    def update(self, dt):
        if self.state in ("right", "reveal"):
            self.timer += dt
            if self.timer > 1.0 and not self.game.voice.busy:
                self.next_task()

    def draw_clock(self, surf, cx, cy, r):
        g, t = self.game, self.task
        pygame.draw.circle(surf, WHITE, (cx, cy), r)
        pygame.draw.circle(surf, COLORS["soft"], (cx, cy), r, int(r * 0.06))
        for k in range(60):
            a = math.radians(k * 6)
            long_ = k % 5 == 0
            r1, r2 = r * (0.86 if long_ else 0.92), r * 0.96
            pygame.draw.line(surf, (60, 50, 90), (cx + r1 * math.sin(a), cy - r1 * math.cos(a)),
                             (cx + r2 * math.sin(a), cy - r2 * math.cos(a)), 4 if long_ else 2)
        for hnum in range(1, 13):
            a = math.radians(hnum * 30)
            g.text(str(hnum), r * 0.2, (40, 30, 70), center=(cx + r * 0.7 * math.sin(a), cy - r * 0.7 * math.cos(a)))
        ha, ma = logic.hand_angles(t["h"], t["m"])
        for ang, length, width, col in ((ha, 0.5, 0.07, (40, 30, 70)), (ma, 0.78, 0.045, (229, 72, 77))):
            a = math.radians(ang)
            pygame.draw.line(surf, col, (cx, cy), (cx + r * length * math.sin(a), cy - r * length * math.cos(a)), int(r * width))
        pygame.draw.circle(surf, (40, 30, 70), (cx, cy), int(r * 0.06))

    def draw(self, surf):
        g, t = self.game, self.task
        draw_dots(g, self.results, len(self.tasks))
        g.text("Vad är klockan?", g.h * 0.07, COLORS["soft"], center=(g.w // 2, int(g.h * 0.12)))
        self.draw_clock(surf, g.w // 2, int(g.h * 0.43), int(g.h * 0.28))
        pulse = int(pygame.time.get_ticks() / 350) % 2 == 0
        for i, r in enumerate(self.btns):
            h, m = t["choices"][i]
            col = COLORS[COLS[i % 4]]
            if i in self.bad:
                col = (110, 110, 140)
            if self.state in ("right", "reveal") and i == t["right"]:
                col = COLORS["good"]
            elif self.hint and i == t["right"] and pulse:
                col = COLORS["soft"]
            button(g, r, logic.fmt(h, m), col, size=r.h * 0.6, text_color=(30, 30, 50) if col == COLORS["soft"] else WHITE)
        if self.state == "right":
            draw_object(surf, "star", g.w - int(g.h * 0.14), int(g.h * 0.3), int(g.h * 0.09))


def run(windowed):
    game = Game("Klockan", windowed)
    game.go(select())
    game.run()


if __name__ == "__main__":
    main_guard(run)