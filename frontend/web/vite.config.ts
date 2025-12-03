import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    host: '0.0.0.0', // Listen on all interfaces for Docker networking
    proxy: {
      '/api': {
        // Use Docker service name when running in container, localhost otherwise
        target: process.env.VITE_API_PROXY_TARGET || 'http://central_api:8000',
        changeOrigin: true,
      },
    },
  },
});
