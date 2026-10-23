import time
from levels import LEVELS
from sokoban_puzzle import SokobanPuzzle
from algos import ALGOS

for num, grid in LEVELS.items():
    print(f"\n--- Niveau {num} ---")
    print(f"{'Algorithme':<10} {'Coût':>5} {'Nœuds développés':>18} {'Temps (s)':>10}")
    for name, solve in ALGOS.items():
        t0 = time.time()
        goal, expanded = solve(SokobanPuzzle(grid))
        dt = time.time() - t0
        cost = goal.g if goal else "-"
        print(f"{name:<10} {str(cost):>5} {expanded:>18} {dt:>10.3f}")
        if goal:
            print("   Solution :", goal.getSolution())
        else:
            print("   Pas de solution")
