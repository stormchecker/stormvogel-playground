<script>
  import { onMount, onDestroy } from 'svelte';
  import { EditorView, basicSetup } from "codemirror";  // Imports the editor
  import { keymap } from "@codemirror/view";
  import { indentWithTab } from "@codemirror/commands"; // Imports tab handling
  import { python } from "@codemirror/lang-python";     // Imports Python syntax highlighting
  import { linter, lintGutter } from "@codemirror/lint"; // Imports linting support
  
  let code = "";
  let specification = 'Calculate probability from start to end';
  let output = "";
  let debug_info = "";
  let error = "";
  let simulationSteps = [];
  let editor;
  let lintErrors = [];

  // Save code to local storage

    function htmlDecode(input) {
      const parser = new DOMParser();
      const doc = parser.parseFromString(input, "text/html");
      return doc.documentElement.textContent;
    }

    function saveCode() {
        const code = editor.state.doc.toString(); // Get the code from the editor
        localStorage.setItem("python_code",code); // Save for a number of days
        alert("Code saved!"); //TODO :change this to a nice saved button change or display it in another way
    }

    // Adds code editor with syntax highlighting
    function createEditor() {
        editor = new EditorView({
            doc: code,
            // Sets up the editor with Python syntax highlighting, tab handling and linting
            extensions: [basicSetup, keymap.of([indentWithTab]), python(), lintGutter(), linter(lintCode)],
            parent: document.querySelector(".code-editor"),
        });
    }

    onMount(() => {
        // Start the backend server
        startupBackend();
        // Load code from local storage
        window.addEventListener("beforeunload", saveCode);
        const savedCode = localStorage.getItem("python_code");
        if (savedCode) {
            code = savedCode;
        }
        
        // Load the editor
        createEditor();
    });

    onDestroy(() => {
        window.removeEventListener("beforeunload", saveCode);
    });

  async function startupBackend() {
    try {
        const response = await fetch('http://localhost:5000/startup', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({}), 
            credentials: 'include'
        });

        const result = await response.json();
        if (result.status === 'success') {
            console.log(result.message); 
        } else {
            console.error('Error:', result.message);
        }
    } catch (e) {
        console.error('Failed to startup server backend:', e);
    }
  }  

  async function lintCode(view) {
    const code = view.state.doc.toString();
    try {
      const response = await fetch('http://localhost:5000/lint', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ code }),
        credentials: 'include'
      });

      const result = await response.json();
      if(result.lint){
        console.log("There are no errors: ", result.lint);
        lintErrors = parseLintErrors(result.lint);
      }else{
        console.log("error", result.error);
        lintErrors = parseLintErrors(result.error);
      }
    } catch (e) {
      lintErrors = [{ from: 0, to: 0, severity: "error", message: "Failed to connect to linting server" }];
    }
    return lintErrors;
  }

  function parseLintErrors(lintOutput) {
    const errors = [];
    const lines = lintOutput.split('\n');
    const regex = /:(\d+):(\d+):\s(\w+)\s(.+)/;

    for (const line of lines) {
      const match = line.match(regex);
      if (match) {
        const [, lineNum, colNum, errorCode, message] = match;
        const lineNumInt = parseInt(lineNum);
        const colNumInt = parseInt(colNum);
        console.log(`Line: ${lineNumInt}, Column: ${colNumInt}, Error Code: ${errorCode}, Message: ${message}`);
        const line = editor.state.doc.line(lineNumInt); // Get the line at lineNum
        const from = line.from + colNumInt - 1; // Adjust the starting position by subtracting 1 for zero-indexing
        const to = from + 1; // TODO: Adjust the ending position based on the length of the error

        errors.push({
          from,
          to,
          severity: mapSeverity(errorCode),
          message
        });
      }
    }
    return errors;
  }

  function mapSeverity(errorCode) {
    // TODO: Map ruff error codes to codemirror severity levels (error, warning, info)
    // See: https://docs.astral.sh/ruff/rules/
    return "error";  
  }

  async function executeCode() {
    const code = editor.state.doc.toString();
    try {
      const response = await fetch('http://localhost:5000/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ code }), 
        credentials: 'include'
      });
      
      const result = await response.json();
      output = result.output;
      debug_info = result.logs;
      error = result.error;
    } catch (e) {
      error = "Failed to connect to execution server";
    }
  }

  function checkSpecification() {
    // Placeholder for actual specification checking
    output = "Specification analysis would go here";
  }

  function simulate() {
    // Mock simulation
    simulationSteps = ['start', 'active', 'end'];
    output = `Simulation path: ${simulationSteps.join(' → ')}`;
  }
</script>

<svelte:head>
  <title>Model Playground</title>
</svelte:head>

<div class="container">
  <header>
    <h1>Model Playground</h1>
    <nav>
      <button class="nav-btn">Examples</button>
      <button class="nav-btn" on:click={saveCode}>Save</button>
    </nav>
  </header>

  <div class="main-content">
    <div class="code-panel">
      <div class="editor-header">
        <span class="file-tab active">model.py</span>
        <button on:click={executeCode} class="nav-btn">Execute</button>
      </div>
      <div class="code-editor"
        placeholder="Enter your Python code here..."
      ></div>
    </div>

    <div class="visualization-panel">
      <div class="model-preview">
        {@html output}
      </div>
      <div class="output-console">
        <pre>{debug_info}</pre>
        <pre style="color: orange;">{lintErrors.map(e => `${e.message} (line ${editor.state.doc.lineAt(e.from).number}, col ${e.from - editor.state.doc.lineAt(e.from).from + 1})`).join('\n')}</pre>
        <pre style="color: red;">{error}</pre>
      </div>
    </div>
  </div>

  <div class="specification-bar">
    <input 
      type="text" 
      bind:value={specification} 
      placeholder="Enter your query"
      class="spec-input"
    />
    <div class="controls">
      <button on:click={checkSpecification} class="action-btn">Analyze</button>
      <button on:click={simulate} class="action-btn">Simulate</button>
    </div>
  </div>
</div>

<style>
  :global(body) {
    margin: 0;
    padding: 0;
    background-color: #ffffff;
    color: #333333;
    font-family: 'Arial', sans-serif;
    height: 100vh;
    overflow: hidden;
  }

  .container {
    display: flex;
    flex-direction: column;
    height: 100vh;
  }

  header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 2rem;
    background-color: #f7f7f7;
    border-bottom: 1px solid #ddd;
  }

  h1 {
    margin: 0;
    font-size: 1.5rem;
  }

  nav {
    display: flex;
  }

  .nav-btn {
    background: #e6f0ff;
    color: #007acc;
    border: 1px solid #b3d1ff;
    padding: 8px 16px;
    margin-left: 1rem;
    cursor: pointer;
    border-radius: 4px;
    transition: background 0.3s;
  }

  .nav-btn:hover {
    background: #d0e0ff;
  }

  .main-content {
    display: grid;
    grid-template-columns: 1fr 1fr;
    flex-grow: 1;
    gap: 1rem;
    padding: 1rem;
    background-color: #fafafa;
    overflow: hidden;
  }

  .code-panel {
    background: #f5f5f5;
    border-radius: 4px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    display: flex;
    flex-direction: column;
  }

  .editor-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #eaeaea;
    padding: 8px 16px;
    border-bottom: 1px solid #ddd;
  }

  .file-tab {
    padding: 6px 12px;
    background: #fff;
    border-radius: 4px 4px 0 0;
    border: 1px solid #ddd;
  }

  .file-tab.active {
    border-bottom: 2px solid #007acc;
    font-weight: bold;
  }

  .code-editor {
    flex-grow: 1;
    overflow: auto;
    background-color: #fff;
    color: #333;
    font-family: 'Courier New', monospace;
    border: none;
    resize: none;
    white-space: pre;
    tab-size: 4;
    text-align: left;
  }

  .visualization-panel {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    overflow: hidden;
  }

  .model-preview {
    flex: 2;
    background: #f5f5f5;
    border-radius: 4px;
    padding: 1rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    overflow: hidden;
  }

  .state-diagram {
    position: relative;
    height: 100%;
  }

  .state {
    position: absolute;
    padding: 1rem;
    background: #007acc;
    border-radius: 8px;
    text-align: center;
    color: #fff;
  }

  .start { top: 20%; left: 10%; }
  .active { top: 50%; left: 40%; }
  .end { top: 20%; left: 70%; }

  .transition {
    position: absolute;
    color: #00cc88;
    font-size: 0.8em;
  }

  .start-active { top: 30%; left: 25%; }
  .start-end { top: 25%; left: 45%; }
  .active-end { top: 60%; left: 55%; }

  .output-console {
    flex: 1;
    background: #fff;
    padding: 1rem;
    border-radius: 4px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    overflow: auto;
    font-family: 'Courier New', monospace;
  }

  .specification-bar {
    display: flex;
    gap: 1rem;
    padding: 1rem;
    background: #f7f7f7;
    border-top: 1px solid #ddd;
  }

  .spec-input {
    flex-grow: 1;
    padding: 8px;
    background: #fff;
    border: 1px solid #ccc;
    color: #333;
    border-radius: 4px;
  }

  .action-btn {
    background: #007acc;
    color: #fff;
    border: none;
    padding: 8px 16px;
    cursor: pointer;
    border-radius: 4px;
    transition: background 0.3s;
  }

  .action-btn:hover {
    background: #005fa3;
  }
</style>
