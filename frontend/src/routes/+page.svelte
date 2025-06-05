<script>
  import { onMount, onDestroy } from 'svelte';
  import { EditorView, basicSetup } from "codemirror";  // Imports the editor
  import { keymap } from "@codemirror/view";
  import { indentWithTab } from "@codemirror/commands"; // Imports tab handling
  import { python } from "@codemirror/lang-python";     // Imports Python syntax highlighting
  import { linter, lintGutter } from "@codemirror/lint"; // Imports linting support
  import { fade } from 'svelte/transition'; // Imports smooth transition for a pop-up message
  import { parseLintErrors } from '../utils';
  import JSZip from "jszip"; // Import JSZip for creating zip files
  import { examples } from  '../examples.js';

  let code = "";
  let output_html = "";
  let output_non_html = "";
  let error = "";
  let editor;
  let lintErrors = [];
  let isExecuting = false;
  let saveStatus = 'idle'; // Variable for checking the save status
  let saveToast = false; // Show a pop-up ('toast') whent the code is saved successfully 
  let activeTab = "Model.py"; // Track the active tab  
  let tabs = {
      "Model.py": "",
      "Model.prism": "",
  };
  let dropdownOpen = false; // Examples dropdown menu
  const githubUrl = 'https://github.com/moves-rwth/stormvogel';

  // Save all tabs to local storage
  function saveCode() {
    try {
      // Update the active tab's content in the tabs object
      tabs[activeTab] = editor.state.doc.toString();
      const tabsData = JSON.stringify(tabs); // Convert the tabs object to JSON
      localStorage.setItem("tabs_data", tabsData); // Save the JSON string to local storage
      saveStatus = 'saved';
      saveToast = true;
      setTimeout(() => { // After 2 seconds set saveStatus back to default
        saveStatus = 'idle';
      }, 2000);
      setTimeout(() => { // After 3 seconds set saveToast to false so it fades away
        saveToast = false;
      }, 3000);
    } catch (error) { // If there are errors while saving, output it to the console
      console.error("Failed to save tabs: ", error);
      alert("Error, unable to save tabs.");
    }
  }

  function exportCode() {
    tabs[activeTab] = editor.state.doc.toString(); // Update the active tab's content in the tabs object
    const zip = new JSZip(); // Create a new zip instance
    const now = new Date();
    // Format date as dd-mm-yyyy
    const date = `${String(now.getDate()).padStart(2, '0')}-${String(now.getMonth() + 1).padStart(2, '0')}-${now.getFullYear()}`; 
    console.log("Date: ", date);
    var folder = zip.folder(`stormvogel-playground-${date}`); // Create a folder in the zip with the date in the name

    // Add each tab's content to the folder in the zip
    for (const [fileName, fileContent] of Object.entries(tabs)) {
      folder.file(fileName, fileContent);
    }

    // Generate the zip file and trigger download
    zip.generateAsync({ type: "blob" }).then((blob) => {
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `stormvogel-playground-${date}.zip`; // Set the name of the zip file
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    });
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

    function switchTab(tabName) {
      // Save the current tab's content before switching
      tabs[activeTab] = editor.state.doc.toString();
      if (activeTab !== tabName) {
        activeTab = tabName;
        code = tabs[activeTab]; // Load the selected tab's content
        editor.dispatch({
          changes: { from: 0, to: editor.state.doc.length, insert: code },
        });
      }
    }

    function loadExample(exampleTitle) {
      // Get the example from the predefined examples list
      const example = examples.find(e => e.title === exampleTitle);
      if (example && example.files) {
        // Merge example tabs into current tabs (overwrite if name exists)
        tabs = { ...tabs, ...example.files };
        // Set the first file of the example as the active tab
        activeTab = Object.keys(example.files)[0];
        code = tabs[activeTab];
        editor.dispatch({
          changes: { 
            from: 0, 
            to: editor.state.doc.length, 
            insert: code 
          }
        });
        dropdownOpen = false;
      }
    }

    function closeTab(tabName) {
      if (Object.keys(tabs).length > 1) {
        const updatedTabs = { ...tabs }; // Create a copy of the tabs object
        delete updatedTabs[tabName]; // Remove the tab
        tabs = updatedTabs; // Update the tabs object
  
        if (activeTab === tabName) {
          activeTab = Object.keys(tabs)[0]; // Switch to the first available tab
          code = tabs[activeTab]; // Update the editor content
          editor.dispatch({
            changes: { from: 0, to: editor.state.doc.length, insert: code }
          });
        }
      } else {
        alert("At least one tab must remain open.");
      }
    }

    function addTab() {
      let newTabIndex = 1;
      while (tabs[`Tab${newTabIndex}.py`] !== undefined) {
        newTabIndex++; // Find the next available unique tab name
      }
      const newTabName = `Tab${newTabIndex}.py`;
      tabs = { ...tabs, [newTabName]: "" }; 
      activeTab = newTabName; // Set the new tab as active
      code = tabs[activeTab]; // Update the editor content
      editor.dispatch({
        changes: { from: 0, to: editor.state.doc.length, insert: code }
      });
    }

    function renameActiveTab() {
      const newTabName = prompt("Enter new name for the active tab:", activeTab);
      if (newTabName && newTabName !== activeTab && !tabs[newTabName]) {
        const updatedTabs = { ...tabs };
        updatedTabs[newTabName] = updatedTabs[activeTab];
        delete updatedTabs[activeTab];
        tabs = updatedTabs;
        activeTab = newTabName;
      } else if (tabs[newTabName]) {
        alert("A tab with this name already exists.");
      }
    }

    // Enable horizontal scrolling with the mouse wheel
    function tabScrollHandler() {
      const tabContainer = document.querySelector(".tab-container");
      if (tabContainer) {
        tabContainer.addEventListener("wheel", (event) => {
          if (event.deltaY !== 0) {
            event.preventDefault();
            tabContainer.scrollLeft += event.deltaY;
          }
        });
      }
    }

    function getTabData() {
      const savedTabs = localStorage.getItem("tabs_data");
      if (savedTabs) {
        tabs = JSON.parse(savedTabs); // Parse the JSON string back into an object
        activeTab = Object.keys(tabs)[0]; // Set the first tab as active
        code = tabs[activeTab]; // Load the content of the active tab
      }
    }

    onMount(() => {
      // Load tabs from local storage
      window.addEventListener("beforeunload", function () {
        saveCode();
        stopExecution();
      });

      getTabData();   // Load the tabs from local storage
      createEditor(); // Load the editor
      startupBackend();
      tabScrollHandler();
    });

    onDestroy(() => {
        window.removeEventListener("beforeunload", function () {
            saveCode();
            stopExecution();
        });
    });

  async function startupBackend() {
    try {
        const response = await fetch('/api/startup', {
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

  async function saveTabs() {
    try {
        const response = await fetch('/api/save-tabs', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ tabs }),
            credentials: 'include'
        });

        const result = await response.json();
        if (result.status !== 'success') {
            console.error('Error saving tabs:', result.message);
            alert('Error saving tabs: ' + result.message);
            return false;
        }

        console.log('Tabs saved successfully in the container.');
        return true;
    } catch (e) {
        console.error('Failed to save tabs to container:', e);
        return false;
    }
}

  async function executeCode() {
    isExecuting = true;
    // Save all tabs to the container before execution
    const tabsSaved = await saveTabs();
    if (!tabsSaved) {
        isExecuting = false;
        return;
    }

    // Execute the active tab's code
    const code = editor.state.doc.toString();
    try {
      const response = await fetch('/api/execute', {
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
          const response = await fetch('/api/stop', {
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
      const response = await fetch('/api/lint', {
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
        lintErrors = parseLintErrors(result.lint, editor.state.doc);
      }else{
        console.log("error", result.error);
        lintErrors = parseLintErrors(result.error, editor.state.doc);
      }
    } catch (e) {
      lintErrors = [{ from: 0, to: 0, severity: "error", message: "Failed to connect to linting server" }];
    }
    return lintErrors;
  }

</script>

<svelte:head>
  <title>Stormvogel Playground</title>
</svelte:head>

<div class="container">
  <header>
    <div class="header-left">
      <h1>Stormvogel Playground</h1>
      <a href={githubUrl} target="_blank" rel="noopener noreferrer">
        <img src="github-mark.svg" alt="Github Repo" class="github-logo"/>
      </a>
    </div>
    <nav>
      <div class="dropdown-container">
        <button class="nav-btn btn-examples"
        on:click={() => dropdownOpen = !dropdownOpen}>
        Examples
        </button>  

        {#if dropdownOpen}
          <div class="dropdown-menu">
            {#each examples as example}
              <button class="nav-btn"
                on:click={() => loadExample(example.title)}>{example.title}</button>
            {/each}
          </div>
        {/if}

      </div>
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
        <div class="tab-container">
          {#each Object.keys(tabs) as tabName}
              <div
                  class="tab {activeTab === tabName ? 'active' : ''}"
                  role="button"
                  tabindex="0"
                  data-tab-name={tabName}
                  on:click={() => {
                    if (activeTab === tabName) {
                      renameActiveTab();
                    } else {
                      switchTab(tabName);
                    }
                  }}
                  on:keydown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      if (activeTab === tabName) {
                        renameActiveTab();
                      } else {
                        switchTab(tabName);
                      }
                    }
                  }}
              >
                  {tabName}
                  {#if activeTab === tabName}
                      <button
                          type="button"
                          class="close-tab"
                          on:click={(e) => {
                              e.stopPropagation();
                              closeTab(tabName);
                          }}
                          on:keydown={(e) => {
                              if (
                                  e.key === "Enter" ||
                                  e.key === " "
                              ) {
                                  e.preventDefault();
                                  e.stopPropagation();
                                  closeTab(tabName);
                              }
                          }}
                      >
                        ×
                      </button>
                  {/if}
              </div>
          {/each}

          <button type="button" class="tab add-tab" on:click={addTab}
              >+</button
          >
      </div>
        <button 
          on:click={executeCode} 
          class="nav-btn" 
          style={isExecuting ? "background: oklch(93.2% 0.032 255.585);" : ""}
        >
          <span class="button-content">
            {#if isExecuting}
              <img src="/progress.svg" alt="Executing..." class="progress-icon" />
            {:else}
              <span>▶ Run</span>
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
        <pre id="output-non-html">{output_non_html}</pre>
        <pre id="error" style="color: red;">{error}</pre>
        <pre id="lint-errors" style="color: orange;">{lintErrors.map(e => `${e.message} (line ${editor.state.doc.lineAt(e.from).number}, col ${e.from - editor.state.doc.lineAt(e.from).from + 1})`).join('\n')}</pre>
      </div>
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
    background: oklch(88.2% 0.059 254.128);
    padding: 4px 16px;
    border-bottom: 1px solid #ddd;
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

  .tab-container {
        margin-left: -12px;
        display: flex;
        background: oklch(93.2% 0.032 255.585); 
        padding: 4px;
        border-radius: 5px;
        position: relative;
        gap: 4px;
        overflow-x: auto;
        overflow-y: hidden;
        white-space: nowrap;
        scrollbar-color: oklch(88.2% 0.059 254.128) transparent;
        margin-bottom: 0px;
  }

  .tab {
        padding: 6px 1rem;
        background: oklch(97% 0.014 254.604); /* Light background */
        border: 2px solid #d0e1f9; /* Subtle border */
        border-radius: 5px;
        cursor: pointer;
        transition: all 0.2s ease;
        font-weight: 500;
        font-size: 1rem;
        color: rgb(80, 80, 80);
        position: relative;
        z-index: 0;
  }

  .tab.active {
        background: white;
        z-index: 1;
        box-shadow: 0 3px 6px rgba(0, 0, 0, 0.15);
        color: #000;
        border: none;
  }

  .tab:hover:not(.active) {
        background-color: #c7ddff; /* Light blue on hover */
        border-color: oklch(62.3% 0.214 259.815);
  }

  .close-tab {
    margin-left: 2px;   /* optional slight left spacing */
    margin-right: -8px; /* shift the button a bit into the rounded edge */
    font-size: 1rem;
    color: rgb(102, 102, 102);
    cursor: pointer;
    font-weight: bold;
    border: none;
    width: 24px;  /* Set a fixed width  for the round button */
    height: 24px; /* Set a fixed height for the round button */
    border-radius: 50%;    /* Make it round */
    background: #f0f0f0; /* Light background */
    transition: background 0.3s, color 0.3s;
  }

  .close-tab:hover {
    background: #cecece; /* Slightly darker background on hover */
  }

  .nav-btn {
    background: oklch(55.7% 0.165 254.624);
    color: #fff;
    border: none;
    font-weight: 500;
    font-size: 1rem;
    padding: 10px 20px;
    margin: 0 4px;
    cursor: pointer;
    border-radius: 5px; /* Rounded pills */
    transition: all 0.2s ease;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  }

  .nav-btn:hover {
    background: oklch(93.2% 0.032 255.585);
    color: oklch(40.7% 0.165 254.624);
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  }
  
  .dropdown-container {
    position: relative;
    display: inline-block;
  }

  .dropdown-menu {
    position: absolute;
    top: 100%;
    left: 50%;
    transform: translateX(-50%);
    z-index: 10;
    min-width: 100%;
    display: flex;
    flex-direction: column;
    box-sizing: border-box;
  }

  .btn-examples {
    width: 200px;
  }

  .github-logo {
    width: 40px;
    height: 40px;
  }

  .header-left {
    display: flex;
    align-items: center; 
    gap: 20px;
  }

</style>
