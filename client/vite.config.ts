import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // En développement, le front et l'API partagent la même origine : pas de CORS.
    // 127.0.0.1 plutôt que localhost, que Node peut résoudre en ::1 alors qu'uvicorn écoute en IPv4.
    // API_PROXY_TARGET permet de viser une autre instance de l'API (tests, deuxième terminal).
    proxy: {
      '/api': process.env.API_PROXY_TARGET ?? 'http://127.0.0.1:8000',
    },
  },
})
