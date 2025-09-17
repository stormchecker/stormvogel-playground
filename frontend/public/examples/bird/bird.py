from stormvogel import *
from playground import show

def available_actions(s):
    if s == "init": # Either study or not
        return [["study"], ["don't study"]]
    else: # Otherwise, we have no choice (DTMC-like behavior)
        return [[]]

def delta(s, a):
    if "study" in a:
        return ["studied"]
    elif "don't study" in a:
        return [(1, "didn't study")]
    elif s == "studied":
        return [(9/10, "pass test"), (1/10, "fail test")]
    elif s == "didn't study":
        return [(2/5, "pass test"), (3/5, "fail test")]
    else:
        return [(1, "end")]

def labels(s):
    return s

# For rewards, you have to provide a dict. This enables multiple reward models if you use a non-singleton list.
def rewards(s: bird.State, a: bird.Action):
    if s == "pass test":
        return {"R":100}
    if s == "didn't study":
        return {"R":15}
    else:
        return {"R":0}

bird_study = bird.build_bird(
    delta=delta,
    init="init",
    available_actions=available_actions,
    labels=labels,
    modeltype=ModelType.MDP,
    rewards=rewards
)
vis = show(bird_study)
