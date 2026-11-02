"""Lyssna och peka: hear a word, tap the right picture. Run: python3 -m kidsgames.lyssna [--window]"""
import random

import pygame

from kidsgames.core.app import LevelSelect, COLORS, WHITE, Game, Reward, Scene, draw_dots, draw_object, main_guard
from kidsgames.core.progress import Progress
from kidsgames.parihop import logic
from kidsgames.parihop.main import draw_speaker
from kidsgames.skrivlabbet.main import picture


PER, TOP = 2, 2
LABELS = ["2 bilder", "3 bilder", "4 bilder"]


def select():
    return LevelSelect("lyssna", LABELS, PER, Round)


class Round(Scene):
    def __init__(self, level=0):
        self.level = level

    def enter(self, game):
        super().enter(game)
        self.progress = Progress()
        self.rng = random.Random()
        self.tasks = logic.make_round(self.level * 2, self.rng)       # 2 pictures first, up to 4 later
        self.results, self.index = [], -1
        self.next_task()

    def next_task(self):
        self.index += 1
        if self.index >= len(self.tasks):
            self.progress.finish_round("lyssna", self.level, PER, TOP)
            self.game.go(Reward(self.results, select))
            return
        self.task = self.tasks[self.index]
        self.state, self.timer, self.wrong, self.bad, self.hint = "ask", 0.0, 0, set(), False
        g, n = self.game, len(self.task["choices"])
        side = int(min(g.h * 0.36, (g.w * 0.92 - (n - 1) * g.w * 0.03) / n))
        x0 = g.w / 2 - (n * side + (n - 1) * g.w * 0.03) / 2
        self.cards = [pygame.Rect(int(x0 + i * (side + g.w * 0.03)), int(g.h * 0.42), side, side) for i in range(n)]
        self.ear = pygame.Rect(0, int(g.h * 0.1), int(g.h * 0.2), int(g.h * 0.2))
        self.ear.centerx = g.w // 2
        g.voice.say(["say_find_letter", self.task["answer"]["voice"]])
        g.redraw = True

    @property
    def animated(self):
        return self.state != "ask" or self.hint

    def submit(self, i):
        if i == self.task["right"]:
            self.results.append(self.wrong == 0)
            self.state, self.timer = "right", 0.0
            self.game.voice.say([self.task["answer"]["voice"], self.game.voice.variant("say_correct", self.rng, 8)])
        else:
            self.wrong += 1
            self.bad.add(i)
            self.hint = self.wrong >= 2
            if self.wrong >= 3:
                self.results.append(False)
                self.state, self.timer = "reveal", 0.0
                self.game.voice.say([self.task["answer"]["voice"]])
            else:
                self.game.voice.say([self.game.voice.variant("say_retry", self.rng, 4), self.task["answer"]["voice"]])

    def event(self, e):
        if self.state == "ask" and e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if self.ear.collidepoint(e.pos):
                self.game.voice.say(["say_find_letter", self.task["answer"]["voice"]])      # hear it again
                return
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
        pygame.draw.rect(surf, COLORS["violet"], self.ear, border_radius=int(self.ear.h * 0.3))
        draw_speaker(surf, self.ear.centerx - 8, self.ear.centery, self.ear.h * 0.3, WHITE)
        pulse = int(pygame.time.get_ticks() / 350) % 2 == 0
        for i, r in enumerate(self.cards):
            border = COLORS["panel"]
            if i in self.bad:
                border = (200, 90, 90)
            elif self.state in ("right", "reveal") and i == t["right"]:
                border = COLORS["good"]
            elif self.hint and i == t["right"] and pulse:
                border = COLORS["soft"]
            pygame.draw.rect(surf, (150, 150, 165) if i in self.bad else WHITE, r, border_radius=24)
            pygame.draw.rect(surf, border, r, 8, border_radius=24)
            pic = picture(t["choices"][i]["pic"], int(r.w * 0.82))
            if pic:
                surf.blit(pic, pic.get_rect(center=r.center))
        if self.state == "right":
            draw_object(surf, "star", g.w - int(g.h * 0.14), int(g.h * 0.25), int(g.h * 0.09))


def run(windowed):
    game = Game("Lyssna och peka", windowed)
    game.go(select())
    game.run()


if __name__ == "__main__":
    main_guard(run)