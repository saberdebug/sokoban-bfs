
from levels import LEVELS
from sokoban_puzzle import SokobanPuzzle
from bfs import bfs

for num, grid in LEVELS.items():
   
    goal, expanded = bfs(SokobanPuzzle(grid))
   

    print(f"\n--- Niveau {num} ---")
    if goal is None:
        print("Pas de solution")
    else:
        print("Coût :", goal.g)
        print("Nœuds développés :", expanded)
        print("Solution :", goal.getSolution())
   