async function loadExample(title, files) {
    const loadedFiles = {};
    for (const [filename, filePath] of Object.entries(files)) {
        const response = await fetch(`/examples/${filePath}`);
        loadedFiles[filename] = await response.text();
    }
    return { title, files: loadedFiles };
}

// Create a manifest file that lists all examples
export const examples = await Promise.all([
    loadExample('MDP Construction', {
        "mdp.py": 'mdp/mdp.py'
    }),
    loadExample('PGC Builder', {
        "pgc.py": 'pgc/pgc.py'
    }),
    loadExample('CTMC Construction', {
        "ctmc.py": 'ctmc/ctmc.py'
    }),
    loadExample('Import prism model', {
        "prism_example.py": 'prism/prism_example.py',
        "prism_example.prism": 'prism/prism_example.prism'
    })
]);
