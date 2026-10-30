# astar.py
import heapq
from itertools import count
from node import Node


def astar(initial_state, heuristic):
    
    root = Node(initial_state)
    root.setF(heuristic)

    tie = count()                                   
    frontier = [(root.f, next(tie), root)]          
    best_g = {initial_state: 0}                     
    expanded = 0

    while frontier:
        _, _, node = heapq.heappop(frontier)
        
        if node.state.isGoal():
                    return node, expanded                               

        expanded += 1
        for action, succ in node.state.successorFunction():
            g = node.g + 1
            if g < best_g.get(succ, float("inf")):
                best_g[succ] = g
                child = Node(succ, parent=node, action=action, g=g)
                child.setF(heuristic)
                heapq.heappush(frontier, (child.f, next(tie), child))

    return None, expanded
