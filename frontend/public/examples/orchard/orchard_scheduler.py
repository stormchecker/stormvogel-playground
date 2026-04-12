import stormpy

# Load the Prism Orchard model and instantiate with full game parameters
prism_program = stormpy.parse_prism_program("orchard_stormvogel.pm")
constants = "NUM_FRUIT=4, DISTANCE_RAVEN=5"
prism_program = stormpy.preprocess_symbolic_input(prism_program, [], constants)[0].as_prism_program()
options = stormpy.BuilderOptions()
options.set_build_state_valuations()
options.set_build_choice_labels()
orchard_prism = stormpy.build_sparse_model_with_options(prism_program, options)

formula = stormpy.parse_properties('Pmax=? [F "PlayersWon"]')[0]

# Extract the optimal policy as a by-product of model checking
result = stormpy.model_checking(orchard_prism, formula, extract_scheduler=True)
print(f"Win probability: {result.at(orchard_prism.initial_states[0]):.4f}")

# Print the optimal action for the interesting nondeterministic states:
# "choose" states arise when the basket is rolled and the player picks any fruit.
# The optimal policy always picks the fruit type with the most remaining pieces.
print("\nOptimal basket choices (first 20):")
i = 0
for state in orchard_prism.states:
    choice = result.scheduler.get_choice(state)
    action_index = choice.get_deterministic_choice()
    action = state.actions[action_index]
    action_name = next(iter(action.labels))
    if action_name.startswith("choose"):
        print(f"  {state.valuations}  =>  {action_name}")
        i += 1
        if i >= 20:
            print("   ...(truncated)...")
            break
