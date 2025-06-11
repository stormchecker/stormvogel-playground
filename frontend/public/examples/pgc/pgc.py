from stormvogel import pgc
from stormvogel.model import EmptyAction, ModelType
from stormvogel.show import show
from stormvogel.layout import Layout

init = pgc.State(x="")

def available_actions(s: pgc.State):
    if s == init: # If we are in the initial state, we have a choice.
        return [pgc.Action(["study"]), pgc.Action(["don't study"])]
    else: # Otherwise, we don't have any choice, we are just a Markov chain.
        return [pgc.Action([])]

def delta(s: pgc.State, a: pgc.Action):
    if "study" in a.labels:
        return [(1, pgc.State(x=["studied"]))]
    elif "don't study" in a.labels:
        return [(1, pgc.State(x=["didn't study"]))]
    elif "studied" in s.x:
        return [(9/10, pgc.State(x=["pass test"])), (1/10, pgc.State(x=["fail test"]))]
    elif "didn't study" in s.x:
        return [(2/5, pgc.State(x=["pass test"])), (3/5, pgc.State(x=["fail test"]))]
    else:
        return [(1, pgc.State(x=["end"]))]

labels = lambda s: s.x

# For rewards, you have to provide a list. This enables multiple reward models if you use a non-singleton list.
def rewards(s: pgc.State, a: pgc.Action):
    if "pass test" in s.x:
        return {"r1":100}
    if "didn't study" in s.x:
        return {"r1":15}
    else:
        return {"r1":0}


pgc_study = pgc.build_pgc(
    delta=delta,
    initial_state_pgc=init,
    available_actions=available_actions,
    labels=labels,
    modeltype=ModelType.MDP,
    rewards=rewards
)
vis = show(pgc_study, do_init_server= False)
print(vis.generate_html())

