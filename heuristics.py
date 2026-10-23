# heuristics.py
# Chaque heuristique prend un état (SokobanPuzzle) et renvoie un nombre.
from itertools import permutations


def _positions(state):
    """Retourne (caisses, cibles, joueur) sous forme de listes de (ligne, colonne)."""
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
    """h2(n) = 2 * nb_left_blocks + somme, pour chaque caisse, de la distance
    de Manhattan à la cible la plus proche."""
    boxes, targets, _ = _positions(state)
    total = 2 * nb_left_blocks(state)
    for b in boxes:
        total += min(_manhattan(b, t) for t in targets)
    return total


def h3(state):
    """h3 (proposée) = coût minimal d'affectation caisses -> cibles (distances de
    Manhattan, chaque cible utilisée une seule fois)
    + distance joueur -> caisse la plus proche (moins 1 : le joueur doit se
    placer à côté d'une caisse avant la première poussée).

    Un blocage de coin est en plus détecté (état perdu -> h très grande).

    Contrairement à h2 (qui laisse deux caisses viser la même cible), h3 impose
    une affectation 1-1, donc elle est plus informée. Elle reste admissible (un état perdu n'a aucune solution) :
    chaque poussée coûte 1 et déplace une caisse d'une case, et le joueur doit
    marcher au moins dist-1 pas avant de pousser."""
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
