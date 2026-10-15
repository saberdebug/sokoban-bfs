# bfs.py
from collections import deque
from node import Node

def bfs(initial_state):
    root = Node(initial_state)

    if initial_state.isGoal():
        return root, 0

    frontier = deque([root])        # file FIFO
    explored = {initial_state}      # états déjà vus (grâce à __hash__ / __eq__)
    expanded = 0                    # nombre de nœuds développés

    while frontier:
        node = frontier.popleft()
        expanded += 1

        for action, succ in node.state.successorFunction():
            if succ in explored:
                continue
            child = Node(succ, parent=node, action=action, g=node.g + 1)
            if succ.isGoal():
                return child, expanded
            explored.add(succ)
            frontier.append(child)

    return None, expanded           # aucune solution