"""Memory (the folder is still called minne): turn two cards; a picture and its word belong together. Run: python3 -m kidsgames.minne [--window]"""
import random

import pygame

from kidsgames.core.app import LevelSelect, COLORS, WHITE, Game, Reward, Scene, draw_dots, main_guard
from kidsgames.core.progress import Progress
from kidsgames.minne import logic
from kidsgames.skrivlabbet.main import picture

BACK = (92, 107, 192)


PER, TOP = 1, 3
LABELS = ["6 kort", "8 kort", "12 kort", "16 kort"]


def select():
    return LevelSelect("minne", LABELS, PER, Round)


class Round(Scene):
    def __init__(self, level=0):
        self.level = level

    def enter(self, game):
        super().enter(game)
        self.progress = Progress()
        self.stage = self.level
        self.rng = random.Random()
        self.cards = logic.make_board(self.stage, self.rng)
        self.up, self.done, self.first, self.wait = set(), set(), None, 0.0
        self.tries = []                                    # True = a pair found, False = two cards that did not match
        game.voice.say(["say_find_pairs"])
        self.layout()

    def layout(self):
        g, n = self.game, len(self.cards)
        cols = logic.COLS[n // 2]
        rows = (n + cols - 1) // cols
        area = pygame.Rect(int(g.w * 0.06), int(g.h * 0.1), int(g.w * 0.88), int(g.h * 0.86))
        cell = min(area.w / cols, area.h / rows)
        self.rects = []
        for i in range(n):
            r, c = divmod(i, cols)
            x = area.centerx - cell * cols / 2 + c * cell
            y = area.centery - cell * rows / 2 + r * cell
            self.rects.append(pygame.Rect(int(x + cell * 0.05), int(y + cell * 0.05), int(cell * 0.9), int(cell * 0.9)))

    @property
    def animated(self):
        return self.wait > 0

    def event(self, e):
        if e.type != pygame.MOUSEBUTTONDOWN or e.button != 1 or self.wait > 0:
            return
        for i, r in enumerate(self.rects):
            if r.collidepoint(e.pos) and i not in self.up and i not in self.done:
                self.flip(i)
                return

    def flip(self, i):
        self.up.add(i)
        self.game.voice.say([self.cards[i]["word"]["voice"]])         # every card is read aloud when turned
        if self.first is None:
            self.first = i
            return
        a, b = self.cards[self.first], self.cards[i]
        if logic.is_match(a, b):
            self.done |= {self.first, i}
            self.up -= {self.first, i}
            self.tries.append(True)
            self.game.voice.say([a["word"]["voice"], "say_pair_found"] if self.game.voice.has("say_pair_found") else [a["word"]["voice"], self.game.voice.variant("say_correct", self.rng, 8)])
            if len(self.done) == len(self.cards):
                self.wait = -1                              # all found: go to the reward when the voice is done
        else:
            self.tries.append(False)
            self.wait = 1.4
        self.first = None

    def update(self, dt):
        if self.wait > 0:
            self.wait -= dt
            if self.wait <= 0:
                self.up = set(i for i in self.up if i == self.first)
                self.wait = 0.0
                self.game.redraw = True
        elif self.wait == -1 and not self.game.voice.busy:
            self.progress.finish_round("minne", self.level, PER, TOP)
            self.game.go(Reward(self.tries, select))

    def draw(self, surf):
        g = self.game
        draw_dots(g, [True] * (len(self.done) // 2), len(self.cards) // 2)
        for i, r in enumerate(self.rects):
            card = self.cards[i]
            if i in self.up or i in self.done:
                if card["kind"] == "pic":
                    pygame.draw.rect(surf, WHITE, r, border_radius=int(r.h * 0.12))
                    pic = picture(card["word"]["pic"], int(r.w * 0.82))
                    if pic:
                        surf.blit(pic, pic.get_rect(center=r.center))
                else:
                    pygame.draw.rect(surf, COLORS["soft"], r, border_radius=int(r.h * 0.12))
                    w = card["word"]["text"]
                    size = r.h * (0.5 if self.level == 0 else 0.34)      # big letters on the first level (always lower case: that is what the keys show)
                    while size > 10 and g.fonts.get(size).size(w)[0] > r.w * 0.86:      # long words (and capitals) must fit the card
                        size *= 0.92
                    g.text(w, size, (40, 30, 10), center=r.center)
                if i in self.done:
                    pygame.draw.rect(surf, COLORS["good"], r, 7, border_radius=int(r.h * 0.12))
            else:
                pygame.draw.rect(surf, tuple(max(0, c - 40) for c in BACK), r.move(0, 5), border_radius=int(r.h * 0.12))
                pygame.draw.rect(surf, BACK, r, border_radius=int(r.h * 0.12))
                g.text("?", r.h * 0.5, (210, 216, 250), center=r.center)


def run(windowed):
    game = Game("Memory", windowed)
    game.go(select())
    game.run()


if __name__ == "__main__":
    main_guard(run)