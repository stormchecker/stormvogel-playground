<script>
  import { onMount, onDestroy } from 'svelte';
  import { EditorView, basicSetup } from "codemirror";  // Imports the editor
  import { keymap } from "@codemirror/view";
  import { indentWithTab } from "@codemirror/commands"; // Imports tab handling
  import { python } from "@codemirror/lang-python";     // Imports Python syntax highlighting
  import { linter, lintGutter } from "@codemirror/lint"; // Imports linting support
  import { fade } from 'svelte/transition'; // Imports smooth transition for a pop-up message
  
  let code = "";
  let specification = 'Calculate probability from start to end';
  let output_html = "";
  let output_non_html = "";
  let error = "";
  let simulationSteps = [];
  let editor;
  let lintErrors = [];
  let isExecuting = false;
  let saveStatus = 'idle'; // Variable for checking the save status
  let saveToast = false; // Show a pop-up ('toast') whent the code is saved successfully 

  // Save code to local storage
    function saveCode() {
        const code = editor.state.doc.toString(); // Get the code from the editor

        try { // Try to save the code
          localStorage.setItem("python_code",code); // Save for a number of days
          saveStatus = 'saved';
          saveToast = true;
          setTimeout(() => { // After 2 seconds set saveStatus back to default
            saveStatus = 'idle'
          }, 2000);
          setTimeout(() => { // After 3 seconds set saveToast to false so it fades away
            saveToast = false
          }, 3000);
        } catch (error) { // If there are errors while saving, output it to the console
          console.error("Failed to save code: ", error);
          alert("Error, unable to save code.");
      }
    }

    function exportCode() {
      const code = editor.state.doc.toString(); // Get the code from the editor
      
      const blob = new Blob([code], { type: "text/plain "}); // Create a Blob object with the code
      const a = document.createElement("a"); // Create a link element
      a.href = URL.createObjectURL(blob); // Set the URL pointing to Blob
      a.download = "stormvogel_playground.py" // Set the default filename

      document.body.appendChild(a); // Add the link element to the DOM
      a.click() // 'Click' the download link
      document.body.removeChild(a); // After the download has been initiated remove the link element
    }

    // Adds code editor with syntax highlighting
    function createEditor() {
        editor = new EditorView({
            doc: code,
            // Sets up the editor with Python syntax highlighting, tab handling and linting
            extensions: [basicSetup, keymap.of([indentWithTab]), python(), lintGutter(),linter(lintCode)],
            parent: document.querySelector(".code-editor"),
        });
    }

    onMount(() => {
        // Load code from local storage
        window.addEventListener("beforeunload", function () {
            saveCode();
            stopExecution();
        });
        const savedCode = localStorage.getItem("python_code");
        if (savedCode) {
            code = savedCode;
        }
        
        // Load the editor
        createEditor();
        startupBackend(); 
    });

    onDestroy(() => {
        window.removeEventListener("beforeunload", function () {
            saveCode();
            stopExecution();
        });
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

  async function executeCode() {
    isExecuting = true;
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

        console.log("Status of execution response: ", result.status);
        if (result.status === "success") {
            output_html = result.output_html;
            output_non_html = result.output_non_html;
            error = "";
        } else {
            error = result.message || "An unknown error occurred";
        }
        
      //output_html = result.output_html;
      //output_non_html = result.output_non_html;
      //error = result.message;
    } catch (e) {
      output_html = "";
      output_non_html = "";
      error = "Failed to connect to execution server";
    } finally {
      isExecuting = false;
    }
  }

  async function stopExecution() {
      try {
          const response = await fetch('http://localhost:5000/stop', {
              method: 'POST',
              headers: {
                  'Content-Type': 'application/json'
              },
              credentials: 'include'
          });

          const result = await response.json();
          return result.message; // Assuming the server returns a message
      } catch (e) {
          return "Failed to connect to execution server";
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
        console.log("Error:", result.error);
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
    // Parses the output of the linter example: 
    // /script.py:16:1: E402 Module level import not at top of file
    const regex = /:(\d+):(\d+):\s(\w+)\s(.+)/;

    // Parses the output of the linter for syntax errors, example:
    // script.py:19:44: SyntaxError: Simple statements must be separated by newlines or semicolons
    const syntaxErrorRegex = /:(\d+):(\d+):\s(SyntaxError):\s(.+)/;

    for (const line of lines) {
      let match = line.match(regex);
      if (!match) {
        match = line.match(syntaxErrorRegex);
      }
      if (match) {
        const [, lineNum, colNum, errorCode, message] = match;
        const lineNumInt = parseInt(lineNum);
        const colNumInt = parseInt(colNum);
        console.log(`Line: ${lineNumInt}, Column: ${colNumInt}, Error Code: ${errorCode}, Message: ${message}`);
        const editorLine = editor.state.doc.line(lineNumInt); // Get the line at lineNum
        const from = editorLine.from + colNumInt - 1; // Adjust the starting position by subtracting 1 for zero-indexing
        const to = editorLine.to; // Mark till the end of the line

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
    if (errorCode.startsWith('E') || errorCode.startsWith('SyntaxError')) {
      return "error";
    } else if (errorCode.startsWith('W')) {
      return "warning";
    } else {
      return "info";
    }
  }

  function checkSpecification() {
    // Placeholder for actual specification checking
    // output = "Specification analysis would go here";
  }

  function simulate() {
    // Mock simulation
    simulationSteps = ['start', 'active', 'end'];
    // output = `Simulation path: ${simulationSteps.join(' → ')}`;
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
      <button on:click={saveCode}
        style={saveStatus === 'saved' ? "background: green; color: white;" : ""}
        class="nav-btn">
        {saveStatus === 'saved' ? 'Saved' : 'Save'}
      </button>
      <button on:click={exportCode}
        class="nav-btn">
        Export
      </button>
    </nav>
  </header>

  <div class="main-content">
    <div class="code-panel">
      <div class="editor-header">
        <span class="file-tab active">model.py</span>
        <button on:click={executeCode} class="nav-btn" disabled={isExecuting}>
          <span class="button-content">
            {#if isExecuting}
              <img src="/progress.svg" alt="Executing..." class="progress-icon" />
            {:else}
              Execute
            {/if}
          </span>
        </button>
      </div>
      <div class="code-editor"
        placeholder="Enter your Python code here..."
      ></div>
    </div>

    <div class="visualization-panel">
      <div class="model-preview">
        <iframe id="sandboxFrame" title="sandboxed_iframe" sandbox="allow-scripts" style="width:100%; height:100%; border:none;"
                srcdoc={output_html}>
        </iframe>
      </div>
      <div class="output-console">
        <pre>{output_non_html}</pre>
        <pre style="color: red;">{error}</pre>
        <pre style="color: orange;">{lintErrors.map(e => `${e.message} (line ${editor.state.doc.lineAt(e.from).number}, col ${e.from - editor.state.doc.lineAt(e.from).from + 1})`).join('\n')}</pre>
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

  {#if saveToast}
    <div class="save-toast" transition:fade>
      The code has been saved successfully
    </div>
  {/if}

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
    display: flex;
    align-items: center;
  }

  .nav-btn:hover {
    background: #d0e0ff;
  }

  .button-content {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 50px; /* Set a fixed width to ensure consistent size */
    height: 15px; /* Set a fixed height to ensure consistent size */
  }

  .progress-icon {
    width: 30px;
    height: 30px;
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

  .save-toast {
    position: fixed;
    bottom: 70px;
    left: 50%;
    transform: translateX(-50%);
    background: #24add6;
    color: #fff;
    padding: 10px 20px;
    border-radius: 5px;
    opacity: 0.9;
  }
</style>
