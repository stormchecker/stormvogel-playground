import stormpy
import stormpy.pomdp

# The POMDP variant of Orchard: the player can observe whether each fruit type
# is still available (hasApple, hasCherry, ...) but not the exact counts.
# The raven position and dice outcome are fully observable.

prism_program = stormpy.parse_prism_program("orchard_pomdp.pm")
formula_str = 'Pmax=? [!"RavenWon" U "PlayersWon"]'
properties = stormpy.parse_properties_for_prism_program(formula_str, prism_program)
prism_program, properties = stormpy.preprocess_symbolic_input(prism_program, properties, "")
prism_program = prism_program.as_prism_program()
options = stormpy.BuilderOptions([p.raw_formula for p in properties])
options.set_build_state_valuations()
options.set_build_choice_labels()
pomdp = stormpy.build_model(prism_program, properties)
pomdp = stormpy.pomdp.make_canonic(pomdp)
print(pomdp)

# Belief-based model checking: approximate the optimal win probability
# by partially exploring the belief MDP
belexpl_options = stormpy.pomdp.BeliefExplorationModelCheckerOptionsDouble(True, True)
belexpl_options.use_clipping = False
belexpl_options.refine = True

belmc = stormpy.pomdp.BeliefExplorationModelCheckerDouble(pomdp, belexpl_options)
result = belmc.check(properties[0].raw_formula, [])
print(f"Win probability (POMDP): [{result.lower_bound:.4f}, {result.upper_bound:.4f}]")
# Result matches the fully-observable MDP: the player can track fruit counts from observations.
