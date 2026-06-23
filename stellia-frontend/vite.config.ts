import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.svg', 'favicon.ico', 'apple-touch-icon.png'],
      manifest: {
        name: 'Stellia',
        short_name: 'Stellia',
        description: 'AI 캐릭터 챗 서비스 — Meet Fate. Beyond Worlds.',
        theme_color: '#090b14',
        background_color: '#090b14',
        display: 'standalone',
        orientation: 'portrait',
        scope: '/',
        start_url: '/',
        icons: [
          {
            src: 'pwa-192x192.png',
            sizes: '192x192',
            type: 'image/png',
          },
          {
            src: 'pwa-512x512.png',
            sizes: '512x512',
            type: 'image/png',
          },
          {
            src: 'pwa-512x512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'any maskable',
          },
        ],
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/suburb-marrow-radial\.ngrok-free\.dev\/characters/,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-characters',
              expiration: {
                maxEntries: 50,
                maxAgeSeconds: 60 * 5,
              },
            },
          },
          {
            urlPattern: /^https:\/\/suburb-marrow-radial\.ngrok-free\.dev\/banners/,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-banners',
              expiration: {
                maxEntries: 10,
                maxAgeSeconds: 60 * 10,
              },
            },
          },
        ],
      },
    }),
  ],
})