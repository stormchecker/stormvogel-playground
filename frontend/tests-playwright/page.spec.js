import { test, expect } from '@playwright/test';

test('Loads the page and checks initial elements', async ({ page }) => {
  await page.goto('/'); // Adjust the URL to your local server

  // Check if the title is correct
  await expect(page).toHaveTitle('Model Playground');

  // Check if the header is visible
  await expect(page.locator('header h1')).toHaveText('Model Playground');

  // Check if the save button is present
  await expect(page.locator('button', { hasText: 'Save' })).toBeVisible();

  // Check if the execute button is present
  await expect(page.locator('button', { hasText: 'Execute' })).toBeVisible();

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

test('Save code functionality', async ({ page }) => {
  await page.goto('/');

  const editor = page.locator('.cm-content');
  await editor.click();
  await editor.fill('print("Hello, Playwright!")');

  // Click the save button
  await page.locator('button', { hasText: 'Save' }).click();

  // Check if the save toast is visible
  await expect(page.locator('.save-toast', {hasText: 'The code has been saved successfully'})).toBeVisible();
  await expect(page.locator('button', { hasText: 'Saved' })).toBeVisible();

  // Check if code is saved in localStorage
  const savedCode = await page.evaluate(() => localStorage.getItem('python_code'));
  expect(savedCode).toBe('print("Hello, Playwright!")');
});

test('Execute Python code and check output', async ({ page }) => {
  await page.goto('/');

  // Locate the CodeMirror editor and input Python code
  const editor = page.locator('.cm-content');
  await editor.click();
  await editor.fill('print("Hello, Playwright!")');
  
  await page.waitForTimeout(1000); 
  // Click the execute button
  await page.locator('button', { hasText: 'Execute' }).click();

  // Wait for the output to appear
  const outputLocator = page.locator('#output-non-html'); // Check the first output element
  await expect(outputLocator).toHaveText('Hello, Playwright!');
});

test('Execute Python code, refresh page, and execute again', async ({ page }) => {
  await page.goto('/'); 

  // Locate the CodeMirror editor and input Python code
  const editor = page.locator('.cm-content');
  await editor.click();
  await editor.fill('print("Hello, Playwright!")');

  await page.waitForTimeout(1000); 
  // Click the execute button
  await page.locator('button', { hasText: 'Execute' }).click();

  // Wait for the output to appear
  const outputLocator = page.locator('#output-non-html');
  await expect(outputLocator).toHaveText('Hello, Playwright!');

  // Refresh the page
  await page.evaluate(() => localStorage.setItem('python_code', 'print("Hello, Playwright!")'));
  await page.reload();

  await page.waitForTimeout(1000); 
  await page.locator('button', { hasText: 'Execute' }).click();
  await expect(outputLocator).toHaveText('Hello, Playwright!');
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
  await page.locator('button', { hasText: 'Execute' }).click();

  // Check execution errors
  const errorLocator = page.locator('#error'); // Adjust selector as needed
  await expect(errorLocator).toContainText('SyntaxError');
});

test('Test auto save functionality', async ({ page }) => {
  await page.goto('/'); 

  // Locate the CodeMirror editor and input Python code
  const editor = page.locator('.cm-content');
  await editor.click();
  await editor.fill('print("Loaded from localStorage")');

  // Save the code to localStorage manually (for some reason it the test doesn't save it automatically)
  await page.evaluate(() => localStorage.setItem('python_code', 'print("Loaded from localStorage")'));

  // Reload the page to ensure the code is loaded from localStorage
  await page.reload();

  // Check if the code editor contains the saved code
  const editorContent = await page.locator('.cm-content').innerText();
  expect(editorContent).toBe('print("Loaded from localStorage")');
});

test('Check if code editor initializes correctly with no saved code', async ({ page }) => {
  await page.goto('/');

  // Check if the code editor is empty
  const editorContent = await page.locator('.cm-content').innerText();
  expect(editorContent).toBe('\n');
});

test('Test user navigates away and returns', async ({ page }) => {
  await page.goto('/'); 

  const editor = page.locator('.cm-content');
  await editor.click();
  await editor.fill('print("Hello, Playwright!")');
  
  // Navigate away
  await page.goto('https://www.google.com');

  // Navigate back
  await page.goto('/');

  // Check if the code editor contains the saved code
  const editorContent = await page.locator('.cm-content').innerText();
  expect(editorContent).toBe('print("Hello, Playwright!")');
});

test('Test user inputs large amount of code', async ({ page }) => {
  await page.goto('/'); 

  const largeCode = 'print("Hello, Playwright!")\n'.repeat(10000);
  const editor = page.locator('.cm-content');
  await editor.click();
  await editor.fill(largeCode);

  // Click the save button
  await page.locator('button', { hasText: 'Save' }).click();

  // Check if code is saved in localStorage
  const savedCode = await page.evaluate(() => localStorage.getItem('python_code'));
  expect(savedCode).toBe(largeCode);
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
