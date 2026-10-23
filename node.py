# node.py

class Node:
    def __init__(self, state, parent=None, action=None, g=0):
        self.state = state      # instance de SokobanPuzzle
        self.parent = parent    # nœud parent (None pour la racine)
        self.action = action    # action appliquée au parent pour arriver ici
        self.g = g              # coût du chemin (chaque pas coûte 1)
        self.f = g              # fonction d'évaluation de A* : f = g + h

    def setF(self, heuristic):
        # f(n) = g(n) + h(n), h étant une fonction heuristique(state) -> nombre
        self.f = self.g + heuristic(self.state)
        return self.f

    def getPath(self):
        # Liste des états du départ jusqu'au but
        path = []
        node = self
        while node is not None:
            path.append(node.state)
            node = node.parent
        path.reverse()
        return path

    def getSolution(self):
        # Liste des actions du départ jusqu'au but
        actions = []
        node = self
        while node.parent is not None:
            actions.append(node.action)
            node = node.parent
        actions.reverse()
        return actions
