# sokoban_puzzle.py

class SokobanPuzzle:
    # Les 4 actions : nom -> (delta ligne, delta colonne)
    ACTIONS = {
        "UP":    (-1, 0),
        "DOWN":  (1, 0),
        "LEFT":  (0, -1),
        "RIGHT": (0, 1),
    }

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

    # Pour comparer des états et les mettre dans un set (utile pour BFS)
    def __eq__(self, other):
        return self.grid == other.grid

    def __hash__(self):
        return hash(self.grid)

    def __str__(self):
        return "\n".join(self.grid)