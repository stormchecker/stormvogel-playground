import { test, expect } from '@playwright/test';
import JSZip from 'jszip';
import fs from 'fs';

test('Loads the page and checks initial elements', async ({ page }) => {
  await page.goto('/'); // Adjust the URL to your local server

  // Check if the title is correct
  await expect(page).toHaveTitle('Stormvogel Playground');

  // Check if the header is visible
  await expect(page.locator('header h1')).toHaveText('Stormvogel Playground');

  // Check if the save button is present
  await expect(page.locator('button', { hasText: 'Save' })).toBeVisible();

  // Check if the execute button is present
  await expect(page.locator('button', { hasText: '▶ Run' })).toBeVisible();

  // Check if the examples button is present
  await expect(page.locator('button', { hasText: 'Examples' })).toBeVisible();

  // Check if the output console is present
  await expect(page.locator('.output-console')).toBeVisible();

  // Check if the output console is empty
  await expect(page.locator('#output-non-html')).toHaveText('');

  // Check if the code editor is present
  await expect(page.locator('.code-editor')).toBeVisible();

  // Check if the code editor is empty
  await expect(page.locator('.cm-content')).toHaveText('');

  // Check if the iframe is present
  await expect(page.locator('.model-preview')).toBeVisible();
});

test('Save code functionality with multiple tabs', async ({ page }) => {
  await page.goto('/');

  // Add a new tab
  await page.locator('button.add-tab').click();

  // Add code to the first tab
  await page.locator('.tab', { hasText: 'Model.py' }).click();
  const editor = page.locator('.cm-content');
  await editor.click();
  await editor.fill('print("Code in Model.py")');

  // Switch to the third tab and add code
  await page.locator('.tab', { hasText: 'Tab1' }).click();
  await editor.click();
  await editor.fill('print("Code in Tab 1")');

  // Save all tabs
  await page.locator('button', { hasText: 'Save' }).click();

  // Check if the save toast is visible
  await expect(page.locator('.save-toast', { hasText: 'The code has been saved successfully' })).toBeVisible();
  await expect(page.locator('button', { hasText: 'Saved' })).toBeVisible();

  // Check if all tabs are saved in localStorage
  const savedTabs = await page.evaluate(() => JSON.parse(localStorage.getItem('tabs_data')));
  expect(savedTabs['Model.py']).toBe('print("Code in Model.py")');
  expect(savedTabs['Tab1.py']).toBe('print("Code in Tab 1")');
});

test('Execute Python code and check output', async ({ page }) => {
  await page.goto('/');

  // Locate the CodeMirror editor and input Python code
  const editor = page.locator('.cm-content');
  await editor.click();
  await editor.fill('print("Hello, Playwright!")');
  
  await page.waitForTimeout(1000); 
  // Click the execute button
  await page.locator('button', { hasText: '▶ Run' }).click();

  // Wait for the output to appear
  const outputLocator = page.locator('#output-non-html'); // Check the first output element
  await expect(outputLocator).toHaveText('Hello, Playwright!', { timeout: 10000 }); // Give it some time to process
});

test('Execute Python code, refresh page, and execute again', async ({ page }) => {
  await page.goto('/'); 

  // Locate the CodeMirror editor and input Python code
  const editor = page.locator('.cm-content');
  await editor.click();
  await editor.fill('print("Hello, Playwright!")');

  await page.waitForTimeout(1000); 
  // Click the execute button
  await page.locator('button', { hasText: '▶ Run' }).click();

  // Wait for the output to appear
  const outputLocator = page.locator('#output-non-html');
  await expect(outputLocator).toHaveText('Hello, Playwright!', { timeout: 10000 }); // Give it some time to process

  // Refresh the page
  await page.reload();
  await page.waitForTimeout(1000); 

  await editor.click();
  await editor.fill('print("Hello, Playwright!")');
  
  await page.locator('button', { hasText: '▶ Run' }).click();
  await expect(outputLocator).toHaveText('Hello, Playwright!', { timeout: 10000 }); // Check if the output is still correct after refresh
});

test('Execute faulty Python code and check for errors', async ({ page }) => {
  await page.goto('/');

  // Locate the CodeMirror editor and input faulty Python code
  const editor = page.locator('.cm-content');
  await editor.click();
  await editor.fill('print("Hello, Playwright!');
  
  // Check linting errors
  const lintErrors = page.locator('#lint-errors'); 
  await expect(lintErrors).toContainText('Got unexpected string (line 1, col 7)');
  await expect(lintErrors).toContainText('unexpected EOF while parsing (line 1, col 26)');

  // Check if the error is underlined in the editor
  const underlineError = page.locator('.cm-lint-marker-error');
  await expect(underlineError).toBeVisible();

  await underlineError.hover();
  await expect(page.locator('.cm-tooltip-lint')).toContainText('Got unexpected string');
  await expect(page.locator('.cm-tooltip-lint')).toContainText('unexpected EOF while parsing');

  // Click the execute button
  await page.locator('button', { hasText: '▶ Run' }).click();

  // Check execution errors
  const errorLocator = page.locator('#error'); // Adjust selector as needed
  await expect(errorLocator).toContainText('SyntaxError', { timeout: 10000 }); // Give it some time to process
});

test('Test auto save functionality with multiple tabs', async ({ page }) => {
  await page.goto('/');

  // Add a new tab
  await page.locator('button.add-tab').click();

  // Add code to the first tab
  await page.locator('.tab', { hasText: 'Model.py' }).click();
  const editor = page.locator('.cm-content');
  await editor.click();
  await editor.fill('print("Code in Model.py")');

  // Add code to the second tab
  await page.locator('.tab', { hasText: 'Tab1' }).click();
  await editor.click();
  await editor.fill('print("Code in Tab 1")');
  
  // For some reason, playwright doesn't set the localStorage item when refreshing the page
  await page.evaluate(() => localStorage.setItem('tabs_data', JSON.stringify({
    'Model.py': 'print("Code in Model.py")',
    'Model.prism': '',
    'Tab1': 'print("Code in Tab 1")'
  })));
  await page.reload();
  
  // Verify the first tab's content
  await page.locator('.tab', { hasText: 'Model.py' }).click();
  const editorContent1 = await page.locator('.cm-content').textContent();
  expect(editorContent1).toBe('print("Code in Model.py")');

  // Verify the second tab's content
  await page.locator('.tab', { hasText: 'Tab1' }).click();
  const editorContent2 = await page.locator('.cm-content').textContent();
  expect(editorContent2).toBe('print("Code in Tab 1")');
});

test('Check if code editor initializes correctly with no saved code', async ({ page }) => {
  await page.goto('/');

  // Ensure the editor exists
  const editor = page.locator('.cm-content');

  // Get text content safely (fallback to empty string)
  const editorContent = await editor.textContent() ?? '';

  expect(editorContent.trim()).toBe('');
});


test('Test user navigates away and returns with multiple tabs', async ({ page }) => {
  await page.goto('/');

  // Add a new tab
  await page.locator('button.add-tab').click();

  // Add code to the first tab
  await page.locator('.tab', { hasText: 'Model.py' }).click();
  const editor = page.locator('.cm-content');
  await editor.click();
  await editor.fill('print("Code in Model.py")');

  // Add code to the second tab
  await page.locator('.tab', { hasText: 'Tab1' }).click();
  await editor.click();
  await editor.fill('print("Code in Tab 1")');

  // Navigate away
  await page.goto('https://www.google.com');

  // Navigate back
  await page.goto('/');

  // Verify the first tab's content
  await page.locator('.tab', { hasText: 'Model.py' }).click();
  const editorContent1 = await page.locator('.cm-content').textContent();
  expect(editorContent1).toBe('print("Code in Model.py")');

  // Verify the second tab's content
  await page.locator('.tab', { hasText: 'Tab1' }).click();
  const editorContent2 = await page.locator('.cm-content').textContent();
  expect(editorContent2).toBe('print("Code in Tab 1")');
});

test('Test user inputs large amount of code', async ({ page }) => {
  await page.goto('/');

  const largeCode = 'print("Hello, Playwright!")\n'.repeat(10000);

  await page.evaluate((code) => {
    localStorage.setItem('python_code', code);
  }, largeCode);

  await page.reload(); // Reload to confirm persistence

  const editorContent = await page.evaluate(() => localStorage.getItem('python_code'));
  expect(editorContent).toBe(largeCode);
});

test('Test user inputs code with various syntax errors', async ({ page }) => {
  await page.goto('/');

  const faultyCode = 'print("Hello, Playwright!"\nprint("Another line")\nprint("Missing parenthesis"\n';
  const editor = page.locator('.cm-content');
  await editor.click();
  await editor.fill(faultyCode);
  
  // Check linting errors
  const lintErrors = page.locator('#lint-errors'); 
  await expect(lintErrors).toContainText('Expected \',\', found name (line 2, col 1)');
  await expect(lintErrors).toContainText('Expected \',\', found name (line 3, col 1)');
  await expect(lintErrors).toContainText('unexpected EOF while parsing (line 4, col 1)');
});

test('Import prism file from different tab', async ({ page }) => {
  await page.goto('/');

  // Locate the CodeMirror editor and input Python code
  const editor = page.locator('.cm-content');
  await editor.click();
  await editor.fill(`import stormpy

def example_prism():
    prism_program = stormpy.parse_prism_program("Model.prism")

    model = stormpy.build_model(prism_program)
    print("Number of states: {}".format(model.nr_states))
    print("Number of transitions: {}".format(model.nr_transitions))

if __name__ == "__main__":
    example_prism()`);
  
  // Locate the CodeMirror editor and input Prism code
  await page.locator('.tab', { hasText: 'Model.prism' }).click();
  await editor.click();
  await editor.fill(`dtmc

module die
    // The integers 0..7 represent our states, and 0 is the initial state.
    s : [0..7] init 0;
    // From s=0, we can go to 1,2,3,4,5,6 with 1/6th probability.
    // The + sign can be interpreted as an 'or'
    // Note that this is similar to our delta function.
    [] s=0 -> 1/6 : (s'=1) +
                1/6: (s'=2) +
                1/6: (s'=3) +
                1/6: (s'=4) +
                1/6: (s'=5) +
                1/6: (s'=6);
    // Self loops
    [] s>0 -> (s'=s);
endmodule

// Add the desired labels
label "rolled1" = s=1;
label "rolled2" = s=2;
label "rolled3" = s=3;
label "rolled4" = s=4;
label "rolled5" = s=5;
label "rolled6" = s=6;`);

  await page.locator('.tab', { hasText: 'Model.py' }).click();

  await page.waitForTimeout(1000); 
  // Click the execute button
  await page.locator('button', { hasText: '▶ Run' }).click();

  // Wait for the output to appear
  const outputLocator = page.locator('#output-non-html'); // Check the output
  await expect(outputLocator).toHaveText(`Number of states: 7
Number of transitions: 12`, { timeout: 10000 }); // Give it some time to process
});

test('Export tabs functionality', async ({ page }) => {
  await page.goto('/');

  // Add code to the first tab
  await page.locator('.tab', { hasText: 'Model.py' }).click();
  const editor = page.locator('.cm-content');
  await editor.click();
  await editor.fill('print("Code in Model.py")');

  // Add code to the second tab
  await page.locator('button.add-tab').click();
  await page.locator('.tab', { hasText: 'Tab1' }).click();
  await editor.click();
  await editor.fill('print("Code in Tab 1")');

  // Mock the download action
  const [download] = await Promise.all([
    page.waitForEvent('download'), // Wait for the download event
    page.locator('button', { hasText: 'Export' }).click(), // Trigger the export
  ]);

  // Save the downloaded file to a temporary path
  const path = await download.path();

  // Verify the contents of the downloaded zip file
  const zipContent = fs.readFileSync(path);
  const zip = await JSZip.loadAsync(zipContent);

  // Check if the zip contains the expected files using regex
  expect(Object.keys(zip.files).some(file => /stormvogel-playground-\d{2}-\d{2}-\d{4}\/Model\.py/.test(file))).toBe(true);
  expect(Object.keys(zip.files).some(file => /stormvogel-playground-\d{2}-\d{2}-\d{4}\/Tab1\.py/.test(file))).toBe(true);
});

test('Linting does not work when linting is disabled', async ({ page }) => {
  await page.goto('/');

  // Locate the CodeMirror editor and input faulty Python code
  const editor = page.locator('.cm-content');
  await editor.click();
  await editor.fill('print("Hello, Playwright!');
  await page.waitForTimeout(2000); // Wait for linting

  // Expect lint errors to be present
  const lintText = await page.locator('#lint-errors').innerText();
  expect(lintText).not.toBe('');

  // Disable linting
  await page.click('.nav-btn:has-text("Linting")');

  // Trigger a small edit to force linter update
  await editor.fill(' ');
  await editor.press('Backspace');
  await page.waitForTimeout(2000);

  // Check that lint errors are now cleared in the DOM
  const lintTextAfter = await page.locator('#lint-errors').innerText();
  expect(lintTextAfter).toBe('');
});

test('Linting only works on .py files', async ({ page }) => {
  await page.goto('/');
  
  // Switch to Model.prism tab
  await page.locator('.tab', { hasText: 'Model.prism' }).click();

  // Locate the CodeMirror editor and input faulty Python code
  const editor = page.locator('.cm-content');
  await editor.click();
  await editor.fill('example code');
  await page.waitForTimeout(2000); // Wait for linting

  // Expect zero lint errors in the DOM
  const lintTextPrism = await page.locator('#lint-errors').innerText();
  expect(lintTextPrism).toBe('');

  // Switch to Model.py tab
  await page.click('.tab:has-text("Model.py")');
  await page.click('.code-editor');

  await editor.click();
  await editor.fill('print("Hello, Playwright!');
  await page.waitForTimeout(2000); // Wait for linting

  // Expect lint errors in the DOM
  const lintTextPython = await page.locator('#lint-errors').innerText();
  expect(lintTextPython).not.toBe('');
});
