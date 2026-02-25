import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import { defineConfig } from 'vite'

// GitHub Pages deploys under /<repo-name>/
// Set VITE_BASE_URL env var to override, or it defaults to '/' for local dev
// For GitHub Pages: VITE_BASE_URL=/computacional-vision/
export default defineConfig(({ mode }) => {
  const isGitHubPages = process.env.GITHUB_PAGES === 'true'
  const base =
    process.env.VITE_BASE_URL ||
    (isGitHubPages ? '/computacional-vision/' : '/')

  return {
    base,
    plugins: [vue()],
    resolve: {
      alias: {
        '@': resolve(__dirname, 'src')
      }
    },
    define: {
      // Expose to client code so the app knows if it's running on GH Pages
      __APP_MODE__: JSON.stringify(
        isGitHubPages
          ? 'demo'
          : mode === 'production'
            ? 'production'
            : 'development'
      ),
      __APP_BASE__: JSON.stringify(base)
    },
    server: {
      port: 3000,
      proxy: {
        '/api/ws': {
          target: 'ws://localhost:8000',
          ws: true,
          changeOrigin: true
        },
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true
        },
        '/files': {
          target: 'http://localhost:8000',
          changeOrigin: true
        },
        '/health': {
          target: 'http://localhost:8000',
          changeOrigin: true
        }
      }
    },
    build: {
      outDir: 'dist',
      assetsDir: 'assets',
      sourcemap: false,
      rollupOptions: {
        output: {
          manualChunks: {
            'vue-vendor': ['vue', 'vue-router'],
            'chart-vendor': ['chart.js', 'vue-chartjs'],
            'axios-vendor': ['axios']
          }
        }
      }
    }
  }
})
