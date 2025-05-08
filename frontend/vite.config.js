import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

// https://vite.dev/config/
export default defineConfig({
    plugins: [svelte()],
    server: { //proxy to avoid cross origin, this way relative addresses are proxied to backend so it looks same origin to the backend
        //only relavant for npm run dev, deployment uses nginx as a proxy wich will act like same origin
        proxy: {
            '/api/startup': 'http://localhost:5000',
            '/api/lint': 'http://localhost:5000',
            '/api/execute': 'http://localhost:5000',
            '/api/stop': `http://localhost:5000`
        }
    },
    test: {
        globals: true,
        environment: 'jsdom',
        setupFiles: './vitest.setup.js',
        exclude: ['**/node_modules/**', '**/tests-playwright/**'],
        include: ['**/tests-vitest/**'],
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
