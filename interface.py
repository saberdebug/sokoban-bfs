# interface.py
# Interface Pygame moderne : menu de sélection des niveaux + simulation animée
# de la solution, avec comparaison BFS / A* (h1, h2, h3).
# Lancer avec :  python interface.py

import math
import threading
import time

import pygame

from levels import LEVELS
from sokoban_puzzle import SokobanPuzzle
from algos import ALGOS

# ------------------------------------------------------------------ constantes
W, H = 1120, 740
PANEL_X, PANEL_W = 730, 360
BOARD_AREA = pygame.Rect(30, 96, 670, 604)

# Palette inspired by classic Sokoban games
BG_TOP = BG_BOT = (10, 10, 12)
CARD = (231, 224, 190)
CARD_HI = (241, 234, 203)
CARD_LINE = (104, 89, 54)
TEXT = (48, 42, 29)
DIM = (116, 104, 74)
DIM_DARK = (151, 139, 105)
ACCENT = (204, 126, 35)
ACCENT_L = (235, 157, 57)
GREEN = (54, 132, 79)
RED = (176, 69, 49)

FLOOR_A, FLOOR_B = (232, 225, 190), (226, 219, 182)
WALL_FACE, WALL_SIDE, WALL_HI = (178, 163, 99), (119, 105, 59), (205, 190, 126)
BOX_C, BOX_DARK = (238, 142, 30), (111, 55, 13)
BOX_OK, BOX_OK_DARK = (179, 95, 24), (79, 39, 12)
TARGET = (218, 142, 126)
PLAYER_C = (48, 119, 209)

ALGO_NAMES = list(ALGOS.keys())
ALGO_COLORS = [(211, 124, 38), (76, 112, 190), (36, 137, 133), (187, 83, 111)]
DIRS = {"UP": (0, -1), "DOWN": (0, 1), "LEFT": (-1, 0), "RIGHT": (1, 0)}
DIR_FR = {"UP": "Haut", "DOWN": "Bas", "LEFT": "Gauche", "RIGHT": "Droite"}
OPPOSITE = {"UP": "DOWN", "DOWN": "UP", "LEFT": "RIGHT", "RIGHT": "LEFT"}

# ------------------------------------------------------------------ utilitaires
def lerp(a, b, t):
    return a + (b - a) * t

def ease(t):
    return t * t * (3 - 2 * t)

def mix(c1, c2, t):
    return tuple(int(lerp(a, b, t)) for a, b in zip(c1, c2))

def gradient(w, h, top, bot):
    s = pygame.Surface((w, h))
    for y in range(h):
        pygame.draw.line(s, mix(top, bot, y / h), (0, y), (w, y))
    return s

def rrect(surf, color, rect, r=12, width=0):
    pygame.draw.rect(surf, color, rect, width, border_radius=r)

def arect(surf, color, rect, r=12, width=0):
    """Rectangle arrondi semi-transparent."""
    rect = pygame.Rect(rect)
    s = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(s, color, s.get_rect(), width, border_radius=r)
    surf.blit(s, rect.topleft)

_shadow_cache = {}

def shadow(surf, rect, r=16, layers=5, alpha=20, dy=6):
    rect = pygame.Rect(rect)
    key = (rect.w, rect.h, r, layers, alpha)
    
    # Prevent memory leak by limiting cache size
    if len(_shadow_cache) > 100:
        _shadow_cache.clear()
        
    if key not in _shadow_cache:
        pad = layers * 4 + 4
        s = pygame.Surface((rect.w + pad * 2, rect.h + pad * 2), pygame.SRCALPHA)
        for i in range(layers, 0, -1):
            g = pygame.Rect(pad, pad, rect.w, rect.h).inflate(i * 4, i * 4)
            pygame.draw.rect(s, (0, 0, 0, alpha), g, border_radius=r + i * 2)
        _shadow_cache[key] = (s, pad)
        
    s, pad = _shadow_cache[key]
    surf.blit(s, (rect.x - pad, rect.y - pad + dy))

_text_cache = {}

def draw_text(surf, font, txt, pos, color=TEXT, anchor="topleft"):
    """Dessine du texte avec un système de cache pour optimiser les FPS."""
    key = (txt, font, color)
    if key not in _text_cache:
        _text_cache[key] = font.render(txt, True, color)
    img = _text_cache[key]
    rect = img.get_rect(**{anchor: pos})
    surf.blit(img, rect)
    return rect

def draw_icon(s, kind, c, u, col):
    """Petites icônes vectorielles (u = demi-taille)."""
    x, y = c
    if kind == "play":
        pygame.draw.polygon(s, col, [(x - u * 0.6, y - u), (x - u * 0.6, y + u), (x + u, y)])
    elif kind == "pause":
        pygame.draw.rect(s, col, (x - u * 0.8, y - u, u * 0.6, u * 2), border_radius=2)
        pygame.draw.rect(s, col, (x + u * 0.2, y - u, u * 0.6, u * 2), border_radius=2)
    elif kind == "prev":
        pygame.draw.polygon(s, col, [(x + u, y - u), (x + u, y + u), (x - u * 0.6, y)])
        pygame.draw.rect(s, col, (x - u, y - u, u * 0.35, u * 2))
    elif kind == "next":
        pygame.draw.polygon(s, col, [(x - u, y - u), (x - u, y + u), (x + u * 0.6, y)])
        pygame.draw.rect(s, col, (x + u * 0.65, y - u, u * 0.35, u * 2))
    elif kind == "end":
        pygame.draw.polygon(s, col, [(x - u, y - u), (x - u, y + u), (x + u * 0.1, y)])
        pygame.draw.polygon(s, col, [(x, y - u), (x, y + u), (x + u * 1.1, y)])
    elif kind == "restart":
        w = max(2, int(u * 0.3))
        pygame.draw.arc(s, col, pygame.Rect(x - u, y - u, u * 2, u * 2), 0.6, 5.7, w)
        a = 5.7
        px, py = x + u * math.cos(a), y - u * math.sin(a)
        tx, ty = -math.sin(a), -math.cos(a)          
        nx, ny = -ty, tx
        pygame.draw.polygon(s, col, [
            (px + tx * u * 0.7, py + ty * u * 0.7),
            (px + nx * u * 0.5, py + ny * u * 0.5),
            (px - nx * u * 0.5, py - ny * u * 0.5)])
    elif kind == "back":
        pygame.draw.lines(s, col, False, [(x + u * 0.4, y - u), (x - u * 0.5, y), (x + u * 0.4, y + u)], 3)
    elif kind == "minus":
        pygame.draw.line(s, col, (x - u, y), (x + u, y), 3)
    elif kind == "plus":
        pygame.draw.line(s, col, (x - u, y), (x + u, y), 3)
        pygame.draw.line(s, col, (x, y - u), (x, y + u), 3)
    elif kind == "check":
        pygame.draw.lines(s, col, False, [(x - u, y), (x - u * 0.3, y + u * 0.7), (x + u, y - u * 0.7)], 4)
    elif kind == "cross":
        pygame.draw.line(s, col, (x - u * 0.8, y - u * 0.8), (x + u * 0.8, y + u * 0.8), 4)
        pygame.draw.line(s, col, (x - u * 0.8, y + u * 0.8), (x + u * 0.8, y - u * 0.8), 4)
    elif kind == "arrow":
        pygame.draw.line(s, col, (x - u, y), (x + u * 0.6, y), 3)
        pygame.draw.polygon(s, col, [(x + u * 0.2, y - u * 0.6), (x + u, y), (x + u * 0.2, y + u * 0.6)])

def draw_spinner(s, c, r, color, width=3):
    a = (time.time() * 4) % (2 * math.pi)
    pygame.draw.arc(s, color, pygame.Rect(c[0] - r, c[1] - r, r * 2, r * 2), a, a + 4.2, width)

def box_positions(state):
    return {(r, c) for r, row in enumerate(state.grid) for c, ch in enumerate(row) if ch in ("B", "*")}

# ------------------------------------------------------------------ application
class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Sokoban : BFS et A*")
        self.screen = pygame.display.set_mode((W, H))
        self.clock = pygame.time.Clock()

        fam = "consolas,couriernew,dejavusansmono,monospace"
        self.f_title = pygame.font.SysFont(fam, 58, bold=True)
        self.f_h1 = pygame.font.SysFont(fam, 27, bold=True)
        self.f_h2 = pygame.font.SysFont(fam, 21, bold=True)
        self.f_bold = pygame.font.SysFont(fam, 17, bold=True)
        self.f_body = pygame.font.SysFont(fam, 16)
        self.f_small = pygame.font.SysFont(fam, 13)

        self.bg = self.make_bg()
        self.level_ids = sorted(LEVELS)
        self.initials = {n: SokobanPuzzle(LEVELS[n]) for n in self.level_ids}

        self.cache = {}                 # (niveau, algo) -> résultat
        self.jobs = set()               # niveaux déjà lancés en arrière-plan
        self.lock = threading.Lock()

        self.scene = "menu"
        self.sel = 0                    # carte sélectionnée dans le menu
        self.idx = 0                    # niveau ouvert
        self.algo_idx = 0
        self.delay = 400
        self.hits = []                  # (rect, action) reconstruits à chaque image
        self.menu_rects = []
        self.progress_rect = None
        self.dragging = False
        self.mouse = (0, 0)
        self.reset_sim()

    # ---------- fond
    def make_bg(self):
        return pygame.Surface((W, H)).convert() if pygame.display.get_surface() else pygame.Surface((W, H))

    def start_jobs(self, num):
        if num in self.jobs:
            return
        self.jobs.add(num)
        threading.Thread(target=self._worker, args=(num,), daemon=True).start()

    def _worker(self, num):
        for name in reversed(ALGO_NAMES):
            try:
                init = SokobanPuzzle(LEVELS[num])
                t0 = time.perf_counter()
                goal, expanded = ALGOS[name](init)
                elapsed = time.perf_counter() - t0
                if goal is None:
                    res = {"states": [init], "actions": [], "cost": None,
                           "expanded": expanded, "time": elapsed}
                else:
                    res = {"states": goal.getPath(), "actions": goal.getSolution(),
                           "cost": goal.g, "expanded": expanded, "time": elapsed}
            except Exception:
                res = {"states": [SokobanPuzzle(LEVELS[num])], "actions": [], "cost": None,
                       "expanded": 0, "time": 0.0}
            with self.lock:
                self.cache[(num, name)] = res

    def info(self):
        return self.cache.get((self.level_ids[self.idx], ALGO_NAMES[self.algo_idx]))

    # ---------- simulation
    def reset_sim(self):
        self.step = 0
        self.playing = False
        self.anim_from = None
        self.anim_t0 = 0
        self.facing = "DOWN"
        self.last_tick = pygame.time.get_ticks()

    def set_step(self, new, animate=True):
        info = self.info()
        if not info:
            return
        new = max(0, min(new, len(info["actions"])))
        old = self.step
        if new == old:
            return
        if animate and abs(new - old) == 1:
            self.anim_from = info["states"][old]
            self.anim_t0 = pygame.time.get_ticks()
            self.facing = info["actions"][new - 1] if new > old else OPPOSITE[info["actions"][old - 1]]
        else:
            self.anim_from = None
        self.step = new

    def anim_duration(self):
        return max(60, min(int(self.delay * 0.85), 220))

    # ---------- navigation
    def open_level(self, i):
        self.idx = i % len(self.level_ids)
        self.scene = "play"
        self.start_jobs(self.level_ids[self.idx])
        self.reset_sim()

    def do(self, action):
        kind = action[0]
        info = self.info() if self.scene == "play" else None
        total = len(info["actions"]) if info else 0
        if kind == "open":
            self.open_level(action[1])
        elif kind == "menu":
            self.scene = "menu"
            self.sel = self.idx
        elif kind == "level":
            self.open_level(action[1])
        elif kind == "algo":
            self.algo_idx = action[1]
            self.reset_sim()
        elif kind == "play":
            if info:
                if self.step >= total:
                    self.set_step(0, animate=False)
                self.playing = not self.playing
                self.last_tick = pygame.time.get_ticks()
        elif kind == "prev":
            self.playing = False
            self.set_step(self.step - 1)
        elif kind == "next":
            self.playing = False
            self.set_step(self.step + 1)
        elif kind == "restart":
            self.set_step(0, animate=False)
            self.playing = False
        elif kind == "end":
            self.playing = False
            self.set_step(total, animate=False)
        elif kind == "slower":
            self.delay = min(1500, self.delay + 50)
        elif kind == "faster":
            self.delay = max(50, self.delay - 50)
        elif kind == "seek":
            self.seek(self.mouse[0])
            self.dragging = True

    def seek(self, mx):
        info = self.info()
        if not info or not self.progress_rect:
            return
        frac = (mx - self.progress_rect.x) / self.progress_rect.w
        self.playing = False
        self.set_step(round(max(0, min(1, frac)) * len(info["actions"])), animate=False)

    # ---------- événements
    def handle_key(self, k):
        if self.scene == "menu":
            n = len(self.level_ids)
            if k == pygame.K_ESCAPE:
                return False
            elif k == pygame.K_RIGHT:
                self.sel = min(self.sel + 1, n - 1)
            elif k == pygame.K_LEFT:
                self.sel = max(self.sel - 1, 0)
            elif k == pygame.K_DOWN:
                self.sel = min(self.sel + 3, n - 1)
            elif k == pygame.K_UP:
                self.sel = max(self.sel - 3, 0)
            elif k in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.open_level(self.sel)
            elif pygame.K_1 <= k <= pygame.K_9 and k - pygame.K_1 < n:
                self.open_level(k - pygame.K_1)
            return True

        # scène de jeu
        if k == pygame.K_ESCAPE:
            self.do(("menu",))
        elif k == pygame.K_SPACE:
            self.do(("play",))
        elif k == pygame.K_RIGHT:
            self.do(("next",))
        elif k == pygame.K_LEFT:
            self.do(("prev",))
        elif k == pygame.K_r:
            self.do(("restart",))
        elif k in (pygame.K_UP, pygame.K_DOWN):
            self.open_level(self.idx + (1 if k == pygame.K_DOWN else -1))
        elif k == pygame.K_TAB:
            self.do(("algo", (self.algo_idx + 1) % len(ALGO_NAMES)))
        elif pygame.K_1 <= k <= pygame.K_4 and k - pygame.K_1 < len(ALGO_NAMES):
            self.do(("algo", k - pygame.K_1))
        elif k in (pygame.K_PLUS, pygame.K_KP_PLUS, pygame.K_EQUALS):
            self.do(("faster",))
        elif k in (pygame.K_MINUS, pygame.K_KP_MINUS):
            self.do(("slower",))
        return True

    # ---------- dessin : composants
    def icon_button(self, kind, center, radius, action, primary=False, enabled=True):
        rect = pygame.Rect(0, 0, radius * 2 + 8, radius * 2 + 8)
        rect.center = center
        hover = enabled and rect.collidepoint(self.mouse)
        if primary:
            fill = ACCENT_L if hover else ACCENT
        else:
            fill = (137, 119, 75) if hover else (94, 82, 54)
            
        pygame.draw.rect(self.screen, (55, 45, 27), rect.move(2, 3))
        pygame.draw.rect(self.screen, fill, rect)
        pygame.draw.rect(self.screen, (61, 49, 29), rect, 2)
        
        icon_color = (255, 245, 215) if enabled else (177, 166, 133)
        draw_icon(self.screen, kind, center, radius * (0.42 if primary else 0.38), icon_color)
        
        if enabled:
            self.hits.append((rect, action))

    def card(self, rect, title=None):
        # Hard-edged parchment panel with a thin dark frame.
        pygame.draw.rect(self.screen, (44, 37, 25), rect.move(4, 4))
        pygame.draw.rect(self.screen, CARD, rect)
        pygame.draw.rect(self.screen, CARD_LINE, rect, 3)
        if title:
            draw_text(self.screen, self.f_h2, title, (rect.x + 18, rect.y + 13), TEXT)
            pygame.draw.line(self.screen, (183, 166, 113),
                             (rect.x + 18, rect.y + 42), (rect.right - 18, rect.y + 42), 2)

    def draw_player(self, s, cx, cy, scale, facing, moving, t):
        """Dedicated method to handle rendering the retro pixel-art character"""
        px, py = DIRS[facing]
        walk = math.sin(time.time() * 16) if (moving and t < 1) else 0.0
        
        def block(x, y, w, h, color):
            pygame.draw.rect(s, color, pygame.Rect(int(x), int(y), max(1, int(w)), max(1, int(h))))
            
        # Sprite shadow
        pygame.draw.ellipse(s, (151, 135, 91),
                            (cx - int(9*scale), cy + int(12*scale),
                             max(4, int(18*scale)), max(3, int(5*scale))))
                             
        # Legs and shoes (alternating slightly while walking)
        leg_shift = int(walk * 2 * scale)
        block(cx - 5*scale, cy + 4*scale, 4*scale, 9*scale + leg_shift, (34, 65, 126))
        block(cx + 1*scale, cy + 4*scale, 4*scale, 9*scale - leg_shift, (34, 65, 126))
        block(cx - 6*scale, cy + 11*scale + leg_shift, 5*scale, 3*scale, (28, 29, 31))
        block(cx + 1*scale, cy + 11*scale - leg_shift, 6*scale, 3*scale, (28, 29, 31))
        
        # Arms and blue shirt
        block(cx - 9*scale, cy - 3*scale, 4*scale, 9*scale, (245, 208, 151))
        block(cx + 5*scale, cy - 3*scale, 4*scale, 9*scale, (245, 208, 151))
        block(cx - 6*scale, cy - 5*scale, 12*scale, 11*scale, (29, 91, 180))
        block(cx - 5*scale, cy - 4*scale, 10*scale, 2*scale, (75, 151, 235))
        
        # Neck, face and black hair
        block(cx - 2*scale, cy - 8*scale, 4*scale, 4*scale, (238, 190, 111))
        block(cx - 6*scale, cy - 18*scale, 12*scale, 11*scale, (244, 210, 72))
        block(cx - 7*scale, cy - 19*scale, 14*scale, 5*scale, (20, 20, 18))
        block(cx - 7*scale, cy - 15*scale, 3*scale, 5*scale, (20, 20, 18))
        block(cx + 4*scale, cy - 15*scale, 3*scale, 5*scale, (20, 20, 18))
        
        # Eyes shift subtly with facing direction.
        eye_y = cy - 12*scale + py * 1.2*scale
        if facing in ("LEFT", "RIGHT"):
            eye_x = cx + px * 2*scale
            block(eye_x, eye_y, 2*scale, 2*scale, (18, 18, 17))
        else:
            block(cx - 3*scale, eye_y, 2*scale, 2*scale, (18, 18, 17))
            block(cx + 2*scale, eye_y, 2*scale, 2*scale, (18, 18, 17))

    def draw_board(self, area, state, prev, t, facing):
        s = self.screen
        rows, cols = state.rows, state.cols
        cell = max(1, min(area.w // cols, area.h // rows, 66))
        bw, bh = cell * cols, cell * rows
        ox = area.x + (area.w - bw) // 2
        oy = area.y + (area.h - bh) // 2

        # Outer parchment board and dark edge, like a vintage handheld puzzle.
        outer = pygame.Rect(ox - 12, oy - 12, bw + 24, bh + 24)
        pygame.draw.rect(s, (4, 4, 5), outer.move(5, 6))
        pygame.draw.rect(s, (222, 214, 174), outer)
        pygame.draw.rect(s, (105, 91, 55), outer, 2)

        pulse = 0.5 + 0.5 * math.sin(time.time() * 2.4)

        # Static board tiles. Brick joints are staggered by row.
        for r in range(rows):
            for c in range(cols):
                ch = state.grid[r][c]
                x, y = ox + c * cell, oy + r * cell
                tile = pygame.Rect(x, y, cell, cell)

                if ch == "O":
                    pygame.draw.rect(s, WALL_FACE, tile)
                    mortar = (91, 79, 44)
                    hi = WALL_HI
                    brick_h = max(4, cell // 3)
                    # Top/bottom courses and staggered vertical joints.
                    for k in range(4):
                        yy = y + k * brick_h
                        if yy < y + cell:
                            pygame.draw.line(s, mortar, (x, yy), (x + cell, yy), 1)
                    offset = (cell // 2) if r % 2 else 0
                    for xx in (x + offset, x + offset + cell // 2):
                        if x < xx < x + cell:
                            pygame.draw.line(s, mortar, (xx, y), (xx, y + cell), 1)
                    pygame.draw.line(s, hi, (x + 2, y + 2), (x + cell - 3, y + 2), 1)
                    pygame.draw.line(s, (140, 126, 76), (x + 1, y + cell - 2),
                                     (x + cell - 2, y + cell - 2), 1)
                    continue

                floor = FLOOR_A if (r + c) % 2 == 0 else FLOOR_B
                pygame.draw.rect(s, floor, tile)
                
                # Fixed little sand marks; their pattern does not flicker.
                seed = (r * 17 + c * 29) % 7
                grain = (202, 193, 157)
                for j in range(2):
                    gx = x + 5 + ((seed * 5 + j * 13) % max(8, cell - 10))
                    gy = y + 7 + ((seed * 3 + j * 11) % max(8, cell - 12))
                    pygame.draw.line(s, grain, (gx, gy), (min(x + cell - 3, gx + 4), gy), 1)

                if ch in ("S", "*", "."):
                    rad = max(3, int(cell * (0.15 + 0.015 * pulse)))
                    pygame.draw.circle(s, (199, 119, 105), tile.center, rad)
                    pygame.draw.circle(s, (230, 160, 143),
                                       (tile.centerx - 1, tile.centery - 1), max(1, rad // 3))

        # Smooth step interpolation for boxes and the character.
        moving = prev is not None and t < 1
        te = ease(max(0.0, min(1.0, t)))
        anim_box = {}
        
        if moving:
            cur, old = box_positions(state), box_positions(prev)
            new_boxes, old_boxes = cur - old, old - cur
            if len(new_boxes) == 1 and len(old_boxes) == 1:
                old_pos, new_pos = next(iter(old_boxes)), next(iter(new_boxes))
                anim_box[new_pos] = (lerp(old_pos[0], new_pos[0], te),
                                     lerp(old_pos[1], new_pos[1], te))
            pr, pc = prev.player
            player_pos = (lerp(pr, state.player[0], te),
                          lerp(pc, state.player[1], te))
        else:
            player_pos = state.player

        # Wooden boxes with inset frame and crossed planks.
        for r, c in sorted(box_positions(state)):
            fr, fc = anim_box.get((r, c), (r, c))
            size = max(8, int(cell * 0.80))
            bx = int(ox + (fc + 0.5) * cell - size / 2)
            by = int(oy + (fr + 0.5) * cell - size / 2)
            box = pygame.Rect(bx, by, size, size)
            
            on_goal = state.grid[r][c] == "*"
            wood = BOX_OK if on_goal else BOX_C
            dark = BOX_OK_DARK if on_goal else BOX_DARK
            light = (255, 190, 83) if not on_goal else (221, 145, 57)
            
            pygame.draw.rect(s, (85, 48, 15), box.move(2, 3))
            pygame.draw.rect(s, dark, box)
            
            inner = box.inflate(-max(3, cell // 12), -max(3, cell // 12))
            pygame.draw.rect(s, wood, inner)
            pygame.draw.rect(s, (67, 39, 14), inner, max(1, cell // 18))
            
            plank = max(2, cell // 13)
            # Crossed wooden strips; outline first, then golden center strokes.
            pygame.draw.line(s, dark, inner.topleft, inner.bottomright, plank + 2)
            pygame.draw.line(s, dark, inner.topright, inner.bottomleft, plank + 2)
            pygame.draw.line(s, light, inner.topleft, inner.bottomright, plank)
            pygame.draw.line(s, light, inner.topright, inner.bottomleft, plank)
            pygame.draw.rect(s, (255, 205, 112), inner, 1)
            pygame.draw.rect(s, (65, 38, 15), box, 2)

        # Draw the animated retro human sprite
        cx = int(ox + (player_pos[1] + 0.5) * cell)
        cy = int(oy + (player_pos[0] + 0.5) * cell)
        scale = cell / 42.0
        self.draw_player(s, cx, cy, scale, facing, moving, t)

    def draw_mini(self, rect, grid):
        s = self.screen
        rows, cols = len(grid), len(grid[0])
        cell = max(1, min(rect.w // cols, rect.h // rows))
        ox = rect.x + (rect.w - cell * cols) // 2
        oy = rect.y + (rect.h - cell * rows) // 2
        
        pygame.draw.rect(s, (218, 209, 169), rect)
        
        for r in range(rows):
            for c in range(cols):
                ch = grid[r][c]
                tile = pygame.Rect(ox + c * cell, oy + r * cell, cell, cell)
                if ch == "O":
                    pygame.draw.rect(s, WALL_FACE, tile)
                    mortar = (91, 79, 44)
                    for k in range(1, 3):
                        yy = tile.y + k * cell // 3
                        pygame.draw.line(s, mortar, (tile.x, yy), (tile.right, yy), 1)
                    joint = tile.centerx + (cell // 4 if r % 2 else -cell // 4)
                    if tile.x < joint < tile.right:
                        pygame.draw.line(s, mortar, (joint, tile.y), (joint, tile.bottom), 1)
                    continue
                    
                pygame.draw.rect(s, FLOOR_A, tile)
                
                if ch in ("S", "*", "."):
                    pygame.draw.circle(s, TARGET, tile.center, max(1, cell // 5))
                    
                if ch in ("B", "*"):
                    box = tile.inflate(-max(2, cell // 5), -max(2, cell // 5))
                    pygame.draw.rect(s, BOX_DARK, box)
                    pygame.draw.rect(s, BOX_C, box.inflate(-2, -2))
                    pygame.draw.line(s, BOX_DARK, box.topleft, box.bottomright, 1)
                    pygame.draw.line(s, BOX_DARK, box.topright, box.bottomleft, 1)
                    
                if ch in ("R", "."):
                    px, py = tile.center
                    unit = max(1, cell // 8)
                    pygame.draw.rect(s, (20, 20, 18),
                                     (px - 2*unit, py - 4*unit, 4*unit, 2*unit))
                    pygame.draw.rect(s, (244, 210, 72),
                                     (px - 2*unit, py - 2*unit, 4*unit, 3*unit))
                    pygame.draw.rect(s, PLAYER_C,
                                     (px - 2*unit, py + unit, 4*unit, 4*unit))

    def draw_menu(self):
        s = self.screen
        s.fill(BG_TOP)
        cx = W // 2
        draw_text(s, self.f_title, "SOKOBAN", (cx, 34), (236, 219, 157), "midtop")
        draw_text(s, self.f_body, "Choisis un niveau", (cx, 105), (196, 181, 137), "midtop")

        self.menu_rects = []
        n = len(self.level_ids)
        cw, ch, gap = 230, 240, 24
        
        for i, num in enumerate(self.level_ids):
            row, col = divmod(i, 3)
            items = min(3, n - row * 3)
            x0 = (W - (items * cw + (items - 1) * gap)) // 2
            base = pygame.Rect(x0 + col * (cw + gap), 170 + row * (ch + gap), cw, ch)
            selected = i == self.sel
            rect = base
            self.menu_rects.append(base)

            pygame.draw.rect(s, (3, 3, 4), rect.move(5, 6))
            pygame.draw.rect(s, CARD_HI if selected else CARD, rect)
            pygame.draw.rect(s, ACCENT if selected else CARD_LINE, rect, 3 if selected else 2)

            preview = pygame.Rect(rect.x + 14, rect.y + 14, cw - 28, 150)
            pygame.draw.rect(s, (216, 207, 165), preview)
            self.draw_mini(preview.inflate(-12, -12), LEVELS[num])

            grid = LEVELS[num]
            boxes = sum(row_.count("B") + row_.count("*") for row_ in grid)
            draw_text(s, self.f_h2, f"NIVEAU {num}", (rect.x + 18, rect.y + 176), TEXT)
            draw_text(s, self.f_small,
                      f"{boxes} caisse(s)  |  {len(grid)} x {len(grid[0])}",
                      (rect.x + 18, rect.y + 208), DIM)
                      
            btn = pygame.Rect(rect.right - 49, rect.y + 178, 32, 32)
            pygame.draw.rect(s, (91, 67, 32), btn)
            pygame.draw.rect(s, ACCENT if selected else (173, 132, 66), btn.inflate(-3, -3))
            draw_icon(s, "play", btn.center, 7, (255, 247, 218))
            self.hits.append((rect, ("open", i)))

        draw_text(s, self.f_small,
                  "Flèches : naviguer   |   Entrée : ouvrir   |   Échap : quitter",
                  (cx, H - 28), (164, 150, 113), "midtop")

    def draw_play(self):
        s = self.screen
        s.fill(BG_TOP)
        num = self.level_ids[self.idx]
        algo = ALGO_NAMES[self.algo_idx]
        info = self.info()

        # Top line and level navigation.
        back = pygame.Rect(26, 22, 102, 38)
        pygame.draw.rect(s, (91, 67, 32), back.move(3, 3))
        pygame.draw.rect(s, CARD, back)
        pygame.draw.rect(s, CARD_LINE, back, 2)
        draw_icon(s, "back", (back.x + 20, back.centery), 7, TEXT)
        draw_text(s, self.f_bold, "Menu", (back.x + 39, back.centery), TEXT, "midleft")
        self.hits.append((back, ("menu",)))
        draw_text(s, self.f_h1, f"NIVEAU {num}", (150, 42), (236, 219, 157), "midleft")

        chip, gap = 34, 7
        x = W - 26 - (len(self.level_ids) * chip + (len(self.level_ids) - 1) * gap)
        for i, lid in enumerate(self.level_ids):
            r = pygame.Rect(x + i * (chip + gap), 24, chip, chip)
            active = i == self.idx
            pygame.draw.rect(s, ACCENT if active else CARD, r)
            pygame.draw.rect(s, (71, 51, 27), r, 2)
            draw_text(s, self.f_bold, str(lid), r.center,
                      (255, 248, 226) if active else TEXT, "center")
            self.hits.append((r, ("level", i)))

        # Board simulation.
        if self.anim_from is not None:
            t = (pygame.time.get_ticks() - self.anim_t0) / self.anim_duration()
            if t >= 1:
                self.anim_from, t = None, 1
        else:
            t = 1
            
        state = info["states"][self.step] if info else self.initials[num]
        self.draw_board(BOARD_AREA, state, self.anim_from, t, self.facing)

        if not info:
            veil = pygame.Surface(BOARD_AREA.size, pygame.SRCALPHA)
            veil.fill((20, 18, 12, 155))
            s.blit(veil, BOARD_AREA.topleft)
            draw_spinner(s, BOARD_AREA.center, 20, ACCENT_L, 4)
            draw_text(s, self.f_body, f"Calcul de {algo}...",
                      (BOARD_AREA.centerx, BOARD_AREA.centery + 30), (255, 245, 215), "midtop")
        elif info["cost"] is None:
            self.banner("cross", "Pas de solution", RED)
        elif self.step == len(info["actions"]) and t >= 1:
            self.banner("check", f"Niveau résolu en {info['cost']} coups", GREEN)

        self.draw_algo_card(num, algo)
        self.draw_sim_card(info, algo)
        draw_text(s, self.f_small,
                  "Espace : lecture/pause   Flèches : pas à pas   Tab : algorithme   Échap : menu",
                  (W // 2, H - 22), (151, 138, 105), "midtop")

    def banner(self, icon, label, color):
        s = self.screen
        img = self.f_bold.render(label, True, (255, 249, 226))
        rect = pygame.Rect(0, 0, img.get_width() + 62, 42)
        rect.midtop = (BOARD_AREA.centerx, BOARD_AREA.y + 8)
        pygame.draw.rect(s, (60, 43, 21), rect.move(3, 3))
        pygame.draw.rect(s, color, rect)
        pygame.draw.rect(s, (61, 43, 21), rect, 2)
        draw_icon(s, icon, (rect.x + 22, rect.centery), 7, (255, 249, 226))
        s.blit(img, (rect.x + 42, rect.centery - img.get_height() // 2))

    def draw_algo_card(self, num, algo):
        s = self.screen
        rect = pygame.Rect(PANEL_X, 96, PANEL_W, 260)
        self.card(rect, "ALGORITHMES")
        results = [self.cache.get((num, name)) for name in ALGO_NAMES]

        for i, name in enumerate(ALGO_NAMES):
            col = ALGO_COLORS[i % len(ALGO_COLORS)]
            row = pygame.Rect(rect.x + 12, rect.y + 50 + i * 48, rect.w - 24, 43)
            selected = name == algo
            
            if selected:
                pygame.draw.rect(s, (248, 235, 195), row)
                pygame.draw.rect(s, col, row, 2)
            elif row.collidepoint(self.mouse):
                pygame.draw.rect(s, (219, 208, 171), row)

            pygame.draw.rect(s, col, (row.x + 10, row.y + 10, 10, 10))
            draw_text(s, self.f_bold, name, (row.x + 29, row.y + 4), TEXT)
            
            result = results[i]
            if result is None:
                detail = "Calcul..."
                elapsed = ""
            else:
                detail = ("Aucune solution" if result["cost"] is None
                          else f"Coût {result['cost']}  |  {result['expanded']} noeuds")
                elapsed = f"{result['time']:.3f} s"
                
            draw_text(s, self.f_small, detail, (row.x + 29, row.y + 24), DIM)
            if elapsed:
                draw_text(s, self.f_small, elapsed, (row.right - 8, row.y + 8), TEXT, "topright")
            if result is None:
                draw_spinner(s, (row.right - 18, row.y + 16), 6, col, 2)
                
            self.hits.append((row, ("algo", i)))

    def draw_sim_card(self, info, algo):
        s = self.screen
        rect = pygame.Rect(PANEL_X, 372, PANEL_W, 328)
        self.card(rect, "SIMULATION")
        col = ALGO_COLORS[self.algo_idx % len(ALGO_COLORS)]
        draw_text(s, self.f_small, algo, (rect.right - 18, rect.y + 21), col, "topright")

        total = len(info["actions"]) if info else 0
        action = info["actions"][self.step - 1] if info and self.step > 0 else None
        
        draw_text(s, self.f_small, "ÉTAPE", (rect.x + 18, rect.y + 58), DIM)
        draw_text(s, self.f_h1, f"{self.step} / {total}", (rect.x + 18, rect.y + 76), TEXT)
        
        draw_text(s, self.f_small, "MOUVEMENT", (rect.x + 190, rect.y + 58), DIM)
        move_label = DIR_FR[action] if action else "Départ"
        draw_text(s, self.f_h2, move_label, (rect.x + 190, rect.y + 80), TEXT if action else DIM)

        # Progress track and percentage.
        progress_y = rect.y + 137
        draw_text(s, self.f_small, "PROGRESSION", (rect.x + 18, progress_y), DIM)
        frac = self.step / total if total else 0.0
        draw_text(s, self.f_small, f"{int(frac * 100)}%", (rect.right - 18, progress_y), TEXT, "topright")
        
        bar = pygame.Rect(rect.x + 18, rect.y + 161, rect.w - 36, 9)
        self.progress_rect = bar
        pygame.draw.rect(s, (193, 181, 143), bar)
        if frac > 0:
            pygame.draw.rect(s, col, (bar.x, bar.y, max(7, int(bar.w * frac)), bar.h))
            
        knob_x = bar.x + int(bar.w * frac)
        pygame.draw.rect(s, (255, 248, 224), (knob_x - 5, bar.y - 4, 10, 17))
        pygame.draw.rect(s, (74, 56, 30), (knob_x - 5, bar.y - 4, 10, 17), 1)
        if info:
            self.hits.append((bar.inflate(16, 22), ("seek",)))

        # Five compact, square arcade buttons.
        cy = rect.y + 222
        cx = rect.centerx
        enabled = bool(info)
        controls = [
            ("restart", cx - 112, 15, False, ("restart",)),
            ("prev", cx - 56, 16, False, ("prev",)),
            ("pause" if self.playing else "play", cx, 22, True, ("play",)),
            ("next", cx + 56, 16, False, ("next",)),
            ("end", cx + 112, 15, False, ("end",)),
        ]
        
        for kind, x, radius, primary, action_data in controls:
            self.icon_button(kind, (x, cy), radius, action_data,
                             primary=primary, enabled=enabled)

        speed_y = rect.y + 286
        draw_text(s, self.f_body, "Vitesse", (rect.x + 18, speed_y), DIM, "midleft")
        self.icon_button("minus", (rect.right - 155, speed_y), 11, ("slower",))
        draw_text(s, self.f_bold, f"{self.delay} ms", (rect.right - 95, speed_y), TEXT, "center")
        self.icon_button("plus", (rect.right - 38, speed_y), 11, ("faster",))

    def run(self):
        running = True
        while running:
            self.mouse = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    running = self.handle_key(event.key) and running
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for rect, action in reversed(self.hits):
                        if rect.collidepoint(event.pos):
                            self.do(action)
                            break
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self.dragging = False
                elif event.type == pygame.MOUSEMOTION:
                    self.mouse = event.pos
                    if self.dragging:
                        self.seek(event.pos[0])
                    elif self.scene == "menu":
                        for i, r in enumerate(self.menu_rects):
                            if r.collidepoint(event.pos):
                                self.sel = i

            # lecture automatique
            now = pygame.time.get_ticks()
            info = self.info() if self.scene == "play" else None
            
            if self.playing and info and now - self.last_tick >= self.delay:
                self.last_tick = now
                if self.step < len(info["actions"]):
                    self.set_step(self.step + 1)
                else:
                    self.playing = False
                    
            if self.playing and info and self.step >= len(info["actions"]) and self.anim_from is None:
                self.playing = False

            self.hits = []
            
            if self.scene == "menu":
                self.draw_menu()
            else:
                self.draw_play()
                
            pygame.display.flip()
            self.clock.tick(60)
            
        pygame.quit()

def main():
    App().run()

if __name__ == "__main__":
    main()