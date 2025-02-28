import { render, screen } from '@testing-library/svelte';
import Page from './+page.svelte';

describe('Page Component', () => {
  test('renders the Model Playground title', () => {
    render(Page);
    expect(screen.getByText('Model Playground')).toBeInTheDocument();
  });

  test('renders the Execute button', () => {
    render(Page);
    expect(screen.getByText('Execute')).toBeInTheDocument();
  });
});