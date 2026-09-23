import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    // Must match backend's SEARCHPROP_CORS_ORIGINS default (http://localhost:5173).
    port: 5173,
  },
});
