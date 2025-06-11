// Helper function to load example files
async function loadExample(title, files) {
    const loadedFiles = {};
    for (const [filename, path] of Object.entries(files)) {
        loadedFiles[filename] = (await import(`./examples/${path}?raw`)).default;
    }
    return { title, files: loadedFiles };
}

export const examples = await Promise.all([
    loadExample('MDP', {
        "mdp.py": 'mdp/mdp.py'
    }),
    loadExample('PGC', {
        "pgc.py": 'pgc/pgc.py'
    }),
    loadExample('CTMC', {
        "ctmc.py": 'ctmc/ctmc.py'
    }),
    loadExample('Import prism model', {
        "prism_example.py": 'prism/prism_example.py',
        "prism_example.prism": 'prism/prism_example.prism'
    })
]);
