"""Skrivlabbet: learn letters, your own name and words with the keyboard.
Run: python3 -m kidsgames.skrivlabbet  (add --window to test in a window)."""
import math
import os
import random

import pygame

from kidsgames.core.app import ASSETS, COLORS, WHITE, Game, Scene, button, draw_object, main_guard
from kidsgames.core.progress import Progress
from kidsgames.skrivlabbet import content as C

LEVELS = [("A", "Bokstäver", "pink"), ("B", "Mitt namn", "violet"), ("C", "Ord", "green")]
GHOST = (92, 100, 150)
_img_cache = {}


def picture(pic_id, size):
    """Word picture (SVG) scaled to size x size; None if it is missing or cannot be loaded."""
    if not pic_id:
        return None
    key = (pic_id, size)
    if key not in _img_cache:
        try:
            img = pygame.image.load(os.path.join(ASSETS, "images", pic_id + ".svg"))
            _img_cache[key] = pygame.transform.smoothscale(img.convert_alpha(), (size, size))
        except (pygame.error, FileNotFoundError):
            _img_cache[key] = None
    return _img_cache[key]


def draw_keyboard(g, area, target=None, pulse=False, flash=None):
    """On-screen Swedish keyboard (letter rows). Returns {char: rect} for mouse clicks."""
    rects = {}
    kw = min(area.w / 12.0, area.h / 3.4)
    gap = kw * 0.12
    for r, row in enumerate(C.ROWS):
        x0 = area.centerx - (len(row) * kw) / 2 + (0.5 * kw if r == 1 else (1.0 * kw if r == 2 else 0))
        for i, ch in enumerate(row):
            rect = pygame.Rect(int(x0 + i * kw), int(area.y + r * kw * 1.05), int(kw - gap), int(kw - gap))
            color = COLORS["panel"]
            lit = (ch == target)
            if lit and pulse:
                color = COLORS["soft"]
            elif lit:
                color = (86, 96, 160)
            if flash and ch == flash:
                color = (200, 90, 90)
            pygame.draw.rect(g.screen, tuple(max(0, c - 40) for c in color), rect.move(0, 4), border_radius=int(kw * 0.2))
            pygame.draw.rect(g.screen, color, rect, border_radius=int(kw * 0.2))
            g.text(ch, kw * 0.58, (30, 30, 50) if (lit and pulse) else WHITE, center=rect.center, plain=True)   # lower case, like the keys
            rects[ch] = rect
    return rects


class Menu(Scene):
    def enter(self, game):
        super().enter(game)
        game.voice.say(["say_hello", "say_choose_game"])
        w, h = game.w, game.h
        n = len(LEVELS)
        tw, th = min(int(w * 0.3), int((w * 0.92 - (n - 1) * w * 0.03) / n)), int(h * 0.5)
        self.tiles = []
        for i, (letter, title, col) in enumerate(LEVELS):
            x = int(w / 2 + (i - 0.5 * (n - 1)) * (tw + w * 0.03) - tw / 2)
            self.tiles.append((pygame.Rect(x, int(h * 0.3), tw, th), i, title, col))

    def start(self, i):
        self.game.go(Round(i))

    def event(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for r, i, _t, _c in self.tiles:
                if r.collidepoint(e.pos):
                    self.start(i)
        if e.type == pygame.KEYDOWN and pygame.K_1 <= e.key < pygame.K_1 + len(LEVELS):
            self.start(e.key - pygame.K_1)

    def draw(self, surf):
        g = self.game
        g.text("Skrivlabbet", g.h * 0.12, COLORS["soft"], center=(g.w // 2, g.h * 0.14))
        for r, i, title, col in self.tiles:
            button(g, r, "", COLORS[col])
            g.text(LEVELS[i][0], r.h * 0.5, WHITE, center=(r.centerx, r.y + r.h * 0.38))
            g.text(title, r.h * 0.12, WHITE, center=(r.centerx, r.y + r.h * 0.78))


class Round(Scene):
    """One round of typing items: letters (A), the child's name (B) or words (C)."""

    def __init__(self, level):
        self.level = level

    def enter(self, game):
        super().enter(game)
        self.progress = Progress()
        self.rng = random.Random()
        stats = self.progress.data.setdefault("skriv", {"A": 0, "B": 0, "C": 0})
        keys = set("".join(C.ROWS))
        if self.level == 0:
            self.items = [{"text": ch, "single": True, "pic": C.LETTERS[ch]["pic"],
                           "say": ["say_find_letter", C.letter_sound_id(ch)], "again": [C.letter_sound_id(ch)]}
                          for ch in C.letter_round(stats["A"], self.rng)]
        elif self.level == 1:
            name = "".join(c for c in C.name_letters(C.child_name()) if c in keys) or "kid"
            self.items = [{"text": name, "ghost": True, "say": ["say_type_name"], "again": ["say_type_name"]}
                          for _ in range(3)]                              # lower case, like the keys
        else:
            self.items = [{"text": w["text"], "pic": w["pic"], "ghost": w["mode"] == "copy",
                           "say": ["say_type_copy" if w["mode"] == "copy" else "say_type_word", w["voice"]],
                           "again": [w["voice"]], "word_voice": w["voice"]}
                          for w in C.word_round(self.rng)]
        self.results, self.index, self.key_rects = [], -1, {}
        self.next_item()

    def next_item(self):
        self.index += 1
        if self.index >= len(self.items):
            stats = self.progress.data["skriv"]
            stats["ABC"[self.level]] = stats.get("ABC"[self.level], 0) + 1
            self.progress.add_sticker("skriv" + "ABC"[self.level])
            self.progress.save()
            self.game.go(Reward(self.results))
            return
        self.item = self.items[self.index]
        self.pos, self.wrong, self.total_wrong = 0, 0, 0
        self.idle, self.hint, self.state, self.timer, self.flash = 0.0, False, "ask", 0.0, (None, 0.0)
        self.game.voice.say(self.item["say"])
        self.game.redraw = True

    @property
    def target(self):
        return self.item["text"][self.pos] if self.state == "ask" else None

    @property
    def animated(self):
        return self.hint or self.state != "ask" or self.flash[1] > 0

    def press(self, ch):
        if self.state != "ask":
            return
        self.idle = 0.0
        if ch == self.target:
            self.wrong = 0
            self.pos += 1
            nm = C.letter_name_id(ch)
            if self.pos >= len(self.item["text"]):
                self.results.append(self.total_wrong == 0)
                self.state, self.timer = "right", 0.0
                ids = [self.game.voice.variant("say_correct", self.rng, 8)]
                if self.item.get("word_voice"):
                    ids = [self.item["word_voice"]] + ids
                elif nm and (self.item.get("single") or self.level == 1):
                    ids = [nm] + ids
                self.game.voice.say(ids)
            elif nm and self.level != 2:
                self.game.voice.say([nm])
        else:
            self.wrong += 1
            self.total_wrong += 1
            self.flash = (ch, 0.35)
            if self.wrong >= 2:
                self.hint = True
            if self.wrong in (2, 4):
                self.game.voice.say(self.item["again"])

    def event(self, e):
        if e.type == pygame.KEYDOWN and not (e.mod & (pygame.KMOD_CTRL | pygame.KMOD_ALT)):
            ch = (e.unicode or "").lower()
            if ch.isalpha() and len(ch) == 1:
                self.press(ch)
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for ch, r in self.key_rects.items():
                if r.collidepoint(e.pos):
                    self.press(ch)

    def update(self, dt):
        if self.flash[1] > 0:
            self.flash = (self.flash[0], max(0.0, self.flash[1] - dt))
        if self.state == "right":
            self.timer += dt
            if self.timer > 0.8 and not self.game.voice.busy:
                self.next_item()
        elif self.state == "ask":
            self.idle += dt
            if self.idle > 6.0 and not self.game.voice.busy:
                self.idle = 0.0
                self.hint = True
                self.game.voice.say(self.item["again"])

    def draw(self, surf):
        g, it = self.game, self.item
        for i in range(len(self.items)):
            col = COLORS["good"] if i < len(self.results) and self.results[i] else (
                COLORS["soft"] if i < len(self.results) else COLORS["panel"])
            pygame.draw.circle(surf, col, (int(g.w * 0.05 + i * g.w * 0.03), int(g.h * 0.05)), int(g.h * 0.016))
        pic = picture(it.get("pic"), int(g.h * 0.26))
        top = int(g.h * 0.08)
        if it.get("single"):
            ch = it["text"]
            if pic:
                surf.blit(pic, (int(g.w * 0.62), top))
            g.text(ch, g.h * 0.5, COLORS["soft"], plain=True, center=(int(g.w * (0.33 if pic else 0.5)), int(g.h * 0.27)))
        else:
            if pic:
                surf.blit(pic, pic.get_rect(midtop=(g.w // 2, top)))
            self.draw_word(surf, int(g.h * (0.47 if pic else 0.34)))
        pulse = int(pygame.time.get_ticks() / 350) % 2 == 0
        self.key_rects = draw_keyboard(g, pygame.Rect(int(g.w * 0.02), int(g.h * 0.63), int(g.w * 0.96), int(g.h * 0.35)),
                                       target=self.target if (self.hint or self.state == "ask" and self.level == 1) else None,
                                       pulse=pulse, flash=self.flash[0] if self.flash[1] > 0 else None)
        if self.state == "right":
            draw_object(surf, "star", g.w - int(g.h * 0.14), int(g.h * 0.22), int(g.h * 0.09))

    def draw_word(self, surf, cy):
        g, it = self.game, self.item
        text, shown = it["text"], it.get("show", it["text"])
        size = min(g.h * 0.16, g.w * 0.9 / max(3, len(text)) / 0.75)
        adv = size * 0.8
        x0 = g.w / 2 - adv * len(text) / 2
        show_ghost = it.get("ghost") or self.hint
        for i, ch in enumerate(shown):
            cx = int(x0 + adv * (i + 0.5))
            done = i < self.pos
            if done or self.state == "right":
                g.text(ch, size, WHITE, center=(cx, cy), plain=True)
            elif show_ghost:
                g.text(ch, size, GHOST, center=(cx, cy), plain=True)
            line_col = COLORS["soft"] if (i == self.pos and self.state == "ask") else GHOST
            pygame.draw.line(surf, line_col, (int(cx - adv * 0.4), int(cy + size * 0.6)),
                             (int(cx + adv * 0.4), int(cy + size * 0.6)), 6)


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
        draw_object(surf, "star", g.w // 2, int(g.h * 0.42), int(g.h * (0.22 + 0.01 * (self.t % 1.0))))
        g.text("Bra jobbat!", g.h * 0.12, COLORS["soft"], center=(g.w // 2, int(g.h * 0.8)))
        g.text("%d av %d direkt" % (sum(self.results), len(self.results)), g.h * 0.06, WHITE,
               center=(g.w // 2, int(g.h * 0.9)))


def run(windowed):
    game = Game("Skrivlabbet", windowed)
    game.go(Menu())
    game.run()


if __name__ == "__main__":
    main_guard(run)
