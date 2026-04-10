from stormvogel import *
from enum import Enum
from copy import deepcopy

# The Orchard game: collect all fruit before the raven arrives.
# Each round, a player throws a 4+2-sided dice:
#   fruit outcome -> pick that fruit from the tree
#   basket outcome -> freely pick any fruit
#   raven outcome -> raven moves one step closer

class Fruit(Enum):
    APPLE = "🍏"
    CHERRY = "🍒"

class DiceOutcome(Enum):
    FRUIT = "fruit"
    BASKET = "🧺"
    RAVEN = "🐦"

class GameState(Enum):
    NOT_ENDED = 0
    PLAYERS_WON = 1
    RAVEN_WON = 2

class Orchard(bird.State):
    def __init__(self, fruit_types, num_fruits, raven_distance):
        self.trees = {f: num_fruits for f in fruit_types}
        self.raven = raven_distance
        self.dice = None

    def game_state(self):
        if all(n == 0 for n in self.trees.values()):
            return GameState.PLAYERS_WON
        elif self.raven == 0:
            return GameState.RAVEN_WON
        return GameState.NOT_ENDED

    def pick_fruit(self, fruit):
        if self.trees[fruit] > 0:
            self.trees[fruit] -= 1

    def move_raven(self):
        self.raven -= 1

    def next_round(self):
        self.dice = None

    def __hash__(self):
        return hash((tuple(self.trees.items()), self.raven, self.dice))

    def __str__(self):
        parts = [f"{n}{f.value}" for f, n in self.trees.items()]
        return ", ".join(parts) + f", raven={self.raven}"

def available_actions(state):
    if state.game_state() != GameState.NOT_ENDED:
        return ["gameEnded"]
    if state.dice is None:
        return ["nextRound"]
    kind, fruit = state.dice
    if kind == DiceOutcome.FRUIT:
        return [f"pick{fruit.name}"]
    if kind == DiceOutcome.BASKET:
        return [f"choose{f.name}" for f, n in state.trees.items() if n > 0]
    return ["moveRaven"]

def delta(state, action):
    if state.game_state() != GameState.NOT_ENDED:
        return [(1, state)]
    if state.dice is None:
        # Uniform dice over all fruit types + basket + raven
        p = 1 / (len(state.trees) + 2)
        outcomes = []
        for fruit in state.trees:
            s = deepcopy(state)
            s.dice = (DiceOutcome.FRUIT, fruit)
            outcomes.append((p, s))
        s = deepcopy(state)
        s.dice = (DiceOutcome.BASKET, None)
        outcomes.append((p, s))
        s = deepcopy(state)
        s.dice = (DiceOutcome.RAVEN, None)
        outcomes.append((p, s))
        return outcomes
    kind, fruit = state.dice
    if kind == DiceOutcome.FRUIT:
        s = deepcopy(state); s.pick_fruit(fruit); s.next_round(); return [(1, s)]
    if kind == DiceOutcome.BASKET:
        s = deepcopy(state); s.pick_fruit(Fruit[action.removeprefix("choose")]); s.next_round(); return [(1, s)]
    s = deepcopy(state); s.move_raven(); s.next_round(); return [(1, s)]

def labels(state):
    gs = state.game_state()
    l = [str(state)]
    if gs == GameState.PLAYERS_WON:
        l.append("PlayersWon")
    elif gs == GameState.RAVEN_WON:
        l.append("RavenWon")
    return l

def rewards(state):
    if state.game_state() == GameState.NOT_ENDED and state.dice is None:
        return {"rounds": 1}
    return {"rounds": 0}

orchard = bird.build_bird(
    modeltype=ModelType.MDP,
    init=Orchard([Fruit.APPLE, Fruit.CHERRY], num_fruits=2, raven_distance=2),
    available_actions=available_actions,
    delta=delta,
    labels=labels,
    rewards=rewards,
)

show(orchard)
