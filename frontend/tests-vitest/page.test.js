import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
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
    if (url.endsWith('/api/startup')) {
      return Promise.resolve({
        json: () => Promise.resolve({
          status: 'success',
          message: 'Succeeded in launching container'
        }),
      });
    } else if (url.endsWith('/api/lint')) {
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
  test('renders the Stormvogel Playground title', () => {
    render(Page);
    expect(screen.getByText('Stormvogel Playground')).toBeInTheDocument();
  });

  test('renders the Execute button', () => {
    render(Page);
    expect(screen.getByText('▶ Run')).toBeInTheDocument();
  });

  test('loads code from local storage', async () => {
    localStorage.setItem('tabs_data', '{"Model.py":"print(\\"model file\\")","Model.prism":"print(\\"prism file\\")"}');  
    render(Page);
    // Wait for the editor to be initialized
    await screen.findByText("Stormvogel Playground"); // Ensures the component is fully mounted
    // Get the CodeMirror editor
    const editorElement = document.querySelector('.code-editor');
    // Ensure the editor contains the expected text
    expect(editorElement.textContent).toContain('print("model file")');

    // Check if the prism file is also loaded
    fireEvent.click(screen.getByText('Model.prism'));
    expect(editorElement.textContent).toContain('print("prism file")');
  });

  test('saves non-empty code to local storage', async () => {
    render(Page);
    const codeEditor = document.querySelector('.code-editor .cm-content[role="textbox"]');
    fireEvent.input(codeEditor, { target: { textContent: '' } });
    // Delete all of the existing content
    fireEvent.paste(codeEditor, { clipboardData: { getData: () => '' } });
    fireEvent.paste(codeEditor, { clipboardData: { getData: () => 'print("Hello, World!")' } });

    const saveButton = screen.getByText('Save');
    fireEvent.click(saveButton);

    // Check if the code was saved to local storage
    const savedCode = localStorage.getItem('tabs_data');
    expect(savedCode).toBe('{"welcome.py":"print(\\"Hello, World!\\")"}'); // Assuming the initial code is an empty string
  });

  test('saves empty code to local storage', async () => {
    render(Page);
    const codeEditor = document.querySelector('.code-editor .cm-content[role="textbox"]');
    fireEvent.input(codeEditor, { target: { textContent: '' } });
    // Delete all of the existing content
    fireEvent.paste(codeEditor, { clipboardData: { getData: () => '' } });

    const saveButton = screen.getByText('Save');
    fireEvent.click(saveButton);

    // Check if the code was saved to local storage
    const savedCode = localStorage.getItem('tabs_data');
    expect(savedCode).toBe('{"welcome.py":""}');
  });

  test('executes code and displays output', async () => {
    // Mock fetch for this test
    const mockFetch = vi.fn(() =>
      Promise.resolve({
        json: () => Promise.resolve({
          status: 'success',
          output_html: '',
          output_non_html: 'Hello, World!',
          message: null,
        }),
      })
    );
    vi.stubGlobal('fetch', mockFetch);

    render(Page);

    // Simulate entering code in the CodeMirror editor
    const codeEditor = document.querySelector('.code-editor .cm-content[role="textbox"]');
    // Clear existing content and paste new code
    fireEvent.input(codeEditor, { target: { textContent: '' } });
    fireEvent.paste(codeEditor, { clipboardData: { getData: () => 'print("Hello, World!")' } });

    // Click the execute button
    const executeButton = screen.getByText('▶ Run');
    fireEvent.click(executeButton);

    // Wait for the output to appear
    await waitFor(() => {
      expect(screen.getByText('Hello, World!')).toBeInTheDocument();
    });

    // Ensure fetch was called with the correct arguments
    expect(mockFetch).toHaveBeenCalledWith(
      '/api/execute',
      expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: 'print("Hello, World!")' }),
      })
    );

    // Restore the global fetch after the test
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
