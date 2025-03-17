// Moved functions here so that they can also be imported in the test file

// Maps Ruff rules to corresponding error codes
export function mapSeverity(errorCode) {
    if (errorCode.startsWith('E')) {
      return "error";
    } else if (errorCode.startsWith('W')) {
      return "warning";
    } else {
      return "info";
    }
  }

// Parses the lint output and extracts the line number, column number, error code, and message
export function parseLintErrors(lintOutput, editorState) {
    const errors = [];
    const lines = lintOutput.split('\n');
    const regex = /:(\d+):(\d+):\s(\w+)\s(.+)/;

    // Extracts the line and column number, error code, and message from the lint output
    // Based on the format of the lint output
    // Example: /tmp/script.py:12:1: F821 Undefined name `jj`
    for (const line of lines) {
      const match = line.match(regex);
      if (match) {
        const [, lineNum, colNum, errorCode, message] = match;
        const lineNumInt = parseInt(lineNum);
        const colNumInt = parseInt(colNum);
        console.log(`Line: ${lineNumInt}, Column: ${colNumInt}, Error Code: ${errorCode}, Message: ${message}`);
        const editorLine = editorState.line(lineNumInt); // Get the line at lineNum
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