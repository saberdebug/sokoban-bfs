# interface.py
# Interface Pygame : simulation de la solution + comparaison BFS / A* (h1, h2, h3).
# Lancer avec :  python interface.py
#
# Commandes :
#   ESPACE        : lecture / pause
#   GAUCHE/DROITE : pas en arrière / en avant
#   HAUT/BAS      : changer de niveau
#   TAB ou 1-4    : changer d'algorithme (BFS, A* h1, A* h2, A* h3)
#   R             : recommencer
#   + / -         : vitesse de la simulation

import time
import pygame

from levels import LEVELS
from sokoban_puzzle import SokobanPuzzle
from algos import ALGOS

# ---------- Constantes ----------
WIN_W, WIN_H = 1000, 660
BOARD_SIZE = 600
PANEL_X = BOARD_SIZE + 20

BG        = (30, 30, 36)
WALL      = (90, 90, 100)
WALL_LINE = (60, 60, 68)
FLOOR     = (240, 220, 180)
TARGET    = (200, 60, 60)
BOX       = (140, 85, 40)
BOX_OK    = (60, 170, 80)
PLAYER    = (50, 110, 220)
TEXT      = (235, 235, 235)
DIM       = (150, 150, 160)
SELECT_BG = (60, 70, 100)

ALGO_NAMES = list(ALGOS.keys())


# ---------- Résolution (avec cache) ----------
cache = {}   # (niveau, algo) -> résultat

def solve(level_num, algo):
    key = (level_num, algo)
    if key not in cache:
        init = SokobanPuzzle(LEVELS[level_num])
        t0 = time.time()
        goal, expanded = ALGOS[algo](init)
        elapsed = time.time() - t0
        if goal is None:
            cache[key] = {"states": [init], "actions": [], "cost": None,
                          "expanded": expanded, "time": elapsed}
        else:
            cache[key] = {"states": goal.getPath(), "actions": goal.getSolution(),
                          "cost": goal.g, "expanded": expanded, "time": elapsed}
    return cache[key]


# ---------- Dessin ----------
def draw_board(screen, state):
    rows, cols = state.rows, state.cols
    cell = min(BOARD_SIZE // cols, BOARD_SIZE // rows, 70)
    ox = (BOARD_SIZE - cell * cols) // 2 + 10
    oy = (BOARD_SIZE - rows * cell) // 2 + 20

    for r in range(rows):
        for c in range(cols):
            ch = state.grid[r][c]
            rect = pygame.Rect(ox + c * cell, oy + r * cell, cell, cell)
            cx, cy = rect.center

            if ch == "O":
                pygame.draw.rect(screen, WALL, rect)
                pygame.draw.rect(screen, WALL_LINE, rect, 2)
                continue

            pygame.draw.rect(screen, FLOOR, rect)
            pygame.draw.rect(screen, (220, 200, 160), rect, 1)

            if ch in ("S", "*", "."):
                pygame.draw.circle(screen, TARGET, (cx, cy), cell // 6)

            if ch in ("B", "*"):
                color = BOX_OK if ch == "*" else BOX
                inner = rect.inflate(-cell // 5, -cell // 5)
                pygame.draw.rect(screen, color, inner, border_radius=4)
                pygame.draw.rect(screen, (0, 0, 0), inner, 2, border_radius=4)

            if ch in ("R", "."):
                pygame.draw.circle(screen, PLAYER, (cx, cy), cell // 3)
                pygame.draw.circle(screen, (0, 0, 0), (cx, cy), cell // 3, 2)


def draw_text(screen, font, text, x, y, color=TEXT):
    screen.blit(font.render(text, True, color), (x, y))


def draw_panel(screen, fonts, level_num, algo, info, step, playing, delay):
    big, mid, small = fonts
    draw_text(screen, big, f"Niveau {level_num}", PANEL_X, 15)

    # --- tableau comparatif des algorithmes ---
    y = 65
    draw_text(screen, small, "Algorithme", PANEL_X, y, DIM)
    draw_text(screen, small, "Coût", PANEL_X + 130, y, DIM)
    draw_text(screen, small, "Nœuds", PANEL_X + 190, y, DIM)
    draw_text(screen, small, "Temps", PANEL_X + 270, y, DIM)
    y += 24
    for i, name in enumerate(ALGO_NAMES):
        res = cache.get((level_num, name))
        if name == algo:
            pygame.draw.rect(screen, SELECT_BG,
                             (PANEL_X - 6, y - 2, WIN_W - PANEL_X - 8, 24), border_radius=4)
        draw_text(screen, small, f"{i + 1}. {name}", PANEL_X, y)
        if res:
            cost = "-" if res["cost"] is None else str(res["cost"])
            draw_text(screen, small, cost, PANEL_X + 130, y)
            draw_text(screen, small, str(res["expanded"]), PANEL_X + 190, y)
            draw_text(screen, small, f"{res['time']:.2f}s", PANEL_X + 270, y)
        y += 26

    # --- simulation en cours ---
    y += 20
    draw_text(screen, mid, f"Simulation : {algo}", PANEL_X, y)
    y += 35
    if info["cost"] is None:
        draw_text(screen, mid, "Pas de solution", PANEL_X, y, (230, 90, 90))
    else:
        draw_text(screen, mid, f"Coût : {info['cost']}", PANEL_X, y)
    y += 30
    total = len(info["actions"])
    draw_text(screen, mid, f"Étape : {step} / {total}", PANEL_X, y)
    y += 30
    action = info["actions"][step - 1] if step > 0 else "-"
    draw_text(screen, mid, f"Action : {action}", PANEL_X, y)
    y += 30
    draw_text(screen, mid, f"{'Lecture' if playing else 'Pause'}  ({delay} ms/pas)", PANEL_X, y)
    y += 35
    if info["cost"] is not None and step == total:
        draw_text(screen, mid, "Niveau résolu !", PANEL_X, y, BOX_OK)

    help_lines = [
        "ESPACE : lecture / pause",
        "← → : pas arrière / avant",
        "↑ ↓ : changer de niveau",
        "TAB ou 1-4 : changer d'algorithme",
        "R : recommencer   + / - : vitesse",
    ]
    for i, line in enumerate(help_lines):
        draw_text(screen, small, line, PANEL_X, 545 + i * 22, DIM)


# ---------- Programme principal ----------
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption("Sokoban - BFS et A*")
    clock = pygame.time.Clock()
    fonts = (pygame.font.SysFont("arial", 32, bold=True),
             pygame.font.SysFont("arial", 22),
             pygame.font.SysFont("arial", 17))

    level_ids = sorted(LEVELS.keys())
    idx, algo_idx = 0, 0
    step, playing = 0, False
    delay = 400
    last_tick = pygame.time.get_ticks()

    def load_level(i):
        """Résout le niveau avec tous les algorithmes (une seule fois)."""
        num = level_ids[i]
        for name in ALGO_NAMES:
            if (num, name) not in cache:
                screen.fill(BG)
                draw_text(screen, fonts[1], f"Niveau {num} : calcul de {name}...", 40, 40)
                pygame.display.flip()
                pygame.event.pump()
                solve(num, name)

    load_level(idx)
    info = solve(level_ids[idx], ALGO_NAMES[algo_idx])
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                k = event.key
                if k == pygame.K_ESCAPE:
                    running = False
                elif k == pygame.K_SPACE:
                    if step >= len(info["actions"]):
                        step = 0
                    playing = not playing
                elif k == pygame.K_RIGHT:
                    playing = False
                    step = min(step + 1, len(info["actions"]))
                elif k == pygame.K_LEFT:
                    playing = False
                    step = max(step - 1, 0)
                elif k == pygame.K_r:
                    step, playing = 0, False
                elif k in (pygame.K_UP, pygame.K_DOWN):
                    idx = (idx + (1 if k == pygame.K_DOWN else -1)) % len(level_ids)
                    load_level(idx)
                    info = solve(level_ids[idx], ALGO_NAMES[algo_idx])
                    step, playing = 0, False
                elif k == pygame.K_TAB or pygame.K_1 <= k <= pygame.K_4:
                    if k == pygame.K_TAB:
                        algo_idx = (algo_idx + 1) % len(ALGO_NAMES)
                    else:
                        algo_idx = k - pygame.K_1
                    info = solve(level_ids[idx], ALGO_NAMES[algo_idx])
                    step, playing = 0, False
                elif k in (pygame.K_PLUS, pygame.K_KP_PLUS, pygame.K_EQUALS):
                    delay = max(50, delay - 50)
                elif k in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    delay = min(1500, delay + 50)

        now = pygame.time.get_ticks()
        if playing and now - last_tick >= delay:
            last_tick = now
            if step < len(info["actions"]):
                step += 1
            else:
                playing = False

        screen.fill(BG)
        draw_board(screen, info["states"][step])
        draw_panel(screen, fonts, level_ids[idx], ALGO_NAMES[algo_idx], info,
                   step, playing, delay)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
