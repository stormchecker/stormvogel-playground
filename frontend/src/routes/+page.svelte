<script>
  import { onMount, onDestroy } from 'svelte';
  import { EditorView, basicSetup } from "codemirror";  // Imports the editor
  import { keymap } from "@codemirror/view";
  import { indentWithTab } from "@codemirror/commands"; // Imports tab handling
  import { python } from "@codemirror/lang-python";     // Imports Python syntax highlighting
  import { linter, lintGutter } from "@codemirror/lint"; // Imports linting support
  import { fade } from 'svelte/transition'; // Imports smooth transition for a pop-up message
  import { parseLintErrors } from '../utils';
  import { examples } from  '../examples.js';
  import LZString from 'lz-string';

  let code = "";
  let output_html = "";
  $: sandboxHtml = makeResponsiveOutput(output_html);
  let output_non_html = "";
  let error = "";
  let editor;
  let lintErrors = [];
  let isExecuting = false;
  let isStopping = false;
  let backendStatus = 'starting';
  let toastMessage = '';
  let toastKind = 'info';
  let toastTimer;
  let renameDialogOpen = false;
  let renameValue = '';
  let activeTab = "welcome.py"; // Track the active tab
  let mobileView = 'editor';
  let editorWidth = 50;
  let previewHeight = 66;
  let resizeCleanup;
  let saveTimer;
  $: isExecutableFile = activeTab.toLowerCase().endsWith('.py');
  let tabs = {
    "welcome.py": `# Welcome to the Stormvogel playground!
# Here is a small snippet to get you started:
from stormvogel import *
from stormvogel.bird import *

# This function describes the transition relation
def delta(state):
    return [
        (1/2, (state + 1) % 5),
        (1/2, (state - 1) % 5)
    ]
def rewards(state):
    return {"R": state / 5}
def labels(state):
    return str(state)

model = build_bird(
    delta, init=0, labels=labels, rewards=rewards, modeltype=ModelType.DTMC
)
# Modify the model directly
for state in model.get_states_with_label("4"):
  state.add_label("goal")

# Perform model checking using Storm
result = model_checking(model, "R=? [F \\\"goal\\\"]")

# Interactive visualization
show(model, result)`,
  };
  let dropdownOpen = false; // Examples dropdown menu
  let shareMenuOpen = false;
  let expandedCategories = {}; // Track which categories are expanded
  const githubUrl = 'https://github.com/stormchecker/stormvogel';
  const docsUrl = 'https://stormchecker.github.io/stormvogel/';
  let containerTag = "nightly"; // Selected container image tag

  function makeResponsiveOutput(html) {
    if (!html) {
      return '';
    }

    const resizeSupport = `
      <style>
        html, body { width: 100%; height: 100%; margin: 0; overflow: hidden; }
        body > div { width: 100% !important; height: 100% !important; min-height: 0 !important; box-sizing: border-box; }
        canvas, svg { width: 100% !important; height: 100% !important; object-fit: contain; }
      </style>
      <script>
        (() => {
          let frame;
          const notifyResize = () => {
            cancelAnimationFrame(frame);
            frame = requestAnimationFrame(() => window.dispatchEvent(new Event('resize')));
          };
          new ResizeObserver(notifyResize).observe(document.documentElement);
          window.addEventListener('load', notifyResize);
        })();
      </` + `script>`;

    return /<\/body>/i.test(html)
      ? html.replace(/<\/body>/i, `${resizeSupport}</body>`)
      : `${html}${resizeSupport}`;
  }

  // Group examples by category
  $: groupedExamples = examples.reduce((acc, example) => {
    const category = example.category || 'Uncategorized';
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(example);
    return acc;
  }, {});

  function toggleCategory(category) {
    expandedCategories[category] = !expandedCategories[category];
    expandedCategories = { ...expandedCategories }; // Trigger reactivity
  }

  // Persist the workspace automatically after edits.
  function saveCode() {
    try {
      if (editor && activeTab) {
        tabs[activeTab] = editor.state.doc.toString();
      }
      localStorage.setItem("tabs_data", JSON.stringify(tabs));
    } catch (error) {
      console.error("Failed to save tabs: ", error);
    }
  }

  function scheduleSave() {
    clearTimeout(saveTimer);
    saveTimer = setTimeout(saveCode, 400);
  }

  function handleBeforeUnload() {
    saveCode();
    stopExecution();
  }

  function showToast(message, kind = 'info') {
    clearTimeout(toastTimer);
    toastMessage = message;
    toastKind = kind;
    toastTimer = setTimeout(() => { toastMessage = ''; }, 3000);
  }

  async function shareCode() {
    shareMenuOpen = false;
    tabs[activeTab] = editor.state.doc.toString();
    const params = new URLSearchParams();
    params.set('active', activeTab);
    Object.entries(tabs).forEach(([name, content], i) => {
      params.set(`tab${i}`, name);
      params.set(`code${i}`, LZString.compressToEncodedURIComponent(content));
    });
    const url = `${window.location.origin}${window.location.pathname}?${params.toString()}`;
    try {
      await navigator.clipboard.writeText(url);
      showToast('Share link copied to clipboard');
    } catch (error) {
      const textarea = document.createElement('textarea');
      textarea.value = url;
      textarea.style.position = 'fixed';
      textarea.style.opacity = '0';
      document.body.appendChild(textarea);
      textarea.select();
      const copied = document.execCommand('copy');
      textarea.remove();
      showToast(copied ? 'Share link copied to clipboard' : 'Could not copy the share link', copied ? 'info' : 'error');
    }
  }

  async function exportCode() {
    shareMenuOpen = false;
    tabs[activeTab] = editor.state.doc.toString(); // Update the active tab's content in the tabs object
    const { default: JSZip } = await import('jszip');
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
      extensions: [
        basicSetup,
        keymap.of([indentWithTab]),
        python(),
        lintGutter(),
        linter(lintCode),
        EditorView.updateListener.of((update) => {
          if (update.docChanged) {
            tabs[activeTab] = update.state.doc.toString();
            scheduleSave();
          }
        })
      ],
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
      scheduleSave();
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
      scheduleSave();
  
    if (activeTab === tabName) {
      activeTab = Object.keys(tabs)[0]; // Switch to the first available tab
      code = tabs[activeTab]; // Update the editor content
      editor.dispatch({
        changes: { from: 0, to: editor.state.doc.length, insert: code }
      });
    }
    } else {
      showToast("At least one tab must remain open", 'error');
    }
  }

  function addTab() {
    let newTabIndex = 1;
    while (tabs[`Tab${newTabIndex}.py`] !== undefined) {
      newTabIndex++; // Find the next available unique tab name
    }
    const newTabName = `Tab${newTabIndex}.py`;
    tabs = { ...tabs, [newTabName]: "" };
    scheduleSave();
    activeTab = newTabName; // Set the new tab as active
    code = tabs[activeTab]; // Update the editor content
    editor.dispatch({
      changes: { from: 0, to: editor.state.doc.length, insert: code }
    });
  }

  function renameActiveTab() {
    renameValue = activeTab;
    renameDialogOpen = true;
  }

  function submitRename() {
    const newTabName = renameValue.trim();
    if (!newTabName) {
      showToast('File name cannot be empty', 'error');
      return;
    }
    if (newTabName === activeTab) {
      renameDialogOpen = false;
      return;
    }
    if (tabs[newTabName]) {
      showToast('A tab with this name already exists', 'error');
      return;
    }

    const updatedTabs = { ...tabs };
    updatedTabs[newTabName] = updatedTabs[activeTab];
    delete updatedTabs[activeTab];
    tabs = updatedTabs;
    activeTab = newTabName;
    renameDialogOpen = false;
    scheduleSave();
  }

  function closeMenus(event) {
    if (!event.target.closest('.dropdown-container')) {
      dropdownOpen = false;
    }
    if (!event.target.closest('.share-container')) {
      shareMenuOpen = false;
    }
  }

  function closeOverlays(event) {
    if (event.key === 'Escape') {
      dropdownOpen = false;
      shareMenuOpen = false;
      renameDialogOpen = false;
    }
  }

  function startResize(event, direction) {
    if (window.innerWidth <= 900) {
      return;
    }

    event.preventDefault();
    event.currentTarget.setPointerCapture?.(event.pointerId);
    const panel = direction === 'columns'
      ? document.querySelector('.main-content')
      : document.querySelector('.visualization-panel');
    const bounds = panel.getBoundingClientRect();
    const property = direction === 'columns' ? '--editor-width' : '--preview-height';
    let latestEvent = event;
    let frame;
    let value = direction === 'columns' ? editorWidth : previewHeight;

    const updateSize = () => {
      frame = undefined;
      const rawValue = direction === 'columns'
        ? ((latestEvent.clientX - bounds.left) / bounds.width) * 100
        : ((latestEvent.clientY - bounds.top) / bounds.height) * 100;
      value = Math.min(75, Math.max(25, rawValue));
      panel.style.setProperty(property, `${value}%`);
    };

    const resize = (moveEvent) => {
      latestEvent = moveEvent;
      if (!frame) {
        frame = requestAnimationFrame(updateSize);
      }
    };

    const stopResize = () => {
      if (frame) {
        cancelAnimationFrame(frame);
        updateSize();
      }
      if (direction === 'columns') {
        editorWidth = value;
      } else {
        previewHeight = value;
      }
      document.body.classList.remove('resizing');
      document.removeEventListener('pointermove', resize);
      document.removeEventListener('pointerup', stopResize);
      document.removeEventListener('pointercancel', stopResize);
      resizeCleanup = undefined;
    };

    resizeCleanup?.();
    resizeCleanup = stopResize;
    document.body.classList.add('resizing');
    document.addEventListener('pointermove', resize);
    document.addEventListener('pointerup', stopResize);
    document.addEventListener('pointercancel', stopResize);
  }

  function resizeWithKeyboard(event, direction) {
    const step = event.shiftKey ? 5 : 2;
    if (direction === 'columns' && ['ArrowLeft', 'ArrowRight'].includes(event.key)) {
      event.preventDefault();
      editorWidth = Math.min(75, Math.max(25, editorWidth + (event.key === 'ArrowRight' ? step : -step)));
    } else if (direction === 'rows' && ['ArrowUp', 'ArrowDown'].includes(event.key)) {
      event.preventDefault();
      previewHeight = Math.min(75, Math.max(25, previewHeight + (event.key === 'ArrowDown' ? step : -step)));
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
    } else {
      code = tabs[activeTab];
    }
  }

  onMount(() => {
    // Load tabs from local storage
    window.addEventListener("beforeunload", handleBeforeUnload);
    document.addEventListener('click', closeMenus);
    document.addEventListener('keydown', closeOverlays);

    // Check for shared workspace in URL params
    const params = new URLSearchParams(window.location.search);
    const sharedActive = params.get('active');
    const gistId = params.get('gist');

    if (gistId) {
      fetch(`https://api.github.com/gists/${gistId}`).then(response => response.json()).then(data => {
      const gistTabs = {};
      for(const[filename, fileObj] of Object.entries(data.files)){
        gistTabs[filename] = fileObj.content;
      }
      tabs = gistTabs;
      activeTab = sharedActive && tabs[sharedActive] ? sharedActive : Object.keys(tabs)[0];
      code = tabs[activeTab];

      if (editor) {
        editor.dispatch({
          changes: { from: 0, to: editor.state.doc.length, insert: code }
        });
      }
      }).catch(error => {
        console.error('Gist could not be pulled: ', error);
        getTabData();
      })
      }else if(sharedActive){
      try {
        const sharedTabs = {};
        let i = 0;
        while (params.has(`tab${i}`)) {
          const name = params.get(`tab${i}`);
          const content = LZString.decompressFromEncodedURIComponent(params.get(`code${i}`));
          sharedTabs[name] = content;
          i++;
        }
        tabs = sharedTabs;
        activeTab = sharedActive;
        code = tabs[activeTab];
      } catch (e) {
        console.error('Failed to decode shared workspace:', e);
        getTabData();
      }
    } else {
      getTabData();   // Load the tabs from local storage
    }
    createEditor(); // Load the editor
    startupBackend();
    tabScrollHandler();
  });

  onDestroy(() => {
    resizeCleanup?.();
    clearTimeout(saveTimer);
    clearTimeout(toastTimer);
    saveCode();
    window.removeEventListener("beforeunload", handleBeforeUnload);
    document.removeEventListener('click', closeMenus);
    document.removeEventListener('keydown', closeOverlays);
  });

  async function startupBackend(tag = containerTag) {
    backendStatus = 'starting';
    try {
      const response = await fetch('/api/startup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ tag }),
        credentials: 'include'
      });

      const result = await response.json();
      if (result.status === 'success') {
        backendStatus = 'ready';
        console.log(result.message);
      } else {
        backendStatus = 'error';
        console.error('Error:', result.message);
      }
    } catch (e) {
      backendStatus = 'error';
      console.error('Failed to startup server backend:', e);
    }
  }

  async function changeContainerTag(newTag) {
    containerTag = newTag;
    output_html = "";
    output_non_html = "";
    error = "";
    await startupBackend(newTag);
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
        showToast('Could not prepare the workspace for execution', 'error');
        return false;
      }

      console.log('Tabs saved successfully in the container.');
      return true;
    } catch (e) {
      console.error('Failed to save tabs to container:', e);
      showToast('Could not connect to the execution backend', 'error');
      return false;
    }
  }

  async function executeCode() {
    // Only Python tabs can be executed. Other files are available to Python
    // scripts in the workspace, but are not executable themselves.
    if (!isExecutableFile || isExecuting || backendStatus !== 'ready') {
      return;
    }

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
        mobileView = output_html ? 'preview' : 'console';
      } else {
        error = result.message || "An unknown error occurred";
        mobileView = 'console';
      }
        
    } catch (e) {
      output_html = "";
      output_non_html = "";
      error = "Failed to connect to execution server";
      mobileView = 'console';
    } finally {
      isExecuting = false;
    }
  }

  async function stopExecution() {
    const showStatus = isExecuting;
    if (showStatus) {
      isStopping = true;
    }
    try {
      const response = await fetch('/api/stop', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include'
      });

      const result = await response.json();
      if (showStatus) {
        output_non_html = result.message || 'Execution stopped.';
        error = '';
        mobileView = 'console';
      }
      return result.message;
    } catch (e) {
      if (showStatus) {
        error = "Failed to stop execution";
        mobileView = 'console';
      }
      return "Failed to connect to execution server";
    } finally {
      if (showStatus) {
        isExecuting = false;
        isStopping = false;
      }
    }
  }

  async function lintCode(view) {
    const code = view.state.doc.toString();
    // Only lint Python files while execution is idle.
    if (isExecuting || !activeTab.endsWith('.py')) {
      lintErrors = [];
      return lintErrors;
    }
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
        <img src="bird.png" alt="Github Repo" class="github-logo"/>
      </a>
      <a href={docsUrl} class=nav-link target="_blank" rel="noopener noreferrer">
        Documentation
      </a>
    </div>
    <nav>
      <div class="version-select-wrapper">
        <span class="version-label">Version:</span>
        <select
          class="nav-select"
          value={containerTag}
          disabled={backendStatus === 'starting'}
          on:change={(e) => changeContainerTag(e.target.value)}
        >
          <option value="latest">latest</option>
          <option value="nightly">nightly</option>
          <option value="experimental">experimental</option>
        </select>
      </div>
      <div class="dropdown-container">
        <button class="nav-btn btn-examples"
        aria-expanded={dropdownOpen}
        on:click={() => { dropdownOpen = !dropdownOpen; shareMenuOpen = false; }}>
        Examples
        </button>

        {#if dropdownOpen}
          <div class="dropdown-menu">
            {#each Object.entries(groupedExamples) as [category, categoryExamples]}
              <div class="category-section">
                <div class="category-header"
                  on:click={() => toggleCategory(category)}
                  on:keydown={(e) => e.key === 'Enter' && toggleCategory(category)}
                  role="button"
                  tabindex="0">
                  <span class="category-title">{category}</span>
                  <span class="category-arrow" class:expanded={expandedCategories[category]}>
                    ▼
                  </span>
                </div>

                {#if expandedCategories[category]}
                  <div class="category-examples">
                    {#each categoryExamples as example}
                      <button class="nav-btn example-btn"
                        on:click={() => loadExample(example.title)}>
                        {example.title}
                      </button>
                    {/each}
                  </div>
                {/if}
              </div>
            {/each}
          </div>
        {/if}

      </div>
      <div class="share-container">
        <button
          class="nav-btn"
          aria-expanded={shareMenuOpen}
          on:click={() => { shareMenuOpen = !shareMenuOpen; dropdownOpen = false; }}
        >
          Share
        </button>
        {#if shareMenuOpen}
          <div class="share-menu">
            <button on:click={shareCode}>Copy share link</button>
            <button on:click={exportCode}>Download ZIP</button>
          </div>
        {/if}
      </div>
    </nav>
  </header>

  <div class="mobile-view-switcher" role="tablist" aria-label="Workspace view">
    <button class:active={mobileView === 'editor'} on:click={() => mobileView = 'editor'} role="tab" aria-selected={mobileView === 'editor'}>Editor</button>
    <button class:active={mobileView === 'preview'} on:click={() => mobileView = 'preview'} role="tab" aria-selected={mobileView === 'preview'}>Preview</button>
    <button class:active={mobileView === 'console'} on:click={() => mobileView = 'console'} role="tab" aria-selected={mobileView === 'console'}>Console</button>
  </div>

  <div
    class="main-content"
    class:show-editor={mobileView === 'editor'}
    class:show-preview={mobileView === 'preview'}
    class:show-console={mobileView === 'console'}
    style={`--editor-width: ${editorWidth}%;`}
  >
    <div class="code-panel">
      <div class="editor-header">
        <div class="tab-container">
          {#each Object.keys(tabs) as tabName}
              <div
                  class="tab {activeTab === tabName ? 'active' : ''}"
                  role="button"
                  tabindex="0"
                  data-tab-name={tabName}
                  title={activeTab === tabName ? 'Double-click to rename' : `Open ${tabName}`}
                  on:click={() => switchTab(tabName)}
                  on:dblclick={() => activeTab === tabName && renameActiveTab()}
                  on:keydown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      switchTab(tabName);
                    } else if (e.key === "F2" && activeTab === tabName) {
                      e.preventDefault();
                      renameActiveTab();
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
          on:click={isExecuting ? stopExecution : executeCode}
          class="nav-btn"
          class:stop-btn={isExecuting}
          disabled={isStopping || (!isExecuting && (!isExecutableFile || backendStatus !== 'ready'))}
          title={isExecuting ? 'Stop execution' : backendStatus === 'error' ? 'Backend unavailable' : backendStatus !== 'ready' ? 'Waiting for backend' : isExecutableFile ? 'Run the active Python file' : 'Only Python files can be run'}
        >
          <span class="button-content">
            {#if isStopping}
              <img src="/progress.svg" alt="Stopping..." class="progress-icon" />
            {:else if isExecuting}
              <span>■ Stop</span>
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

    <div
      class="resizer vertical-resizer"
      role="slider"
      aria-label="Editor width"
      aria-orientation="horizontal"
      aria-valuemin="25"
      aria-valuemax="75"
      aria-valuenow={Math.round(editorWidth)}
      tabindex="0"
      on:pointerdown={(event) => startResize(event, 'columns')}
      on:keydown={(event) => resizeWithKeyboard(event, 'columns')}
    ></div>

    <div class="visualization-panel" style={`--preview-height: ${previewHeight}%;`}>
      <div class="model-preview">
        {#if !output_html}
          <div class="empty-state" title="Run code that produces a visualization">No preview output yet</div>
        {/if}
        <iframe id="sandboxFrame" title="Model visualization output" sandbox="allow-scripts" style="width:100%; height:100%; border:none;"
                srcdoc={sandboxHtml}>
        </iframe>
      </div>
      <div
        class="resizer horizontal-resizer"
        role="slider"
        aria-label="Preview height"
        aria-orientation="vertical"
        aria-valuemin="25"
        aria-valuemax="75"
        aria-valuenow={Math.round(previewHeight)}
        tabindex="0"
        on:pointerdown={(event) => startResize(event, 'rows')}
        on:keydown={(event) => resizeWithKeyboard(event, 'rows')}
      ></div>
      <div class="output-console">
        {#if !output_non_html && !error}
          <div class="empty-state" title="Standard output and execution errors appear here">No console output yet</div>
        {/if}
        <pre id="output-non-html">{output_non_html}</pre>
        <pre id="error" style="color: red;">{error}</pre>
      </div>
    </div>
  </div>
  {#if renameDialogOpen}
    <div
      class="modal-backdrop"
      role="presentation"
      on:click={(event) => event.target === event.currentTarget && (renameDialogOpen = false)}
    >
      <div class="rename-dialog" role="dialog" aria-modal="true" aria-labelledby="rename-title">
        <form on:submit={(event) => { event.preventDefault(); submitRename(); }}>
          <h2 id="rename-title">Rename file</h2>
          <label for="rename-input">File name</label>
          <input id="rename-input" bind:value={renameValue} spellcheck="false" />
          <div class="dialog-actions">
            <button type="button" on:click={() => renameDialogOpen = false}>Cancel</button>
            <button type="submit" class="primary">Rename</button>
          </div>
        </form>
      </div>
    </div>
  {/if}

  {#if toastMessage}
    <div class="save-toast" class:error-toast={toastKind === 'error'} role="status" aria-live="polite" transition:fade>
      {toastMessage}
    </div>
  {/if}

</div>

<style>
  :global(*) {
    box-sizing: border-box;
  }

  :global(html) {
    width: 100%;
    height: 100%;
    overflow: hidden;
    overscroll-behavior: none;
  }

  :global(body) {
    margin: 0;
    padding: 0;
    background-color: #ffffff;
    color: #333333;
    font-family: 'Arial', sans-serif;
    height: 100%;
    overflow: hidden;
  }

  :global(#app) {
    width: 100%;
    height: 100%;
    overflow: hidden;
  }

  .container {
    display: flex;
    flex-direction: column;
    width: 100%;
    max-width: 100vw;
    height: 100vh;
    height: 100dvh;
    min-width: 0;
    overflow: hidden;
  }

  header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
    min-width: 0;
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
    align-items: center;
    min-width: 0;
  }

  .button-content {
    display: flex;
    align-items: center;
    justify-content: center;
    min-width: 50px;
    height: 15px;
    white-space: nowrap;
  }

  .progress-icon {
    width: 30px;
    height: 30px;
  }

  .main-content {
    display: grid;
    grid-template-columns: minmax(0, calc(var(--editor-width) - 6px)) 12px minmax(0, 1fr);
    flex-grow: 1;
    gap: 0;
    padding: 1rem;
    background-color: #fafafa;
    overflow: hidden;
  }

  .code-panel {
    min-width: 0;
    min-height: 0;
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
    min-width: 0;
    align-items: center;
    background: oklch(88.2% 0.059 254.128);
    padding: 4px 16px;
    border-bottom: 1px solid #ddd;
  }

  .code-editor {
    flex-grow: 1;
    min-width: 0;
    min-height: 0;
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
    min-width: 0;
    min-height: 0;
    gap: 0;
    overflow: hidden;
  }

  .resizer {
    position: relative;
    z-index: 2;
    flex: 0 0 12px;
    padding: 0;
    border: 0;
    background: transparent;
    touch-action: none;
  }

  .resizer::after {
    position: absolute;
    content: '';
    border-radius: 2px;
    background: #cbd5e1;
    transition: background 0.15s;
  }

  .resizer:hover::after,
  .resizer:focus-visible::after {
    background: oklch(55.7% 0.165 254.624);
  }

  .vertical-resizer {
    cursor: col-resize;
  }

  .vertical-resizer::after {
    top: 0;
    bottom: 0;
    left: 5px;
    width: 2px;
  }

  .horizontal-resizer {
    cursor: row-resize;
  }

  .horizontal-resizer::after {
    top: 5px;
    right: 0;
    left: 0;
    height: 2px;
  }

  :global(body.resizing) {
    user-select: none;
  }

  :global(body.resizing iframe) {
    pointer-events: none;
  }

  .model-preview {
    position: relative;
    flex: 0 0 calc(var(--preview-height) - 6px);
    background: #f5f5f5;
    border-radius: 4px;
    padding: 1rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    overflow: hidden;
  }

  .output-console {
    position: relative;
    flex: 1 1 0;
    background: #fff;
    padding: 1rem;
    border-radius: 4px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    overflow: auto;
    font-family: 'Courier New', monospace;
  }

  .empty-state {
    position: absolute;
    inset: 0;
    z-index: 1;
    display: grid;
    place-items: center;
    color: #777;
    font-family: 'Arial', sans-serif;
    font-size: 0.9rem;
    pointer-events: none;
  }

  .save-toast {
    position: fixed;
    bottom: 70px;
    left: 50%;
    z-index: 40;
    transform: translateX(-50%);
    background: #246b9e;
    color: #fff;
    padding: 10px 20px;
    border-radius: 5px;
    opacity: 0.95;
  }

  .error-toast {
    background: #b42318;
  }

  .modal-backdrop {
    position: fixed;
    inset: 0;
    z-index: 30;
    display: grid;
    place-items: center;
    padding: 1rem;
    background: rgba(0, 0, 0, 0.35);
  }

  .rename-dialog {
    width: min(100%, 380px);
    padding: 1.25rem;
    border-radius: 8px;
    background: #fff;
    box-shadow: 0 16px 40px rgba(0, 0, 0, 0.22);
  }

  .rename-dialog h2 {
    margin: 0 0 1rem;
    font-size: 1.15rem;
  }

  .rename-dialog label {
    display: block;
    margin-bottom: 0.35rem;
    font-size: 0.85rem;
    font-weight: 600;
  }

  .rename-dialog input {
    width: 100%;
    padding: 9px 10px;
    border: 1px solid #aaa;
    border-radius: 5px;
    font: inherit;
  }

  .dialog-actions {
    display: flex;
    justify-content: flex-end;
    gap: 0.5rem;
    margin-top: 1rem;
  }

  .dialog-actions button {
    padding: 8px 14px;
    border: 0;
    border-radius: 5px;
    cursor: pointer;
  }

  .dialog-actions .primary {
    background: oklch(55.7% 0.165 254.624);
    color: #fff;
  }

  .tab-container {
        flex: 1;
        min-width: 0;
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

  .nav-btn:hover:not(:disabled) {
    background: oklch(93.2% 0.032 255.585);
    color: oklch(40.7% 0.165 254.624);
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  }

  .nav-btn:disabled {
    cursor: not-allowed;
    opacity: 0.5;
  }

  .stop-btn,
  .stop-btn:hover:not(:disabled) {
    background: #b42318;
    color: #fff;
  }

  .version-select-wrapper {
    display: flex;
    align-items: center;
    gap: 6px;
    margin: 0 4px;
  }

  .version-label {
    font-size: 1rem;
    font-weight: 500;
    color: #333;
    white-space: nowrap;
  }

  .nav-select {
    background: oklch(55.7% 0.165 254.624);
    color: #fff;
    border: none;
    font-weight: 500;
    font-size: 1rem;
    padding: 10px 32px 10px 14px;
    cursor: pointer;
    border-radius: 5px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
    appearance: auto;
    -webkit-appearance: auto;
  }

  .nav-select:hover {
    background: oklch(93.2% 0.032 255.585);
    color: oklch(40.7% 0.165 254.624);
  }

  .nav-select option {
    background: #fff;
    color: #333;
  }

  .nav-link {
    padding: 0 1em;
    text-decoration: none;
    color: #000000;
  }

  .example-btn {
    color: #000000;
  }

  .dropdown-container,
  .share-container {
    position: relative;
    display: inline-block;
  }

  .share-menu {
    position: absolute;
    top: calc(100% + 4px);
    right: 4px;
    z-index: 20;
    width: 180px;
    padding: 4px;
    border: 1px solid #ddd;
    border-radius: 5px;
    background: #fff;
    box-shadow: 0 6px 18px rgba(0, 0, 0, 0.16);
  }

  .share-menu button {
    width: 100%;
    padding: 9px 10px;
    border: 0;
    border-radius: 4px;
    background: transparent;
    color: #333;
    text-align: left;
    cursor: pointer;
  }

  .share-menu button:hover {
    background: #f1f5f9;
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
    max-height: 90vh;
    overflow-y: auto;
    overflow-x: hidden;
  }

  .category-section {
    border-bottom: 1px solid #eee;
  }

  .category-section:last-child {
    border-bottom: none;
  }

  .category-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 12px;
    cursor: pointer;
    background-color: #f8f9fa;
    border: none;
    text-align: left;
    font-weight: 600;
  }

  .category-header:hover {
    background-color: #e9ecef;
  }

  .category-title {
    font-size: 14px;
    color: #495057;
  }

  .category-arrow {
    transition: transform 0.2s ease;
    font-size: 12px;
    color: #6c757d;
  }

  .category-arrow.expanded {
    transform: rotate(180deg);
  }

  .category-examples {
    background-color: #fff;
  }

  .example-btn {
    width: 100%;
    text-align: left;
    padding: 8px 24px;
    border: none;
    background: none;
    cursor: pointer;
    font-size: 13px;
  }

  .example-btn:hover {
    background-color: #f8f9fa;
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
    min-width: 0;
    gap: 20px;
  }

  :global(.code-editor .cm-editor) {
    height: 100%;
  }

  :global(.code-editor .cm-scroller) {
    overflow: auto;
  }

  .mobile-view-switcher {
    display: none;
  }

  /* Let the header wrap before its controls become cramped. */
  @media (max-width: 1200px) {
    header {
      flex-wrap: wrap;
      gap: 0.75rem;
    }

    nav {
      width: 100%;
      justify-content: flex-end;
      flex-wrap: wrap;
      row-gap: 0.5rem;
    }
  }

  /* Stack the workspace while preserving the editor-first layout. */
  @media (max-width: 900px) {
    :global(body) {
      height: auto;
      min-height: 100%;
      overflow-x: hidden;
      overflow-y: auto;
    }

    .container {
      height: auto;
      min-height: 100vh;
      min-height: 100dvh;
    }

    header {
      position: relative;
      padding: 0.875rem 1rem;
    }

    .main-content {
      grid-template-columns: minmax(0, 1fr);
      flex-grow: 0;
      overflow: visible;
    }

    .resizer {
      display: none;
    }

    .code-panel {
      height: clamp(420px, 65dvh, 680px);
    }

    .visualization-panel {
      gap: 1rem;
      overflow: visible;
    }

    .model-preview {
      flex: none;
      height: clamp(320px, 55dvh, 560px);
    }

    .output-console {
      flex: none;
      min-height: 220px;
      max-height: 45dvh;
    }
  }

  @media (max-width: 600px) {
    :global(body) {
      width: 100%;
      height: 100%;
      overflow: hidden;
      overscroll-behavior: none;
    }

    .container {
      height: 100vh;
      height: 100dvh;
      min-height: 0;
    }

    header {
      flex: none;
      gap: 0.5rem;
      padding: max(0.5rem, env(safe-area-inset-top)) 0.75rem 0.5rem;
    }

    .header-left {
      width: 100%;
      gap: 0.65rem;
    }

    h1 {
      flex: 1;
      font-size: 1.05rem;
      line-height: 1.2;
    }

    .github-logo {
      width: 28px;
      height: 28px;
    }

    .nav-link {
      padding: 0;
      font-size: 0.8rem;
    }

    nav {
      width: 100%;
      justify-content: flex-start;
      flex-wrap: nowrap;
      gap: 0.4rem;
      overflow-x: auto;
      scrollbar-width: none;
    }

    nav::-webkit-scrollbar {
      display: none;
    }

    .nav-btn {
      flex: 0 0 auto;
      width: auto;
      min-height: 36px;
      margin: 0;
      padding: 7px 12px;
      font-size: 0.85rem;
      white-space: nowrap;
    }

    .version-select-wrapper {
      flex: 0 0 auto;
      margin: 0;
      gap: 0.3rem;
    }

    .version-label {
      font-size: 0.8rem;
    }

    .nav-select {
      min-height: 36px;
      padding: 7px 24px 7px 8px;
      font-size: 0.8rem;
    }

    .btn-examples {
      width: auto;
    }

    .dropdown-menu,
    .share-menu {
      position: fixed;
      top: 96px;
      right: 0.75rem;
      left: 0.75rem;
      width: auto;
      min-width: 0;
      max-height: 55dvh;
      transform: none;
      border-radius: 5px;
      box-shadow: 0 6px 18px rgba(0, 0, 0, 0.18);
    }

    .mobile-view-switcher {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      flex: none;
      gap: 4px;
      padding: 6px 0.75rem;
      background: #fafafa;
      border-bottom: 1px solid #ddd;
    }

    .mobile-view-switcher button {
      min-height: 34px;
      border: 0;
      border-radius: 5px;
      background: transparent;
      color: #555;
      font-weight: 600;
    }

    .mobile-view-switcher button.active {
      background: oklch(55.7% 0.165 254.624);
      color: white;
    }

    .main-content {
      display: block;
      flex: 1;
      min-height: 0;
      padding: 0.5rem;
      padding-bottom: max(0.5rem, env(safe-area-inset-bottom));
      overflow: hidden;
    }

    .main-content .code-panel,
    .main-content .visualization-panel {
      display: none;
    }

    .main-content.show-editor .code-panel,
    .main-content.show-preview .visualization-panel,
    .main-content.show-console .visualization-panel {
      display: flex;
    }

    .code-panel,
    .visualization-panel {
      width: 100%;
      height: 100%;
    }

    .visualization-panel {
      gap: 0;
    }

    .main-content.show-preview .output-console,
    .main-content.show-console .model-preview {
      display: none;
    }

    .model-preview,
    .output-console {
      flex: 1;
      width: 100%;
      height: auto;
      min-height: 0;
      max-height: none;
      padding: 0.5rem;
    }

    .output-console {
      font-size: 0.85rem;
    }

    .editor-header {
      gap: 0.5rem;
      padding: 4px 8px;
    }

    .tab-container {
      min-width: 0;
      margin-left: 0;
    }

    .tab {
      padding: 6px 0.75rem;
      font-size: 0.9rem;
    }

    .editor-header > .nav-btn {
      flex: 0 0 auto;
      padding-inline: 8px;
    }

    .save-toast {
      right: 0.75rem;
      bottom: max(1rem, env(safe-area-inset-bottom));
      left: 0.75rem;
      width: auto;
      text-align: center;
      transform: none;
    }
  }

  @media (hover: none) {
    .nav-btn:hover:not(:disabled) {
      transform: none;
    }
  }

</style>
