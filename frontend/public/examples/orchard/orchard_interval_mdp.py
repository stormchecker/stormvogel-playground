import stormpy
from stormvogel import *
from playground import show
from enum import Enum
from copy import deepcopy

# Interval MDP: dice probabilities are uncertain intervals instead of exact values.
# Each face probability is 1/4 ± 1/36, capturing imprecision in the dice.

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
        # Replace point probability with an interval [p - 1/36, p + 1/36]
        p_interval = model.Interval(p - 1/36, p + 1/36)
        outcomes = []
        for fruit in state.trees:
            s = deepcopy(state); s.dice = (DiceOutcome.FRUIT, fruit); outcomes.append((p_interval, s))
        s = deepcopy(state); s.dice = (DiceOutcome.BASKET, None); outcomes.append((p_interval, s))
        s = deepcopy(state); s.dice = (DiceOutcome.RAVEN, None); outcomes.append((p_interval, s))
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

orchard = bird.build_bird(
    modeltype=ModelType.MDP,
    init=Orchard([Fruit.APPLE, Fruit.CHERRY], num_fruits=2, raven_distance=2),
    available_actions=available_actions,
    delta=delta,
    labels=labels,
)

orchard_storm = mapping.stormvogel_to_stormpy(orchard)
print(orchard_storm)

properties = stormpy.parse_properties('Pmax=? [F "PlayersWon"]')
task = stormpy.CheckTask(properties[0].raw_formula)

env = stormpy.Environment()
env.solver_environment.minmax_solver_environment.method = stormpy.MinMaxMethod.value_iteration

# Cooperative: uncertainty resolved in favour of the policy
task.set_uncertainty_resolution_mode(stormpy.UncertaintyResolutionMode.COOPERATIVE)
result = stormpy.check_interval_mdp(orchard_storm, task, env)
print(f"Cooperative (best case): {result.at(orchard_storm.initial_states[0]):.4f}")

# Robust: uncertainty resolved against the policy
task.set_uncertainty_resolution_mode(stormpy.UncertaintyResolutionMode.ROBUST)
result = stormpy.check_interval_mdp(orchard_storm, task, env)
print(f"Robust (worst case):     {result.at(orchard_storm.initial_states[0]):.4f}")
