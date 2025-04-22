import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

// https://vite.dev/config/
export default defineConfig({
  plugins: [svelte()],
  test: {
		globals: true,
		environment: 'jsdom',
		setupFiles: './vitest.setup.js',
		exclude: ['**/node_modules/**', '**/tests-playwright/**'],
		include: ['**/tests-vitest/**'],
		reporters: process.env.GITHUB_ACTIONS ? ['dot', 'github-actions'] : ['dot'],
		coverage: {
			include: ['src/**/*.{js,svelte}'],
			exclude: ['**/node_modules/**', '**/tests-vitest/**', '**/tests-playwright/**']
		}
	},
  resolve: process.env.VITEST
		? {
				conditions: ['browser']
			}
		: undefined
})
