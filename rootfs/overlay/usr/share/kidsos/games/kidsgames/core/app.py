"""Window, main loop, voice player and drawing helpers shared by the KidsOS games (pygame)."""
import math
import os
import sys

import pygame

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.environ.get("KIDSGAMES_ASSETS", os.path.join(HERE, "..", "..", "assets"))
FONT_PATHS = ("/usr/share/fonts/opentype/comic-neue/ComicNeue-Bold.otf",
              "C:/Windows/Fonts/comicbd.ttf")
QUIT_HOLD_SECONDS = 3.0

BG = (27, 31, 59)
WHITE = (255, 255, 255)
COLORS = {"pink": (232, 71, 139), "violet": (123, 79, 209), "green": (26, 160, 90), "blue": (30, 136, 229),
          "orange": (240, 122, 26), "yellow": (224, 168, 0), "panel": (46, 52, 96), "good": (62, 190, 110),
          "soft": (255, 214, 102)}


class Voice:
    """Plays voice clips one after another. say(["num_003", "say_op_plus"]) speaks them in order."""

    def __init__(self, lang="sv"):
        self.dir = os.path.join(ASSETS, "voices", lang)
        self.cache, self.queue, self.channel = {}, [], None
        self.ok = True
        try:
            # a big buffer: this CPU is slow and a small one makes the sound crackle
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
        except pygame.error:
            self.ok = False

    def _load(self, cid):
        if cid not in self.cache:
            try:
                self.cache[cid] = pygame.mixer.Sound(os.path.join(self.dir, cid + ".mp3"))
            except (pygame.error, FileNotFoundError):
                self.cache[cid] = None
        return self.cache[cid]

    def say(self, ids, interrupt=True):
        if not self.ok:
            return
        if interrupt:
            self.stop()
        self.queue.extend(ids)

    def stop(self):
        self.queue.clear()
        if self.channel:
            self.channel.stop()

    @property
    def busy(self):
        return bool(self.queue) or (self.channel is not None and self.channel.get_busy())

    def update(self):
        if self.ok and self.queue and not (self.channel and self.channel.get_busy()):
            snd = self._load(self.queue.pop(0))
            if snd:
                self.channel = snd.play()


class Fonts:
    def __init__(self):
        self.path = next((p for p in FONT_PATHS if os.path.exists(p)), None)
        self.cache = {}

    def get(self, size):
        size = max(8, int(size))
        if size not in self.cache:
            self.cache[size] = pygame.font.Font(self.path, size)
        return self.cache[size]


class Game:
    def __init__(self, title, windowed=False):
        pygame.init()
        self.windowed = windowed
        pygame.display.set_caption(title)
        if windowed:
            self.screen = pygame.display.set_mode((1024, 600))
        else:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            pygame.event.set_grab(True)          # keep the keyboard and mouse inside the game
        pygame.mouse.set_visible(True)
        self.w, self.h = self.screen.get_size()
        self.fonts, self.voice = Fonts(), Voice()
        self.clock = pygame.time.Clock()
        self.scene, self.running, self.esc_held = None, True, 0.0
        self.redraw = True                        # drawing is slow here (44 ms for a full screen): only redraw on change

    def go(self, scene):
        self.scene = scene
        scene.enter(self)

    def text(self, s, size, color=WHITE, center=None, topleft=None, midleft=None):
        img = self.fonts.get(size).render(s, True, color)
        r = img.get_rect()
        if center:
            r.center = center
        elif topleft:
            r.topleft = topleft
        elif midleft:
            r.midleft = midleft
        self.screen.blit(img, r)
        return r

    def run(self):
        while self.running:
            animated = self.scene.animated or self.esc_held > 0
            dt = self.clock.tick(15 if animated else 20) / 1000.0
            for e in pygame.event.get():
                if e.type != pygame.MOUSEMOTION:
                    self.redraw = True            # any event (key, click, window uncovered) -> redraw
                if e.type == pygame.QUIT:
                    if self.windowed:             # test window: the close button works
                        self.running = False
                    continue                      # fullscreen: a child cannot close the game by accident
                if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    if self.esc_held == 0:
                        self.esc_held = 0.001
                    continue
                if e.type == pygame.KEYUP and e.key == pygame.K_ESCAPE:
                    self.esc_held = 0.0
                    continue
                self.scene.event(e)
            if self.esc_held > 0:                 # parents: hold Esc for a few seconds to leave
                self.esc_held += dt
                if self.esc_held >= QUIT_HOLD_SECONDS:
                    self.running = False
            self.voice.update()
            self.scene.update(dt)
            if self.redraw or animated:
                self.redraw = False
                self.screen.fill(BG)
                self.scene.draw(self.screen)
                if self.esc_held > 0.3:
                    self.draw_quit_ring()
                pygame.display.flip()
        pygame.quit()

    def draw_quit_ring(self):
        frac = min(1.0, self.esc_held / QUIT_HOLD_SECONDS)
        cx, cy, r = self.w - 70, 70, 40
        pygame.draw.circle(self.screen, COLORS["panel"], (cx, cy), r + 6)
        pygame.draw.arc(self.screen, COLORS["soft"], (cx - r, cy - r, 2 * r, 2 * r),
                        math.pi / 2, math.pi / 2 + 2 * math.pi * frac, 8)


def button(game, rect, label, color, size=None, pressed=False, text_color=WHITE):
    """Big rounded button; returns nothing, the scene keeps the rect for hit testing."""
    r = pygame.Rect(rect)
    shadow = r.move(0, 6)
    pygame.draw.rect(game.screen, tuple(max(0, c - 60) for c in color), shadow, border_radius=int(r.h * 0.25))
    pygame.draw.rect(game.screen, color, r.move(0, 3) if pressed else r, border_radius=int(r.h * 0.25))
    game.text(label, size or r.h * 0.55, text_color, center=r.center)


def draw_object(surf, kind, cx, cy, r, crossed=False):
    """Simple flat objects drawn with shapes (no image files needed)."""
    if kind == "ball":
        pygame.draw.circle(surf, (30, 136, 229), (cx, cy), r)
        pygame.draw.circle(surf, (120, 190, 250), (cx - r // 3, cy - r // 3), r // 3)
    elif kind == "star":
        pts = []
        for i in range(10):
            a = -math.pi / 2 + i * math.pi / 5
            rr = r if i % 2 == 0 else r * 0.45
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
        pygame.draw.polygon(surf, (255, 200, 40), pts)
    else:                                         # apple
        pygame.draw.circle(surf, (220, 50, 60), (cx, cy + r // 8), int(r * 0.9))
        pygame.draw.line(surf, (110, 70, 30), (cx, cy - r // 2), (cx + r // 8, cy - r), max(2, r // 7))
        pygame.draw.ellipse(surf, (60, 170, 80), (cx + r // 10, cy - r, r // 2, r // 3))
    if crossed:
        pygame.draw.line(surf, (255, 255, 255), (cx - r, cy - r), (cx + r, cy + r), max(3, r // 4))
        pygame.draw.line(surf, (255, 255, 255), (cx - r, cy + r), (cx + r, cy - r), max(3, r // 4))


class Scene:
    animated = False                              # True: redraw every frame (animations, timers)

    def enter(self, game):
        self.game = game

    def event(self, e):
        pass

    def update(self, dt):
        pass

    def draw(self, surf):
        pass


def main_guard(run):
    """Run a game; in a window with --window (for development), fullscreen otherwise."""
    windowed = "--window" in sys.argv
    run(windowed)
