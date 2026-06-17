import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    allowedHosts: ["suburb-marrow-radial.ngrok-free.dev"],
    // 또는 전체 허용
    // allowedHosts: "all",
  },
})