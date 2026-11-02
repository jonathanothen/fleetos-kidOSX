"""Para ihop: match a word to its picture. Tap a word (or the picture) to hear it, then either drag the word onto
the picture or tap the marked word again. Several ways, so every child finds one that works.
Run: python3 -m kidsgames.parihop  (add --window to test in a window)."""
import random

import pygame

from kidsgames.core.app import COLORS, WHITE, Game, Scene, draw_object, main_guard
from kidsgames.core.progress import Progress
from kidsgames.parihop import logic
from kidsgames.skrivlabbet.main import picture

DRAG_PIXELS = 14


def draw_speaker(surf, cx, cy, s, color):
    """Small loudspeaker symbol (drawn, so it does not depend on a font glyph)."""
    pygame.draw.polygon(surf, color, [(cx - s, cy - s * 0.35), (cx - s * 0.45, cy - s * 0.35), (cx + s * 0.15, cy - s * 0.85),
                                      (cx + s * 0.15, cy + s * 0.85), (cx - s * 0.45, cy + s * 0.35), (cx - s, cy + s * 0.35)])
    for k in (1, 2):
        pygame.draw.arc(surf, color, (cx - s * 0.2 + k * s * 0.15, cy - s * 0.35 * k, s * 0.7 * k * 0.75, s * 0.7 * k),
                        -0.9, 0.9, max(2, int(s * 0.12)))


class Round(Scene):
    def enter(self, game):
        super().enter(game)
        self.progress = Progress()
        self.stats = self.progress.data.setdefault("parihop", {"rounds": 0})
        self.tasks = logic.make_round(self.stats["rounds"], random.Random())
        self.rng = random.Random()
        self.results, self.index = [], -1
        self.next_task()

    def next_task(self):
        self.index += 1
        if self.index >= len(self.tasks):
            self.stats["rounds"] += 1
            self.progress.add_sticker("parihop")
            self.progress.save()
            self.game.go(Reward(self.results))
            return
        self.task = self.tasks[self.index]
        self.state, self.timer, self.wrong, self.selected = "ask", 0.0, 0, None
        self.drag = None                          # {"i": card index, "pos": (x, y), "start": (x, y), "moved": bool}
        self.bad = {}                             # card index -> seconds of red flash
        self.hint = False
        self.layout()
        self.game.redraw = True

    def layout(self):
        g, n = self.game, len(self.task["choices"])
        side = int(g.h * 0.4)
        self.pic_rect = pygame.Rect(0, int(g.h * 0.1), side + 40, side + 40)
        self.pic_rect.centerx = g.w // 2
        cw = min(int(g.w * 0.27), int((g.w * 0.94 - (n - 1) * g.w * 0.02) / n))
        ch = int(g.h * 0.18)
        x0 = g.w / 2 - (n * cw + (n - 1) * g.w * 0.02) / 2
        self.cards = [pygame.Rect(int(x0 + i * (cw + g.w * 0.02)), int(g.h * 0.72), cw, ch) for i in range(n)]

    def card_rect(self, i):
        r = self.cards[i]
        if self.drag and self.drag["i"] == i and self.drag["moved"]:
            r = r.copy()
            r.center = self.drag["pos"]
        return r

    def hear(self, i):
        self.game.voice.say([self.task["choices"][i]["voice"]])

    def submit(self, i):
        if self.state != "ask":
            return
        if i == self.task["right"]:
            self.results.append(self.wrong == 0)
            self.state, self.timer, self.selected = "right", 0.0, i
            self.game.voice.say([self.task["answer"]["voice"], "say_correct_%d" % self.rng.randint(1, 4)])
        else:
            self.wrong += 1
            self.bad[i] = 0.5
            self.selected = None
            if self.wrong >= 2:
                self.hint = True
            if self.wrong >= 3:
                self.results.append(False)
                self.state, self.timer = "reveal", 0.0
                self.game.voice.say([self.task["answer"]["voice"]])
            else:
                self.game.voice.say(["say_retry_%d" % self.rng.randint(1, 2)])

    @property
    def animated(self):
        return bool(self.drag) or self.state != "ask" or bool(self.bad) or self.hint or self.selected is not None

    def event(self, e):
        if self.state != "ask":
            return
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i, r in enumerate(self.cards):
                if r.collidepoint(e.pos) and i not in self.bad:
                    if self.selected == i:
                        self.submit(i)            # second tap on the same word: choose it
                        return
                    self.selected = i
                    self.hear(i)                  # first tap: read the word aloud (and it can be dragged from here)
                    self.drag = {"i": i, "pos": e.pos, "start": e.pos, "moved": False}
                    return
            if self.pic_rect.collidepoint(e.pos):
                self.game.voice.say([self.task["answer"]["voice"]])   # tapping the picture reads its word aloud
        elif e.type == pygame.MOUSEMOTION and self.drag:
            self.drag["pos"] = e.pos
            if abs(e.pos[0] - self.drag["start"][0]) + abs(e.pos[1] - self.drag["start"][1]) > DRAG_PIXELS:
                self.drag["moved"] = True
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1 and self.drag:
            d, self.drag = self.drag, None
            if d["moved"] and self.pic_rect.inflate(60, 60).collidepoint(e.pos):
                self.submit(d["i"])               # dropped on the picture

    def update(self, dt):
        for i in list(self.bad):
            self.bad[i] -= dt
            if self.bad[i] <= 0:
                del self.bad[i]
        if self.state in ("right", "reveal"):
            self.timer += dt
            if self.timer > 0.8 and not self.game.voice.busy:
                self.next_task()

    def draw(self, surf):
        g, t = self.game, self.task
        for i in range(len(self.tasks)):
            col = COLORS["good"] if i < len(self.results) and self.results[i] else (
                COLORS["soft"] if i < len(self.results) else COLORS["panel"])
            pygame.draw.circle(surf, col, (int(g.w * 0.05 + i * g.w * 0.03), int(g.h * 0.05)), int(g.h * 0.016))
        # the picture card
        good = self.state in ("right", "reveal")
        border = COLORS["good"] if good else (COLORS["soft"] if self.selected is not None else COLORS["panel"])
        pygame.draw.rect(surf, WHITE, self.pic_rect, border_radius=28)
        pygame.draw.rect(surf, border, self.pic_rect, 8, border_radius=28)
        pic = picture(t["answer"]["pic"], self.pic_rect.w - 40)
        if pic:
            surf.blit(pic, pic.get_rect(center=self.pic_rect.center))
        draw_speaker(surf, self.pic_rect.right - 34, self.pic_rect.top + 34, 16, (120, 100, 70))   # tap the picture to hear it
        pulse = int(pygame.time.get_ticks() / 350) % 2 == 0
        order = [i for i in range(len(self.cards)) if not (self.drag and self.drag["moved"] and self.drag["i"] == i)]
        if self.drag and self.drag["moved"]:
            order.append(self.drag["i"])          # the word being dragged is drawn last, on top
        for i in order:
            r = self.card_rect(i)
            word = t["choices"][i]["text"]
            col = COLORS["panel"]
            if i in self.bad:
                col = (200, 90, 90)
            elif self.state in ("right", "reveal") and i == t["right"]:
                col = COLORS["good"]
            elif self.hint and i == t["right"] and pulse:
                col = (96, 108, 190)
            elif i == self.selected:
                col = (86, 96, 160)
            pygame.draw.rect(surf, tuple(max(0, c - 40) for c in col), r.move(0, 6), border_radius=int(r.h * 0.25))
            pygame.draw.rect(surf, col, r, border_radius=int(r.h * 0.25))
            if i == self.selected:
                pygame.draw.rect(surf, COLORS["soft"], r, 6, border_radius=int(r.h * 0.25))
            size = min(r.h * 0.55, r.w * 0.62 / max(3, len(word)) * 1.7)
            g.text(word, size, WHITE, center=(r.centerx + r.h * 0.2, r.centery))
            draw_speaker(surf, int(r.x + r.h * 0.38), r.centery, r.h * 0.2, (170, 180, 230))

        if good:
            draw_object(surf, "star", g.w - int(g.h * 0.14), int(g.h * 0.2), int(g.h * 0.09))


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
            self.game.go(Round())

    def draw(self, surf):
        g = self.game
        draw_object(surf, "star", g.w // 2, int(g.h * 0.42), int(g.h * (0.22 + 0.01 * (self.t % 1.0))))
        g.text("Bra jobbat!", g.h * 0.12, COLORS["soft"], center=(g.w // 2, int(g.h * 0.8)))
        g.text("%d av %d direkt" % (sum(self.results), len(self.results)), g.h * 0.06, WHITE,
               center=(g.w // 2, int(g.h * 0.9)))


def run(windowed):
    game = Game("Para ihop", windowed)
    game.go(Round())
    game.run()


if __name__ == "__main__":
    main_guard(run)
