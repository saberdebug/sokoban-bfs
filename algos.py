# algos.py : liste des algorithmes disponibles (nom -> fonction de résolution)
from bfs import bfs
from astar import astar
from heuristics import h1, h2, h3

ALGOS = {
    "BFS":       lambda s: bfs(s),
    "A* (h1)":   lambda s: astar(s, h1),
    "A* (h2)":   lambda s: astar(s, h2),
    "A* (h3)":   lambda s: astar(s, h3),
}
