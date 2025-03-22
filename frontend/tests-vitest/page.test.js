import { render, screen, fireEvent } from '@testing-library/svelte';
import Page from '../src/routes/+page.svelte';
import { mapSeverity, parseLintErrors } from '../src/utils.js'; // Import functions
import { vi } from 'vitest';


beforeAll(() => {
  // Mock the element.animate function is necessary because an error is thrown otherwise
  Element.prototype.animate = function() {
    return {
      onfinish: null,
      cancel: () => {}, 
    };
  };

  // Mock the getClientRects function (Used by CodeMirror)
  Range.prototype.getClientRects = function() {
    return {
      length: 0,
      item: () => null,
    };
  };
});

beforeEach(() => {
  localStorage.clear(); // Clear local storage before each test

  // Mock the fetch function
  vi.stubGlobal('fetch', vi.fn((url) => {
    if (url.endsWith('/startup')) {
      return Promise.resolve({
        json: () => Promise.resolve({
          status: 'success',
          message: 'Succeeded in lauching container'
        }),
      });
    } else if (url.endsWith('/lint')) {
      return Promise.resolve({
        json: () => Promise.resolve({
          error: '/script.py:1:1: E001 Example error message'
        }),
      });
    }
    return Promise.reject(new Error('Unknown URL'));
  }));
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe('Page Component', () => {
  test('renders the Model Playground title', () => {
    render(Page);
    expect(screen.getByText('Model Playground')).toBeInTheDocument();
  });

  test('renders the Execute button', () => {
    render(Page);
    expect(screen.getByText('Execute')).toBeInTheDocument();
  });

  test('saves code to local storage', async () => {
    render(Page);
    const saveButton = screen.getByText('Save');
    fireEvent.click(saveButton);

    // Check if the code was saved to local storage
    const savedCode = localStorage.getItem('python_code');
    expect(savedCode).not.toBeNull();
    expect(savedCode).toBe(''); // Assuming the initial code is an empty string
  });

  test('loads code from local storage', async () => {
    localStorage.setItem('python_code', 'print("Hello, World!")');  
    render(Page);
    // Wait for the editor to be initialized
    await screen.findByText("Model Playground"); // Ensures the component is fully mounted
    // Get the CodeMirror editor
    const editorElement = document.querySelector('.code-editor');
    // Ensure the editor contains the expected text
    expect(editorElement.textContent).toContain('print("Hello, World!")');
  });

  test('saves non-empty code to local storage', async () => {
    render(Page);
    const codeEditor = document.querySelector('.code-editor .cm-content[role="textbox"]');
    fireEvent.paste(codeEditor, { clipboardData: { getData: () => 'print("Hello, World!")' } });

    const saveButton = screen.getByText('Save');
    fireEvent.click(saveButton);

    // Check if the code was saved to local storage
    const savedCode = localStorage.getItem('python_code');
    expect(savedCode).toBe('print("Hello, World!")');
  });

  test('saves empty code to local storage', async () => {
    render(Page);
    const codeEditor = document.querySelector('.code-editor .cm-content[role="textbox"]');
    fireEvent.input(codeEditor, { target: { textContent: '' } });

    const saveButton = screen.getByText('Save');
    fireEvent.click(saveButton);

    // Check if the code was saved to local storage
    const savedCode = localStorage.getItem('python_code');
    expect(savedCode).toBe('');
  });

  test('executes code and displays output', async () => {
    // Mock fetch using Vitest (so always send hello world)
    vi.stubGlobal('fetch', vi.fn(() =>
      Promise.resolve({
        json: () => Promise.resolve({
          output_html: '', 
          output_non_html: 'Hello, World!',
          message: null
        }),
      })
    ));
    render(Page);
  
    // Simulate entering code in the CodeMirror editor
    const codeEditor = document.querySelector('.code-editor .cm-content[role="textbox"]');
    fireEvent.paste(codeEditor, { clipboardData: { getData: () => 'print("Hello, World!")' } });
  
    // Click the execute button
    const executeButton = screen.getByText('Execute');
    fireEvent.click(executeButton);
  
    // Wait for the output to appear
    const outputElement = await screen.findByText('Hello, World!');
    expect(outputElement).toBeInTheDocument();
  
    // Restore original fetch after test
    vi.restoreAllMocks();
  });

  test('lints code and displays errors', async () => {
    render(Page);
    // Simulate entering code in the CodeMirror editor
    const codeEditor = document.querySelector('.code-editor .cm-content[role="textbox"]');
    
    // Trigger linting by pasting code
    fireEvent.paste(codeEditor, { clipboardData: { getData: () => 'print("Hello, World!")' } });
    
    const lintErrorsElement = await screen.findByText('Example error message (line 1, col 1)');
    expect(lintErrorsElement).toBeInTheDocument();
  });
  
  test('mapSeverity function', () => {
    // Todo: improve the mapping based on the rules https://docs.astral.sh/ruff/rules/
    expect(mapSeverity('E402')).toBe('warning');
    expect(mapSeverity('E001')).toBe('error');
    expect(mapSeverity('W001')).toBe('warning');
    expect(mapSeverity('I001')).toBe('info');
    expect(mapSeverity('unknown')).toBe('info');
  });

  test('parseLintErrors function', () => {
    const lintOutput = `
      /path/to/file.py:1:1: E001 Example error message
      /path/to/file.py:2:5: W001 Example warning message
      /path/to/file.py:3:10: I001 Example info message
    `;
    const editor = {
      state: {
        doc: {
          // Returns the start and end positions of a line given its line number
          line: (lineNum) => ({ 
            from: (lineNum - 1) * 20, // Start position of the line (0-based index)
            to: lineNum * 20          // End position of the line
          }),
          // Returns the line number and start position given a character position
          lineAt: (pos) => ({ 
            number: Math.floor(pos / 20) + 1, // Line number (1-based index)
            from: Math.floor(pos / 20) * 20   // Start position of the line
          })
        }
      }
    };

    const errors = parseLintErrors(lintOutput, editor.state.doc);
    expect(errors).toEqual([
      { from: 0, to: 20, severity: 'error', message: 'Example error message' },
      { from: 24, to: 40, severity: 'warning', message: 'Example warning message' },
      { from: 49, to: 60, severity: 'info', message: 'Example info message' }
    ]);
  });
});