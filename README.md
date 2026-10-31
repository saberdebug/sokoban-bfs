# Sokoban Solver : BFS et A*

Projet 1 de Résolution de Problèmes (Master 1 Visual Computing, USTHB).
Modélisation du jeu Sokoban, résolution par **BFS** et **A\*** (3 heuristiques), et interface **Pygame** pour visualiser les solutions.

## Installation

```bash
pip install pygame
```

Python 3.8+ est suffisant. `main.py` n'a besoin d'aucune dépendance externe.

## Lancer le projet

| Commande | Rôle |
|---|---|
| `python main.py` | Résout les 5 niveaux avec chaque algorithme et affiche le coût, le nombre de nœuds développés et le temps |
| `python interface.py` | Ouvre l'interface Pygame (menu des niveaux + simulation animée de la solution) |
| `python test.py` | Petit test de la détection de deadlock |

## Structure du projet

| Fichier | Contenu |
|---|---|
| `sokoban_puzzle.py` | Classe `SokobanPuzzle` : état, `isGoal()`, `successorFunction()`, `dead_lock()` |
| `node.py` | Classe `Node` : `state, parent, action, g, f`, `getPath()`, `getSolution()`, `setF()` |
| `bfs.py` | Recherche en largeur (BFS) |
| `astar.py` | Recherche A* (avec élagage des deadlocks) |
| `heuristics.py` | Heuristiques `h1`, `h2`, `h3` |
| `algos.py` | Dictionnaire des algorithmes disponibles (utilisé par `main.py` et l'interface) |
| `levels.py` | Les 5 niveaux de test |
| `interface.py` | Interface Pygame |

## Modélisation

**Symboles de la grille**

| Symbole | Signification |
|---|---|
| `R` | Joueur |
| `O` | Mur |
| ` ` | Case vide |
| `S` | Cible |
| `B` | Caisse |
| `.` | Joueur sur une cible |
| `*` | Caisse sur une cible |

- **État** : la grille complète (tuple de chaînes, donc hashable).
- **Actions** : `UP (-1,0)`, `DOWN (1,0)`, `LEFT (0,-1)`, `RIGHT (0,1)`.
- **Test de but** : plus aucune caisse `B` sur la grille (toutes sont sur des cibles).
- **Coût** : chaque pas coûte 1, donc le coût du chemin est le nombre de mouvements.

## Algorithmes

- **BFS** : suit le pseudo-code du cours (test du but à la génération, file FIFO). Les listes Open/Closed sont remplacées par une file et un ensemble d'états déjà vus.
- **A\*** : file de priorité sur `f = g + h`. Test du but à la sortie de Open. Un nœud déjà dans Open ou Closed est remplacé si on le retrouve avec un `f` plus petit.

## Heuristiques

| Heuristique | Définition | Admissible |
|---|---|---|
| `h1` | Nombre de caisses pas encore sur une cible | Oui |
| `h2` | `2 × nb_caisses_restantes + Σ (distance de Manhattan de chaque caisse à la cible la plus proche)` | Non (à cause du facteur 2) |
| `h3` | Somme des distances de Manhattan avec **l'affectation optimale** caisses → cibles, plus la distance du joueur à la caisse la plus proche (moins 1) | Oui |

Remarque : `h3` teste toutes les permutations des cibles, ce qui coûte O(n!) en nombre de caisses. C'est acceptable pour les niveaux fournis (3 caisses maximum).

## Détection de deadlock (ajout personnel)

Une caisse est dans un état perdu (deadlock) si elle ne pourra plus jamais atteindre une cible :

1. **Coin** : la caisse est dans un coin (un mur vertical et un mur horizontal adjacents) et n'est pas sur une cible.
2. **Caisse bloquée le long d'un mur** : la caisse est contre un mur, et sur toute la ligne le long de ce mur il n'y a aucune cible et aucune ouverture permettant de s'écarter du mur.

Les cases mortes sont calculées une seule fois par niveau (cache), puis `dead_lock()` vérifie si une caisse `B` s'y trouve. **A\*** ignore les successeurs en deadlock, ils n'entrent jamais dans Open. Le BFS reste "pur" (sans élagage), comme dans le pseudo-code du cours.

## Résultats

Nombre de nœuds développés (le coût est identique pour les 4 algorithmes) :

| Niveau | Coût | BFS | A\* h1 | A\* h2 | A\* h3 |
|---|---|---|---|---|---|
| 1 | 4 | 11 | 11 | 8 | 5 |
| 2 | 16 | 278 | 237 | 87 | 59 |
| 3 | 22 | 2581 | 1339 | 785 | 650 |
| 4 | 12 | 1247 | 329 | 107 | 130 |
| 5 | 27 | 97522 | 43739 | 6114 | 7728 |

`h2` développe parfois moins de nœuds que `h3` car son facteur 2 le rend plus "gourmand", mais il n'est pas admissible : il ne garantit pas l'optimalité en général. `h3` est admissible, donc A\* avec `h3` garantit une solution optimale.

## Interface Pygame

- **Menu** : choisir un niveau (flèches + Entrée, ou clic).
- **Simulation** : animation pas à pas de la solution, avec le coût, le nombre de nœuds développés et le temps de chaque algorithme.

| Touche | Action |
|---|---|
| `Espace` | Lecture / pause |
| `←` / `→` | Pas précédent / suivant |
| `R` | Recommencer |
| `Tab` ou `1`-`4` | Changer d'algorithme |
| `↑` / `↓` | Changer de niveau |
| `+` / `-` | Accélérer / ralentir |
| `Échap` | Retour au menu |