# sokoban_puzzle.py

class SokobanPuzzle:
    # Les 4 actions : nom -> (delta ligne, delta colonne)
    ACTIONS = {
        "UP":    (-1, 0),
        "DOWN":  (1, 0),
        "LEFT":  (0, -1),
        "RIGHT": (0, 1),
    }
    _dead_cache = {}   # layout -> set of dead cells (computed once per level)

    def __init__(self, grid):
        # Grille stockée en tuple de chaînes (immuable -> utilisable dans un set)
        self.grid = tuple(grid)
        self.rows = len(self.grid)
        self.cols = len(self.grid[0])
        self.player = self._find_player()

    def _find_player(self):
        # Le joueur est 'R' ou '.' (joueur sur une cible)
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] in ("R", "."):
                    return (r, c)
        return None

    def isGoal(self):
        # But atteint : plus aucune caisse hors cible, donc plus de 'B'
        return not any("B" in row for row in self.grid)

    def successorFunction(self):
        successors = []
        r, c = self.player

        for action, (dr, dc) in self.ACTIONS.items():
            nr, nc = r + dr, c + dc          # case où le joueur veut aller
            target = self.grid[nr][nc]

            # 1) Mur : mouvement interdit
            if target == "O":
                continue

            # Copie de la grille en liste de listes pour la modifier
            new = [list(row) for row in self.grid]

            # 2) Caisse : on regarde la case derrière elle
            if target in ("B", "*"):
                br, bc = nr + dr, nc + dc
                beyond = self.grid[br][bc]
                if beyond not in (" ", "S"):  # mur ou autre caisse : interdit
                    continue
                new[br][bc] = "B" if beyond == " " else "*"

            # 3) Le joueur quitte sa case
            new[r][c] = " " if self.grid[r][c] == "R" else "S"

            # 4) Le joueur arrive sur sa nouvelle case
            new[nr][nc] = "R" if target in (" ", "B") else "."

            new_state = SokobanPuzzle(["".join(row) for row in new])
            successors.append((action, new_state))

        return successors

    def _is_target(self, r, c):
        return self.grid[r][c] in ("S", "*", ".")

    def _line_dead(self, r, c, dr, dc, wr, wc):
        # (dr, dc) : direction along the line the box can slide
        # (wr, wc) : direction of the wall the box is against
        for sign in (1, -1):
            rr, cc = r, c
            while self.grid[rr][cc] != "O":
                # the wall side opens up -> the box can escape, not a deadlock
                if self.grid[rr + wr][cc + wc] != "O":
                    return False
                # a target on the line -> the box can still be solved
                if self._is_target(rr, cc):
                    return False
                rr += sign * dr
                cc += sign * dc
        return True   # whole line checked: no target and no way out

    def _compute_dead(self):
        dead = set()
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == "O" or self._is_target(r, c):
                    continue
                wall_v = self.grid[r - 1][c] == "O" or self.grid[r + 1][c] == "O"
                wall_h = self.grid[r][c - 1] == "O" or self.grid[r][c + 1] == "O"
                if wall_v and wall_h:                      # corner
                    dead.add((r, c))
                    continue
                for wr in (-1, 1):                         # line along top/bottom wall
                    if self.grid[r + wr][c] == "O" and self._line_dead(r, c, 0, 1, wr, 0):
                        dead.add((r, c))
                for wc in (-1, 1):                         # line along left/right wall
                    if self.grid[r][c + wc] == "O" and self._line_dead(r, c, 1, 0, 0, wc):
                        dead.add((r, c))
        return dead

    def dead_lock(self):
        # layout without boxes/player = same key for every state of a level
        key = tuple(row.replace("R", " ").replace("B", " ")
                       .replace("*", "S").replace(".", "S") for row in self.grid)
        if key not in SokobanPuzzle._dead_cache:
            SokobanPuzzle._dead_cache[key] = self._compute_dead()
        dead = SokobanPuzzle._dead_cache[key]

        return any(self.grid[r][c] == "B" and (r, c) in dead
                   for r in range(self.rows) for c in range(self.cols))
        
    # Pour comparer des états et les mettre dans un set (utile pour BFS)
    def __eq__(self, other):
        return self.grid == other.grid

    def __hash__(self):
        return hash(self.grid)

    def __str__(self):
        return "\n".join(self.grid)