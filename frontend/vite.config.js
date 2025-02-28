import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import preprocess from 'svelte-preprocess';

export default defineConfig({
  plugins: [
    svelte({
      preprocess: preprocess(),
      compilerOptions: {
        dev: process.env.NODE_ENV !== 'production',
      },
    }),
  ],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './vitest.setup.js', // Point to the setup file
  },
});