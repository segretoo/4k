import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// 개발 중에는 /api 요청을 로컬 백엔드(FastAPI, 8000번)로 넘긴다.
// 배포 때는 npm run build → dist/를 백엔드가 같은 주소로 제공한다.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: { '/api': 'http://localhost:8000', '/health': 'http://localhost:8000' },
  },
})
