import { fileURLToPath, URL } from 'node:url';
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    // Listen on localhost ONLY — the dev server is not reachable from the LAN
    // (phone/other devices). Set host: true to re-expose it on the network.
    host: '127.0.0.1',
    port: 5173,
    proxy: {
      // Forward API calls to the backend so the browser stays same-origin.
      '/api': { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
});
