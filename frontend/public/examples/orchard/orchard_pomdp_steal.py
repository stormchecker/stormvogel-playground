import stormpy
import stormpy.pomdp

# Extended POMDP: before the game starts, a random player steals one fruit
# (uniformly at random from all four types). The players don't know which
# fruit was stolen, making partial observability actually matter.

def load_pomdp(filename):
    prism_program = stormpy.parse_prism_program(filename)
    formula_str = 'Pmax=? [!"RavenWon" U "PlayersWon"]'
    properties = stormpy.parse_properties_for_prism_program(formula_str, prism_program)
    prism_program, properties = stormpy.preprocess_symbolic_input(prism_program, properties, "")
    prism_program = prism_program.as_prism_program()
    options = stormpy.BuilderOptions([p.raw_formula for p in properties])
    options.set_build_state_valuations()
    options.set_build_choice_labels()
    pomdp = stormpy.build_model(prism_program, properties)
    pomdp = stormpy.pomdp.make_canonic(pomdp)
    return pomdp, properties

pomdp, properties = load_pomdp("orchard_pomdp_steal.pm")
print(pomdp)

# Fully observable upper bound: pretend the player knows exactly which fruit was stolen
mdp_result = stormpy.model_checking(pomdp, properties[0], force_fully_observable=True)
print(f"Win probability (fully observable): {mdp_result.at(pomdp.initial_states[0]):.4f}")

# Partially observable: player only sees whether each fruit type is non-empty
belexpl_options = stormpy.pomdp.BeliefExplorationModelCheckerOptionsDouble(True, True)
belexpl_options.use_clipping = False
belexpl_options.refine = True

belmc = stormpy.pomdp.BeliefExplorationModelCheckerDouble(pomdp, belexpl_options)
result = belmc.check(properties[0].raw_formula, [])
print(f"Win probability (POMDP, belief):    [{result.lower_bound:.4f}, {result.upper_bound:.4f}]")
# The gap between the two results shows the cost of partial observability.
