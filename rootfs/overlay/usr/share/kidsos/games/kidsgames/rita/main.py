"""Rita: a simple drawing program for small children. Run: python3 -m kidsgames.rita [--window]
Big colours, three brush sizes, eraser, paint bucket, stamps (our own pictures), undo, new picture, save to ~/Bilder/Rita."""
import os
import time

import pygame

from kidsgames.core.app import COLORS, WHITE, Game, Scene, button, draw_object, main_guard
from kidsgames.skrivlabbet import content as C
from kidsgames.skrivlabbet.main import picture

PALETTE = [(229, 57, 53), (251, 140, 0), (253, 216, 53), (67, 160, 71), (156, 204, 101), (30, 136, 229),
           (79, 195, 247), (142, 36, 170), (240, 98, 146), (121, 85, 72), (33, 33, 33), (255, 255, 255)]
SIZES = [6, 16, 34]
SAVE_DIR = os.path.expanduser("~/Bilder/Rita")
LAST = os.path.join(os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share")), "kidsos", "rita-last.png")
UNDO_STEPS = 8
STAMPS_PER_PAGE = 20


class Draw(Scene):
    def enter(self, game):
        super().enter(game)
        g = self.game
        self.panel_w = int(g.w * 0.2)
        self.canvas_rect = pygame.Rect(self.panel_w + 8, int(g.h * 0.11), g.w - self.panel_w - 16, int(g.h * 0.87))
        self.canvas = pygame.Surface(self.canvas_rect.size)
        self.canvas.fill(WHITE)
        try:
            img = pygame.image.load(LAST)
            self.canvas.blit(img, (0, 0))
        except (pygame.error, FileNotFoundError):
            pass
        self.color, self.size_i, self.tool = PALETTE[0], 1, "pen"        # pen | eraser | fill | stamp
        self.stamp = None
        self.undo, self.last_pos, self.dirty, self.toast = [], None, False, (None, 0.0)
        self.stamp_menu, self.page = False, 0
        game.voice.say(["say_draw_something"])
        self.layout()

    # ---- layout ----
    def layout(self):
        g, pw = self.game, self.panel_w
        pad = int(pw * 0.06)
        sw = (pw - pad * 5) // 4
        self.color_rects = [(pygame.Rect(pad + (i % 4) * (sw + pad), int(g.h * 0.03) + (i // 4) * (sw + pad), sw, sw), c)
                            for i, c in enumerate(PALETTE)]
        y = int(g.h * 0.03) + 3 * (sw + pad) + pad
        self.size_rects = [pygame.Rect(pad + i * ((pw - pad * 2) // 3), y, (pw - pad * 2) // 3 - pad // 2, int(g.h * 0.09)) for i in range(3)]
        y += int(g.h * 0.09) + pad * 2
        bw, bh = (pw - pad * 3) // 2, int(g.h * 0.115)
        names = [("pen", "Penna"), ("eraser", "Sudd"), ("fill", "Färg"), ("stamp", "Stämpel"), ("undo", "Ångra"), ("new", "Ny"), ("save", "Spara")]
        self.tool_rects = [(pygame.Rect(pad + (i % 2) * (bw + pad), y + (i // 2) * (bh + pad), bw, bh), k, label)
                           for i, (k, label) in enumerate(names)]
        cols, cell = 5, int(min(g.w * 0.7 / 5, g.h * 0.6 / 4))
        menu = pygame.Rect(0, 0, cols * cell + 40, 4 * cell + 110)
        menu.center = (self.canvas_rect.centerx, self.canvas_rect.centery)
        self.menu_rect = menu
        self.stamp_rects = [pygame.Rect(menu.x + 20 + (i % cols) * cell, menu.y + 20 + (i // cols) * cell, cell - 6, cell - 6)
                            for i in range(STAMPS_PER_PAGE)]
        self.next_rect = pygame.Rect(menu.right - 200, menu.bottom - 80, 180, 60)
        self.close_rect = pygame.Rect(menu.x + 20, menu.bottom - 80, 180, 60)

    @property
    def animated(self):
        return self.last_pos is not None or self.toast[1] > 0

    # ---- drawing ----
    def to_canvas(self, pos):
        return pos[0] - self.canvas_rect.x, pos[1] - self.canvas_rect.y

    def push_undo(self):
        self.undo.append(self.canvas.copy())
        del self.undo[:-UNDO_STEPS]

    def paint_line(self, a, b):
        col = WHITE if self.tool == "eraser" else self.color
        r = SIZES[self.size_i] // 2 + (4 if self.tool == "eraser" else 0)
        pygame.draw.line(self.canvas, col, a, b, r * 2)
        pygame.draw.circle(self.canvas, col, b, r)

    def flood_fill(self, pos):
        """Paint bucket: fill the area of similar colour around pos (done in C by pygame.mask, so it is fast)."""
        x, y = pos
        target = self.canvas.get_at((x, y))
        if tuple(target[:3]) == tuple(self.color):
            return
        region = pygame.mask.from_threshold(self.canvas, target, (40, 40, 40, 255)).connected_component((x, y))
        self.push_undo()
        region.to_surface(self.canvas, setcolor=tuple(self.color) + (255,), unsetcolor=None)
        self.dirty = True

    def put_stamp(self, pos):
        side = (90, 150, 240)[self.size_i]
        pic = picture(self.stamp, side)
        if pic:
            self.push_undo()
            self.canvas.blit(pic, pic.get_rect(center=pos))
            self.dirty = True

    def save_png(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        pygame.image.save(self.canvas, path)

    def save_picture(self):
        path = os.path.join(SAVE_DIR, "rita-%s.png" % time.strftime("%Y%m%d-%H%M%S"))
        try:
            self.save_png(path)
            self.toast = ("Sparat!", 1.8)
            self.game.voice.say(["say_saved"])
        except (OSError, pygame.error):
            self.toast = ("Det gick inte att spara", 2.5)

    def new_picture(self):
        if self.dirty:                                   # never lose a picture: keep the old one in the folder
            self.save_picture()
        self.push_undo()
        self.canvas.fill(WHITE)
        self.dirty = False

    def leave(self):
        if self.dirty:
            try:
                self.save_png(LAST)
            except (OSError, pygame.error):
                pass

    # ---- input ----
    def event(self, e):
        g = self.game
        if self.stamp_menu:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                words = C.WORDS
                for i, r in enumerate(self.stamp_rects):
                    idx = self.page * STAMPS_PER_PAGE + i
                    if r.collidepoint(e.pos) and idx < len(words):
                        self.stamp, self.tool, self.stamp_menu = words[idx]["pic"], "stamp", False
                        return
                if self.next_rect.collidepoint(e.pos):
                    self.page = (self.page + 1) % ((len(words) + STAMPS_PER_PAGE - 1) // STAMPS_PER_PAGE)
                elif self.close_rect.collidepoint(e.pos) or not self.menu_rect.collidepoint(e.pos):
                    self.stamp_menu = False
            return
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if self.canvas_rect.collidepoint(e.pos):
                p = self.to_canvas(e.pos)
                if self.tool == "stamp" and self.stamp:
                    self.put_stamp(p)
                elif self.tool == "fill":
                    self.flood_fill(p)
                else:
                    self.push_undo()
                    self.last_pos = p
                    self.paint_line(p, p)
                    self.dirty = True
                return
            for r, c in self.color_rects:
                if r.collidepoint(e.pos):
                    self.color = c
                    if self.tool in ("eraser", "stamp"):
                        self.tool = "pen"                        # picking a colour means "draw with it"
                    return
            for i, r in enumerate(self.size_rects):
                if r.collidepoint(e.pos):
                    self.size_i = i
                    return
            for r, key, _label in self.tool_rects:
                if r.collidepoint(e.pos):
                    if key in ("pen", "eraser", "fill"):
                        self.tool = key
                    elif key == "stamp":
                        self.stamp_menu = True
                    elif key == "undo" and self.undo:
                        self.canvas = self.undo.pop()
                    elif key == "new":
                        self.new_picture()
                    elif key == "save":
                        self.save_picture()
        elif e.type == pygame.MOUSEMOTION and self.last_pos is not None:
            p = self.to_canvas(e.pos)
            self.paint_line(self.last_pos, p)
            self.last_pos = p
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            self.last_pos = None

    def update(self, dt):
        if self.toast[1] > 0:
            self.toast = (self.toast[0], max(0.0, self.toast[1] - dt))
            self.game.redraw = True

    # ---- screen ----
    def draw_icon(self, surf, key, r):
        cx, cy, u = r.centerx, r.y + r.h * 0.38, r.h * 0.22
        w = (240, 240, 250)
        if key == "pen":
            pygame.draw.line(surf, w, (cx - u, cy + u), (cx + u, cy - u), int(u * 0.7))
            pygame.draw.polygon(surf, (255, 214, 102), [(cx - u * 1.3, cy + u * 1.3), (cx - u * 1.1, cy + u * 0.6), (cx - u * 0.5, cy + u * 1.2)])
        elif key == "eraser":
            pygame.draw.rect(surf, (240, 140, 160), (cx - u * 1.1, cy - u * 0.6, u * 2.2, u * 1.3), border_radius=6)
            pygame.draw.rect(surf, w, (cx - u * 1.1, cy + u * 0.1, u * 2.2, u * 0.6), border_radius=6)
        elif key == "fill":
            pygame.draw.polygon(surf, w, [(cx - u, cy - u * 0.2), (cx, cy - u * 1.1), (cx + u * 0.9, cy - u * 0.2), (cx, cy + u * 0.9)])
            pygame.draw.circle(surf, self.color, (int(cx + u * 1.1), int(cy + u * 0.9)), int(u * 0.45))
        elif key == "stamp":
            pic = picture(self.stamp, int(u * 2.6)) if self.stamp else None
            if pic:
                surf.blit(pic, pic.get_rect(center=(int(cx), int(cy))))
            else:
                draw_object(surf, "star", int(cx), int(cy), int(u * 1.2))
        elif key == "undo":
            pygame.draw.arc(surf, w, (cx - u, cy - u * 0.8, u * 2, u * 1.8), 0.2, 3.3, int(u * 0.5))
            pygame.draw.polygon(surf, w, [(cx - u * 1.5, cy + u * 0.2), (cx - u * 0.3, cy - u * 0.6), (cx - u * 0.3, cy + u * 0.9)])
        elif key == "new":
            pygame.draw.rect(surf, w, (cx - u * 0.9, cy - u * 1.1, u * 1.8, u * 2.2), border_radius=6)
            pygame.draw.line(surf, (60, 70, 120), (cx, cy - u * 0.5), (cx, cy + u * 0.5), 5)
            pygame.draw.line(surf, (60, 70, 120), (cx - u * 0.5, cy), (cx + u * 0.5, cy), 5)
        elif key == "save":
            pygame.draw.rect(surf, w, (cx - u, cy - u, u * 2, u * 2), border_radius=6)
            pygame.draw.rect(surf, (60, 70, 120), (cx - u * 0.5, cy - u, u, u * 0.7))
            pygame.draw.rect(surf, (60, 70, 120), (cx - u * 0.6, cy + u * 0.1, u * 1.2, u * 0.8), border_radius=3)

    def draw(self, surf):
        g = self.game
        pygame.draw.rect(surf, (36, 41, 80), (0, 0, self.panel_w, g.h))
        for r, c in self.color_rects:
            pygame.draw.rect(surf, c, r, border_radius=int(r.h * 0.25))
            if c == self.color and self.tool in ("pen", "fill"):
                pygame.draw.rect(surf, (255, 214, 102), r.inflate(8, 8), 6, border_radius=int(r.h * 0.3))
            elif c == WHITE:
                pygame.draw.rect(surf, (150, 160, 215), r, 3, border_radius=int(r.h * 0.25))
        for i, r in enumerate(self.size_rects):
            pygame.draw.rect(surf, (255, 214, 102) if i == self.size_i else COLORS["panel"], r, border_radius=18)
            pygame.draw.circle(surf, (33, 33, 60) if i == self.size_i else (200, 206, 240), r.center, max(4, SIZES[i] // 2 + 2))
        for r, key, label in self.tool_rects:
            on = key == self.tool
            pygame.draw.rect(surf, (86, 96, 190) if on else COLORS["panel"], r, border_radius=int(r.h * 0.22))
            if on:
                pygame.draw.rect(surf, (255, 214, 102), r, 5, border_radius=int(r.h * 0.22))
            self.draw_icon(surf, key, r)
            g.text(label, r.h * 0.2, WHITE, center=(r.centerx, r.bottom - r.h * 0.17))
        surf.blit(self.canvas, self.canvas_rect)
        pygame.draw.rect(surf, (150, 160, 215), self.canvas_rect, 4)
        if self.stamp_menu:
            pygame.draw.rect(surf, (36, 41, 80), self.menu_rect, border_radius=26)
            pygame.draw.rect(surf, (255, 214, 102), self.menu_rect, 6, border_radius=26)
            for i, r in enumerate(self.stamp_rects):
                idx = self.page * STAMPS_PER_PAGE + i
                if idx < len(C.WORDS):
                    pygame.draw.rect(surf, WHITE, r, border_radius=16)
                    pic = picture(C.WORDS[idx]["pic"], int(r.w * 0.86))
                    if pic:
                        surf.blit(pic, pic.get_rect(center=r.center))
            button(g, self.close_rect, "Stäng", COLORS["orange"], size=self.close_rect.h * 0.5)
            button(g, self.next_rect, "Fler", COLORS["blue"], size=self.next_rect.h * 0.5)
        if self.toast[1] > 0:
            t = pygame.Rect(0, 0, int(g.w * 0.3), int(g.h * 0.12))
            t.center = (self.canvas_rect.centerx, int(g.h * 0.2))
            pygame.draw.rect(surf, COLORS["good"], t, border_radius=24)
            g.text(self.toast[0], t.h * 0.5, WHITE, center=t.center)


def run(windowed):
    game = Game("Rita", windowed)
    game.go(Draw())
    game.run()


if __name__ == "__main__":
    main_guard(run)