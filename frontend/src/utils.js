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
export function parseLintErrors(lintOutput, doc) {
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
      const editorLine = doc.line(lineNumInt); // Get the line at lineNum
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