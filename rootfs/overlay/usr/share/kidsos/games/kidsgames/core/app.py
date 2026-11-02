"""Window, main loop, voice player and drawing helpers shared by the KidsOS games (pygame)."""
import math
import os
import sys

import pygame

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.environ.get("KIDSGAMES_ASSETS", os.path.join(HERE, "..", "..", "assets"))
FONT_PATHS = ("/usr/share/fonts/opentype/comic-neue/ComicNeue-Bold.otf",
              "C:/Windows/Fonts/comicbd.ttf")
# A plain sans font whose letters look like the ones printed on the keys (double-storey a, g, y): used where the child
# has to find a letter on the keyboard. Comic Neue is friendlier for everything else but draws a single-storey a.
PLAIN_FONT_PATHS = ("/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                    "C:/Windows/Fonts/arialbd.ttf")
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

    def has(self, cid):
        """True if the clip exists. Planned clips that are not made yet are skipped silently."""
        return os.path.exists(os.path.join(self.dir, cid + ".mp3"))

    def variant(self, prefix, rng, top):
        """A random clip out of prefix_1 .. prefix_top that exists (more praise variants appear as they are made)."""
        ids = ["%s_%d" % (prefix, i) for i in range(1, top + 1)]
        ids = [i for i in ids if self.has(i)] or ids[:1]
        return rng.choice(ids)

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
        self.plain_path = next((p for p in PLAIN_FONT_PATHS if os.path.exists(p)), self.path)
        self.cache = {}

    def get(self, size, plain=False):
        size = max(8, int(size))
        if (size, plain) not in self.cache:
            self.cache[(size, plain)] = pygame.font.Font(self.plain_path if plain else self.path, size)
        return self.cache[(size, plain)]


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

    def text(self, s, size, color=WHITE, center=None, topleft=None, midleft=None, plain=False):
        img = self.fonts.get(size, plain).render(s, True, color)
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
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.home_rect().collidepoint(e.pos):
                    self.running = False          # the small Hem button: back to the start screen
                    continue
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
                self.draw_home_button()
                if self.esc_held > 0.3:
                    self.draw_quit_ring()
                pygame.display.flip()
        getattr(self.scene, "leave", lambda: None)()                 # e.g. Rita saves the picture
        pygame.quit()

    def home_rect(self):
        s = int(self.h * 0.085)
        return pygame.Rect(self.w - s - int(self.h * 0.02), int(self.h * 0.015), s, s)

    def draw_home_button(self):
        r = self.home_rect()
        pygame.draw.rect(self.screen, COLORS["panel"], r, border_radius=int(r.h * 0.3))
        cx, cy, u = r.centerx, r.centery, r.h * 0.26                      # a little house
        pygame.draw.polygon(self.screen, (200, 206, 240), [(cx - u * 1.3, cy - u * 0.1), (cx, cy - u * 1.3), (cx + u * 1.3, cy - u * 0.1)])
        pygame.draw.rect(self.screen, (200, 206, 240), (cx - u * 0.9, cy - u * 0.1, u * 1.8, u * 1.2))

    def draw_quit_ring(self):
        frac = min(1.0, self.esc_held / QUIT_HOLD_SECONDS)
        cx, cy, r = self.w - 70, self.h - 70, 40
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


def draw_object(surf, kind, cx, cy, r, crossed=False, ghost=False):
    """Simple flat objects drawn with shapes (no image files needed). ghost = dashed outline only (to be counted)."""
    if ghost:
        col = (150, 160, 215)
        if kind == "star":
            pts = [(cx + (r if i % 2 == 0 else r * 0.45) * math.cos(-math.pi / 2 + i * math.pi / 5),
                    cy + (r if i % 2 == 0 else r * 0.45) * math.sin(-math.pi / 2 + i * math.pi / 5)) for i in range(10)]
            pygame.draw.polygon(surf, col, pts, 4)
        else:
            pygame.draw.circle(surf, col, (cx, cy), r, 4)
        return
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


def draw_dots(game, results, total):
    """Row of dots at the top: green = right at the first try, yellow = done, dark = still to do."""
    for i in range(total):
        col = COLORS["good"] if i < len(results) and results[i] else (
            COLORS["soft"] if i < len(results) else COLORS["panel"])
        pygame.draw.circle(game.screen, col, (int(game.w * 0.05 + i * game.w * 0.03), int(game.h * 0.05)),
                           int(game.h * 0.016))


class Reward(Scene):
    """End of a round: a pulsing star. `again` is a function that returns the scene to show next."""
    animated = True

    def __init__(self, results, again):
        self.results, self.again = results, again

    def enter(self, game):
        super().enter(game)
        self.t = 0.0
        game.voice.say(["say_well_done_round", "say_sticker"])

    def update(self, dt):
        self.t += dt

    def event(self, e):
        if self.t > 2.0 and e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            self.game.go(self.again())

    def draw(self, surf):
        g = self.game
        draw_object(surf, "star", g.w // 2, int(g.h * 0.42), int(g.h * (0.22 + 0.01 * (self.t % 1.0))))
        g.text("Bra jobbat!", g.h * 0.12, COLORS["soft"], center=(g.w // 2, int(g.h * 0.8)))
        g.text("%d av %d direkt" % (sum(self.results), len(self.results)), g.h * 0.06, WHITE,
               center=(g.w // 2, int(g.h * 0.9)))

class LevelSelect(Scene):
    """Shows every level of a game: the one the child has reached, stars for rounds played, locked ones greyed out.
    Any reached level can be chosen, so a child can go back and practise an easier level again."""

    def __init__(self, game_key, labels, per, start):
        self.key, self.labels, self.per, self.start = game_key, labels, per, start

    def enter(self, game):
        super().enter(game)
        from kidsgames.core.progress import Progress
        self.progress = Progress()
        n = len(self.labels)
        self.reached = self.progress.unlocked(self.key, self.per, n - 1)
        w, h = game.w, game.h
        cw = min(int(w * 0.22), int((w * 0.92 - (n - 1) * w * 0.025) / n))
        x0 = w / 2 - (n * cw + (n - 1) * w * 0.025) / 2
        self.cards = [pygame.Rect(int(x0 + i * (cw + w * 0.025)), int(h * 0.27), cw, int(h * 0.52)) for i in range(n)]
        game.voice.say(["say_choose_level"])

    def event(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i, r in enumerate(self.cards):
                if r.collidepoint(e.pos) and i <= self.reached:
                    self.game.go(self.start(i))
        elif e.type == pygame.KEYDOWN and pygame.K_1 <= e.key < pygame.K_1 + len(self.cards):
            i = e.key - pygame.K_1
            if i <= self.reached:
                self.game.go(self.start(i))

    def draw(self, surf):
        g = self.game
        g.text("Välj nivå", g.h * 0.1, COLORS["soft"], center=(g.w // 2, int(g.h * 0.13)))
        cols = ["blue", "green", "orange", "pink", "violet"]
        for i, r in enumerate(self.cards):
            locked = i > self.reached
            col = (70, 76, 120) if locked else COLORS[cols[i % len(cols)]]
            pygame.draw.rect(surf, tuple(max(0, c - 50) for c in col), r.move(0, 7), border_radius=int(r.w * 0.12))
            pygame.draw.rect(surf, col, r, border_radius=int(r.w * 0.12))
            if i == self.reached:
                pygame.draw.rect(surf, COLORS["soft"], r.inflate(14, 14), 8, border_radius=int(r.w * 0.14))
                g.text("Här är du!", r.w * 0.13, COLORS["soft"], center=(r.centerx, r.bottom + r.w * 0.17))
            g.text(str(i + 1), r.h * 0.4, (150, 156, 190) if locked else WHITE, center=(r.centerx, r.y + r.h * 0.34))
            g.text(self.labels[i], r.w * 0.12, (150, 156, 190) if locked else WHITE, center=(r.centerx, r.y + r.h * 0.62))
            if locked:                                   # padlock
                bx, by, s = r.centerx, r.y + r.h * 0.86, r.w * 0.09
                pygame.draw.rect(surf, (150, 156, 190), (bx - s, by - s * 0.2, s * 2, s * 1.5), border_radius=5)
                pygame.draw.arc(surf, (150, 156, 190), (bx - s * 0.7, by - s * 1.4, s * 1.4, s * 1.6), 0, 3.1416, 5)
            else:                                        # stars: rounds played on this level (up to three)
                done = min(3, self.progress.done(self.key, i))
                for k in range(3):
                    cx = int(r.centerx + (k - 1) * r.w * 0.26)
                    if k < done:
                        draw_object(surf, "star", cx, int(r.y + r.h * 0.87), int(r.w * 0.09))
                    else:
                        draw_object(surf, "star", cx, int(r.y + r.h * 0.87), int(r.w * 0.09), ghost=True)