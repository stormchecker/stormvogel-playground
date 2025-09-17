async function loadExample(category, title, files) {
    const loadedFiles = {};
    for (const [filename, filePath] of Object.entries(files)) {
        try {
            const response = await fetch(`./examples/${filePath}`);
            loadedFiles[filename] = await response.text();
        } catch (error) {
        }
    }
    return { title, category: category, files: loadedFiles };
}

// Create a manifest file that lists all examples
export const examples = await Promise.all([
    loadExample('stormvogel', 'MDP Construction', {
        "mdp.py": 'mdp/mdp.py'
    }),
    loadExample('stormvogel', 'Bird Builder', {
        "bird.py": 'bird/bird.py'
    }),
    loadExample('stormvogel', 'CTMC Construction', {
        "ctmc.py": 'ctmc/ctmc.py'
    }),
    loadExample('stormvogel', 'Import prism model', {
        "prism_example.py": 'prism/prism_example.py',
        "prism_example.prism": 'prism/prism_example.prism'
    }),
    // loadExample('stormpy: Getting Started', 'Getting Started Part 1', {
    //     "getting_started_part1.py": 'stormpy/getting_started_part1.py'
    // }),
    // loadExample('stormpy: Getting Started', 'Getting Started Part 2', {
    //     "getting_started_part2.py": 'stormpy/getting_started_part2.py'
    // }),
    // loadExample('stormpy: Getting Started', 'Getting Started Part 3', {
    //     "getting_started_part3.py": 'stormpy/getting_started_part3.py'
    // }),
    // loadExample('stormpy: Getting Started', 'Getting Started Part 4', {
    //     "getting_started_part4.py": 'stormpy/getting_started_part4.py'
    // }),
    // loadExample('stormpy: Analysis', 'Analysis Part 1', {
    //     "analysis_part1.py": 'stormpy/analysis_part1.py'
    // }),
    // loadExample('stormpy: Analysis', 'Analysis Part 2', {
    //     "analysis_part2.py": 'stormpy/analysis_part2.py'
    // }),
    // loadExample('stormpy: Analysis', 'Analysis Part 3', {
    //     "analysis_part3.py": 'stormpy/analysis_part3.py'
    // }),
    // loadExample('stormpy: Analysis', 'Analysis Part 4', {
    //     "analysis_part4.py": 'stormpy/analysis_part4.py'
    // }),
    // loadExample('stormpy: Building Models', 'Building CTMCs', {
    //     "building_ctmcs_model.py": 'stormpy/building_ctmcs_model.py'
    // }),
    // loadExample('stormpy: Building Models', 'Building MAS', {
    //     "building_mas_model.py": 'stormpy/building_mas_model.py'
    // }),
    // loadExample('stormpy: Building Models', 'Building MDPs', {
    //     "building_mdps_model.py": 'stormpy/building_mdps_model.py'
    // }),
    // loadExample('stormpy: Building Models', 'Building Models Part 1', {
    //     "building_models_part1.py": 'stormpy/building_models_part1.py'
    // }),
    // loadExample('stormpy: Building Models', 'Building Models Part 2', {
    //     "building_models_part2.py": 'stormpy/building_models_part2.py'
    // }),
    // loadExample('stormpy: Building Models', 'Building Models Part 3', {
    //     "building_models_part3.py": 'stormpy/building_models_part3.py'
    // }),
    // loadExample('stormpy: Building Models', 'Building Models Part 4', {
    //     "building_models_part4.py": 'stormpy/building_models_part4.py'
    // }),
    // loadExample('stormpy: DFTs', 'DFTs Interactive Simulator', {
    //     "dfts_interactive_simulator.py": 'stormpy/dfts_interactive_simulator.py'
    // }),
    // loadExample('stormpy: DFTs', 'DFTs Part 1', {
    //     "dfts_part1.py": 'stormpy/dfts_part1.py'
    // }),
    // loadExample('stormpy: DFTs', 'DFTs Part 2', {
    //     "dfts_part2.py": 'stormpy/dfts_part2.py'
    // }),
    // loadExample('stormpy: Exploration', 'Exploration Part 1', {
    //     "exploration_part1.py": 'stormpy/exploration_part1.py'
    // }),
    // loadExample('stormpy: Exploration', 'Exploration Part 2', {
    //     "exploration_part2.py": 'stormpy/exploration_part2.py'
    // }),
    // loadExample('stormpy: Exploration', 'Exploration Part 3', {
    //     "exploration_part3.py": 'stormpy/exploration_part3.py'
    // }),
    // loadExample('stormpy: GSPNs', 'GSPNs Part 1', {
    //     "gspns_part1.py": 'stormpy/gspns_part1.py'
    // }),
    // loadExample('stormpy: GSPNs', 'GSPNs Part 2', {
    //     "gspns_part2.py": 'stormpy/gspns_part2.py'
    // }),
    // loadExample('stormpy: High Level Models', 'High Level Models Part 1', {
    //     "highlevel_models_part1.py": 'stormpy/highlevel_models_part1.py'
    // }),
    // loadExample('stormpy: High Level Models', 'High Level Models Part 2', {
    //     "highlevel_models_part2.py": 'stormpy/highlevel_models_part2.py'
    // }),
    // loadExample('stormpy: Parametric Models', 'Parametric Models Part 1', {
    //     "parametric_models_part1.py": 'stormpy/parametric_models_part1.py'
    // }),
    // loadExample('stormpy: Parametric Models', 'Parametric Models Part 2', {
    // "parametric_models_part2.py": 'stormpy/parametric_models_part2.py'
    // }),
    // loadExample('stormpy: Parametric Models', 'Parametric Models Part 3', {
    //     "parametric_models_part3.py": 'stormpy/parametric_models_part3.py'
    // }),
    // loadExample('stormpy: Parametric Models', 'Parametric Models Part 4', {
    //     "parametric_models_part4.py": 'stormpy/parametric_models_part4.py'
    // }),
    // loadExample('stormpy: POMDPs', 'POMDP High Level Observations', {
    //     "pomdp_high_level_observations.py": 'stormpy/pomdp_high_level_observations.py'
    // }),
    // loadExample('stormpy: POMDPs', 'POMDP Part 1', {
    //     "pomdp_part1.py": 'stormpy/pomdp_part1.py'
    // }),
    // loadExample('stormpy: PyCarl', 'PyCarl Getting Started', {
    //     "pycarl_getting_started.py": 'stormpy/pycarl_getting_started.py'
    // }),
    // loadExample('stormpy: Reward Models', 'Reward Models Part 1', {
    //     "reward_models_part1.py": 'stormpy/reward_models_part1.py'
    // }),
    // loadExample('stormpy: Schedulers', 'Schedulers Part 1', {
    //     "schedulers_part1.py": 'stormpy/schedulers_part1.py'
    // }),
    // loadExample('stormpy: Schedulers', 'Schedulers Part 2', {
    //     "schedulers_part2.py": 'stormpy/schedulers_part2.py'
    // }),
    // loadExample('stormpy: Shortest Paths', 'Shortest Paths Part 1', {
    //     "shortest_paths_part1.py": 'stormpy/shortest_paths_part1.py'
    // }),
    // loadExample('stormpy: Simulation', 'Simulator Part 1', {
    //     "simulator_part1.py": 'stormpy/simulator_part1.py'
    // }),
    // loadExample('stormpy: Simulation', 'Simulator Part 2', {
    //     "simulator_part2.py": 'stormpy/simulator_part2.py'
    // }),
    // loadExample('stormpy: Simulation', 'Simulator Part 3', {
    //     "simulator_part3.py": 'stormpy/simulator_part3.py'
    // }),
    // loadExample('stormpy: Simulation', 'Simulator Part 4', {
    //     "simulator_part4.py": 'stormpy/simulator_part4.py'
    // })
]);
