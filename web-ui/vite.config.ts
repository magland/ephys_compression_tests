import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: '/ephys_compression_tests/', // Base URL for GitHub Pages deployment
  define: {
    __BUILD_DATE__: JSON.stringify(new Date().toLocaleDateString())
  }
})
