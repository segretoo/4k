import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
// 글꼴을 앱에 같이 넣어 외부(Google Fonts) 요청 없이 쓴다 — 접속 기록이 밖으로 나가지 않게
import '@fontsource/jua/400.css'
import '@fontsource/gowun-dodum/400.css'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
