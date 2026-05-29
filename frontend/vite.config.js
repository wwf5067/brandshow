import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/img-proxy': {
        target: 'https://img.chinapp.com',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/img-proxy/, ''),
        headers: {
          Referer: 'https://www.chinapp.com/',
        },
      },
    },
  },
})
