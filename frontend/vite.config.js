import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

// https://vite.dev/config/
export default defineConfig({
  plugins: [svelte()],
  test: {
		globals: true,
		environment: 'jsdom',
		setupFiles: './vitest.setup.js'
	},
  resolve: process.env.VITEST
		? {
				conditions: ['browser']
			}
		: undefined
})
