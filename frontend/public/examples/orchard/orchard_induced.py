import stormpy

# Load and build the full Prism Orchard model
prism_program = stormpy.parse_prism_program("orchard_stormvogel.pm")
constants = "NUM_FRUIT=4, DISTANCE_RAVEN=5"
prism_program = stormpy.preprocess_symbolic_input(prism_program, [], constants)[0].as_prism_program()
options = stormpy.BuilderOptions()
options.set_build_state_valuations()
options.set_build_choice_labels()
orchard_prism = stormpy.build_sparse_model_with_options(prism_program, options)

def model_check(model, prop):
    formula = stormpy.parse_properties(prop)[0]
    result = stormpy.model_checking(model, formula, only_initial_states=True)
    return result.at(model.initial_states[0])

# Extract the policy that maximises the probability of winning
formula = stormpy.parse_properties('Pmax=? [F "PlayersWon"]')[0]
result = stormpy.model_checking(orchard_prism, formula, extract_scheduler=True)

# Apply the scheduler to produce the induced Markov chain M^sigma
induced = orchard_prism.apply_scheduler(result.scheduler, True)

# Now ask a secondary question: how likely is it to pick all cherries?
# Under the winning policy (fixed) vs the cherry-optimal policy (free).
all_cherries = 'Pmax=? [F "AllCherriesPicked"]'
print(f"P(all cherries)  with fixed win policy: {model_check(induced,      all_cherries):.4f}")
print(f"P(all cherries) with optimal cherry policy: {model_check(orchard_prism, all_cherries):.4f}")
# The winning policy picks the fruit with the most pieces, which may not be cherries,
# so the cherry-optimal policy yields a higher probability.
