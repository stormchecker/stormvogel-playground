import stormpy
import paynt

# Load and build the full Prism Orchard model with state valuations
prism_program = stormpy.parse_prism_program("orchard_stormvogel.pm")
constants = "NUM_FRUIT=4, DISTANCE_RAVEN=5"
prism_program = stormpy.preprocess_symbolic_input(prism_program, [], constants)[0].as_prism_program()
options = stormpy.BuilderOptions()
options.set_build_state_valuations()
options.set_build_choice_labels()
orchard_prism = stormpy.build_sparse_model_with_options(prism_program, options)

formula = stormpy.parse_properties('Pmax=? [F "PlayersWon"]')[0]

# The raw fruit-count variables alone don't yield a compact decision tree.
# We add Boolean helper variables "most_X" = fruit X has the most pieces left.
# PAYNT can then find a depth-3 tree using only these predicates.
def declare_extra_variables(manager):
    def get_or_create_bool(name):
        if not manager.has_variable(name):
            return manager.create_boolean_variable(name)
        return manager.get_variable(name)

    apple  = manager.get_variable("apple").get_expression()
    pear   = manager.get_variable("pear").get_expression()
    cherry = manager.get_variable("cherry").get_expression()
    plum   = manager.get_variable("plum").get_expression()

    defs = []
    for fruit_name, fruit_expr, others in [
        ("most_apples",   apple,  [pear, cherry, plum]),
        ("most_pears",    pear,   [apple, cherry, plum]),
        ("most_cherries", cherry, [apple, pear, plum]),
        ("most_plums",    plum,   [apple, pear, cherry]),
    ]:
        var = get_or_create_bool(fruit_name)
        cond = stormpy.Expression.Conjunction(
            [stormpy.Expression.Geq(fruit_expr, o) for o in others]
        )
        defs.append((var, cond))
    return defs

svt = stormpy.StateValuationTransformer(orchard_prism.state_valuations)
for var, defn in declare_extra_variables(prism_program.expression_manager):
    svt.add_boolean_expression(var, defn)
mdp_with_extras = stormpy.set_state_valuations(orchard_prism, svt.build(False))

# Synthesise a decision tree of depth <= 3 that achieves the optimal win probability
mc_result = stormpy.model_checking(mdp_with_extras, formula)
print(f"Optimal win probability: {mc_result.at(mdp_with_extras.initial_states[0]):.4f}")

colored_mdp_factory = paynt.dt.DtColoredMdpFactory(mdp_with_extras)
task = paynt.dt.DtTask([formula], 3)
result = paynt.dt.synthesize(colored_mdp_factory, task)

print(f"Synthesis success: {result.success}")
if result.success:
    print(f"Decision tree value: {result.value:.4f}")
    print("Decision tree:\n", result.tree.to_string())

    import io
    import matplotlib.pyplot as plt
    import matplotlib.image as mpimg
    from playground import show

    # Render decision tree via graphviz, embed in a matplotlib figure, display via playground
    png_bytes = result.tree.to_graphviz().pipe(format='png')
    img = mpimg.imread(io.BytesIO(png_bytes))
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.imshow(img)
    ax.axis('off')
    fig.tight_layout()
    show(fig)
