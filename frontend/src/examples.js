export const examples = [
    {
        title: 'MDP',
        code: 'from stormvogel import *\nvis = show(examples.create_car_mdp(), do_init_server=False)\nprint(vis.generate_html())'
    },
    {
        title: 'PGC',
        code: `from stormvogel import pgc
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
vis = show(pgc_study, layout=Layout("layouts/pinkgreen.json"))`
    },
    {
        title: 'CTMC',
        code: `from stormvogel import *
# Create a new model with the name "Nuclear fusion"
ctmc = stormvogel.model.new_ctmc("Nuclear fusion")

# hydrogen fuses into helium
ctmc.get_state_by_id(0).set_transitions([(3, ctmc.new_state("helium"))])
# helium fuses into carbon
ctmc.get_state_by_id(1).set_transitions([(2, ctmc.new_state("carbon"))])
# carbon fuses into iron
ctmc.get_state_by_id(2).set_transitions([(7, ctmc.new_state("iron"))])
# supernova
ctmc.get_state_by_id(3).set_transitions([(12, ctmc.new_state("Supernova"))])

# we add the rates which are equal to whats in the transitions since the probabilities are all 1
rates = [3, 2, 7, 12, 0]
for i in range(5):
    ctmc.set_rate(ctmc.get_state_by_id(i), rates[i])

# we add self loops to all states with no outgoing transitions
ctmc.add_self_loops()
vis = show(ctmc, do_init_server = False)
print(vis.generate_html())`
    },
    {title: 'USING PRISM',
     code: `from stormvogel import *
import stormpy
prism_code = stormpy.parse_prism_program("Model.prism")
prism_die = mapping.from_prism(prism_code)
vis3 = show(prism_die,do_init_server=False)
print(vis3.generate_html())`
    },
{
    title: 'PRISM CODE',
    code: `dtmc

module die
    // The integers 0..7 represent our states, and 0 is the initial state.
    s : [0..7] init 0;
    // From s=0, we can go to 1,2,3,4,5,6 with 1/6th probability.
    // The + sign can be interpreted as an 'or'
    // Note that this is similar to our delta function.
    [] s=0 -> 1/6 : (s'=1) +
                1/6: (s'=2) +
                1/6: (s'=3) +
                1/6: (s'=4) +
                1/6: (s'=5) +
                1/6: (s'=6);
    // Self loops
    [] s>0 -> (s'=s);
endmodule

// Add the desired labels
label "rolled1" = s=1;
label "rolled2" = s=2;
label "rolled3" = s=3;
label "rolled4" = s=4;
label "rolled5" = s=5;
label "rolled6" = s=6;`
}];
