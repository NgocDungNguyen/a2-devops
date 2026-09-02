import { fileURLToPath, URL } from 'node:url'

import vue from '@vitejs/plugin-vue'
import { defineConfig, loadEnv } from 'vite'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  // Where `npm run dev` forwards /api and /media. Override with
  // VITE_DEV_API_PROXY if the API is not on the usual port — for example when
  // something else on your machine already has 8000.
  const apiTarget = env.VITE_DEV_API_PROXY || 'http://localhost:8000'

  return {
    plugins: [vue()],

    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url))
      }
    },

    server: {
      port: 5173,
      // Listen on every interface, not just loopback. Without this the dev
      // server is unreachable from outside an EC2 instance even with the
      // security group open.
      host: '0.0.0.0',
      // Proxy the API during development so the browser sees a single origin
      // and CORS never enters the picture. This mirrors the nginx
      // configuration you will write for a real deployment.
      //
      // changeOrigin stays FALSE so the browser's own Host header is passed
      // through untouched. Django builds absolute media URLs from that header
      // (see absolute_media_url in server/apps/core/serializers.py), so
      // rewriting it to the proxy target makes every image_url come back as
      // http://localhost:8000/... — which resolves to the *browser's* machine.
      // On a laptop that is accidentally correct; on EC2 every product image
      // breaks. Same rule as `proxy_set_header Host $host` in nginx.
      proxy: {
        '/api': { target: apiTarget, changeOrigin: false },
        '/media': { target: apiTarget, changeOrigin: false },
        '/static': { target: apiTarget, changeOrigin: false }
      }
    },

    preview: {
      port: 4173,
      host: '0.0.0.0'
    },

    build: {
      outDir: 'dist',
      // Useful when a production bundle misbehaves and you need to read a
      // stack trace. Costs disk space, not runtime performance.
      sourcemap: true
    }
  }
})
