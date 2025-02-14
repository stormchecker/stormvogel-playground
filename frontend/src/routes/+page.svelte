<script>
    let code = '';
    let output = '';
    let error = '';
  
    async function executeCode() {
      const response = await fetch('http://localhost:5000/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ code })
      });
  
      const result = await response.json();
      output = result.output;
      error = result.error;
    }
  </script>
  
  <main>
    <h1>Execute Python Code</h1>
    <textarea bind:value={code} placeholder="Enter your Python code here..."></textarea>
    <button on:click={executeCode}>Execute</button>
    <pre>{output}</pre>
    <pre style="color: red;">{error}</pre>
  </main>
  
  <style>
    /* Add your styles here */
  </style>
  
