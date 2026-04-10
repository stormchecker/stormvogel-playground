import stormpy
from stormvogel import *
from enum import Enum
from copy import deepcopy

class Fruit(Enum):
    APPLE = "🍏"
    CHERRY = "🍒"
    PEAR = "🍐"
    PLUM = "🍇"

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
        if all(n == 0 for n in self.trees.values()): return GameState.PLAYERS_WON
        elif self.raven == 0: return GameState.RAVEN_WON
        return GameState.NOT_ENDED
    def pick_fruit(self, fruit):
        if self.trees[fruit] > 0: self.trees[fruit] -= 1
    def move_raven(self): self.raven -= 1
    def next_round(self): self.dice = None
    def __hash__(self): return hash((tuple(self.trees.items()), self.raven, self.dice))
    def __str__(self):
        return ", ".join(f"{n}{f.value}" for f, n in self.trees.items()) + f", raven={self.raven}"

def available_actions(state):
    if state.game_state() != GameState.NOT_ENDED: return ["gameEnded"]
    if state.dice is None: return ["nextRound"]
    kind, fruit = state.dice
    if kind == DiceOutcome.FRUIT: return [f"pick{fruit.name}"]
    if kind == DiceOutcome.BASKET: return [f"choose{f.name}" for f, n in state.trees.items() if n > 0]
    return ["moveRaven"]

def delta(state, action):
    if state.game_state() != GameState.NOT_ENDED: return [(1, state)]
    if state.dice is None:
        p = 1 / (len(state.trees) + 2)
        outcomes = []
        for fruit in state.trees:
            s = deepcopy(state); s.dice = (DiceOutcome.FRUIT, fruit); outcomes.append((p, s))
        s = deepcopy(state); s.dice = (DiceOutcome.BASKET, None); outcomes.append((p, s))
        s = deepcopy(state); s.dice = (DiceOutcome.RAVEN, None); outcomes.append((p, s))
        return outcomes
    kind, fruit = state.dice
    if kind == DiceOutcome.FRUIT:
        s = deepcopy(state); s.pick_fruit(fruit); s.next_round(); return [(1, s)]
    if kind == DiceOutcome.BASKET:
        s = deepcopy(state); s.pick_fruit(Fruit[action.removeprefix("choose")]); s.next_round(); return [(1, s)]
    s = deepcopy(state); s.move_raven(); s.next_round(); return [(1, s)]

def labels(state):
    gs = state.game_state()
    if gs == GameState.PLAYERS_WON: return ["PlayersWon"]
    if gs == GameState.RAVEN_WON: return ["RavenWon"]
    return []

# Full game: 4 fruits, 4 pieces each, raven 5 steps away => ~22k states
orchard = bird.build_bird(
    modeltype=ModelType.MDP,
    init=Orchard([Fruit.APPLE, Fruit.CHERRY, Fruit.PEAR, Fruit.PLUM], num_fruits=4, raven_distance=5),
    available_actions=available_actions,
    delta=delta,
    labels=labels,
    max_size=100000,
)

orchard_storm = mapping.stormvogel_to_stormpy(orchard)
formula = stormpy.parse_properties('Pmax=? [F "PlayersWon"]')

print(f"Before bisimulation: {orchard_storm.nr_states} states, {orchard_storm.nr_transitions} transitions")

# Strong bisimulation collapses behaviourally equivalent states
orchard_bisim = stormpy.perform_bisimulation(orchard_storm, formula, stormpy.BisimulationType.STRONG)

print(f"After bisimulation:  {orchard_bisim.nr_states} states, {orchard_bisim.nr_transitions} transitions")
print(f"Reduction: {100 * (1 - orchard_bisim.nr_states / orchard_storm.nr_states):.0f}% fewer states")
