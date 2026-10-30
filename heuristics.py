# heuristics.py
# Chaque heuristique prend un état (SokobanPuzzle) et renvoie un nombre.
from itertools import permutations


def _positions(state):
    
    boxes, targets = [], []
    for r, row in enumerate(state.grid):
        for c, ch in enumerate(row):
            if ch in ("B", "*"):
                boxes.append((r, c))
            if ch in ("S", "*", "."):
                targets.append((r, c))
    return boxes, targets, state.player


def _manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


DEADLOCK = 10_000


def _in_corner(state, r, c):
    wall = lambda rr, cc: state.grid[rr][cc] == "O"
    return ((wall(r - 1, c) or wall(r + 1, c)) and
            (wall(r, c - 1) or wall(r, c + 1)))


def nb_left_blocks(state):
    # caisses pas encore sur une cible = caisses 'B'
    return sum(row.count("B") for row in state.grid)


def h1(state):
    """h1(n) = nombre de caisses pas encore placées sur une cible."""
    return nb_left_blocks(state)


def h2(state):
    
    boxes, targets, _ = _positions(state)
    total = 2 * nb_left_blocks(state)
    for b in boxes:
        total += min(_manhattan(b, t) for t in targets)
    return total


def h3(state):
    
    if nb_left_blocks(state) == 0:
        return 0
    boxes, targets, player = _positions(state)

    # Blocage simple : une caisse 'B' coincée dans un coin ne pourra plus jamais
    # bouger -> état perdu, on le pénalise fortement (élagage).
    for r, c in boxes:
        if state.grid[r][c] == "B" and _in_corner(state, r, c):
            return DEADLOCK

    best = min(
        sum(_manhattan(b, t) for b, t in zip(boxes, perm))
        for perm in permutations(targets, len(boxes))
    )
    walk = min(_manhattan(player, b) for b in boxes) - 1
    return best + max(walk, 0)
