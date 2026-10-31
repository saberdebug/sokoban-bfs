# astar.py
import heapq
from itertools import count
from node import Node


def astar(initial_state, heuristic):
    tie = count()                       # départage les f égaux dans le heap

    root = Node(initial_state)
    root.setF(heuristic)                # f = g + h = 0 + h(root)

    open_heap = [(root.f, next(tie), root)]   # Open : file de priorité sur f
    open_dict = {initial_state: root}         # Open : état -> nœud (accès rapide)
    closed = {}                               # Closed : état -> nœud
    expanded = 0

    while open_heap:
        _, _, current = heapq.heappop(open_heap)

        # entrée obsolète (nœud remplacé dans Open) -> on l'ignore
        if open_dict.get(current.state) is not current:
            continue
        del open_dict[current.state]

        # test du but au moment où on sort le nœud de Open (comme dans le PDF)
        if current.state.isGoal():
            return current, expanded

        closed[current.state] = current       # Closed.add(current)
        expanded += 1

        for action, succ in current.state.successorFunction():
                            
             if succ.dead_lock():
                continue
            
             child = Node(succ, parent=current, action=action, g=current.g + 1)
             child.setF(heuristic)

             if succ not in open_dict and succ not in closed:
                # ni dans Open ni dans Closed -> insérer
                open_dict[succ] = child
                heapq.heappush(open_heap, (child.f, next(tie), child))

             elif succ in open_dict and open_dict[succ].f > child.f:
                # dans Open avec f plus grand -> remplacer
                open_dict[succ] = child
                heapq.heappush(open_heap, (child.f, next(tie), child))

             elif succ in closed and closed[succ].f > child.f:
                # dans Closed avec f plus grand -> retirer de Closed, insérer dans Open
                del closed[succ]
                open_dict[succ] = child
                heapq.heappush(open_heap, (child.f, next(tie), child))

    return None, expanded