import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

const backendUrl = process.env.VITE_BACKEND_URL || 'http://127.0.0.1:5000'

// https://vite.dev/config/
export default defineConfig({
    build: {
        target: "esnext"
    },
    plugins: [svelte()],
    server: { // proxy API requests during local development
        proxy: {
            '/api': {
                target: backendUrl,
                changeOrigin: true,
                secure: true
            }
        }
    },
    test: {
        globals: true,
        environment: 'jsdom',
        setupFiles: './vitest.setup.js',
        exclude: ['**/node_modules/**'],
        include: ['**/tests-vitest/**'],
		reporters: process.env.GITHUB_ACTIONS ? ['dot', 'github-actions'] : ['dot'],
        coverage: {
            include: ['src/**/*.{js,svelte}'],
            exclude: ['**/node_modules/**', '**/tests-vitest/**'],
            reportsDirectory: './coverage',
            reportOnFailure: true,

        }
    },
    resolve: process.env.VITEST
    ? {
        conditions: ['browser']
    }
    : undefined
})
