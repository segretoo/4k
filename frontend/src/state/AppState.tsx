import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react'
import type { CheckResponse, EngineResult, UploadResponse } from '../api/types'

interface Uc1State {
  upload: UploadResponse | null
  thumbs: Record<string, string> // photo_id → 브라우저 메모리의 썸네일 주소 (서버 파일은 분석 후 삭제됨)
  selected: string[]
  jobId: string | null
  result: EngineResult | null
}

interface Uc2State {
  file: File | null
  previewUrl: string | null
  caption: string
  check: CheckResponse | null
}

interface AppState {
  uc1: Uc1State
  setUc1: (patch: Partial<Uc1State>) => void
  resetUc1: () => void
  uc2: Uc2State
  setUc2: (patch: Partial<Uc2State>) => void
  resetUc2: () => void
}

const emptyUc1: Uc1State = { upload: null, thumbs: {}, selected: [], jobId: null, result: null }
const emptyUc2: Uc2State = { file: null, previewUrl: null, caption: '', check: null }

const Ctx = createContext<AppState | null>(null)

export function AppProvider({ children }: { children: ReactNode }) {
  const [uc1, setUc1State] = useState<Uc1State>(emptyUc1)
  const [uc2, setUc2State] = useState<Uc2State>(emptyUc2)

  // 함수는 한 번만 만들어 useEffect 의존성으로 써도 반복 실행되지 않게 한다
  const setUc1 = useCallback((patch: Partial<Uc1State>) => setUc1State((s) => ({ ...s, ...patch })), [])
  const resetUc1 = useCallback(
    () =>
      setUc1State((s) => {
        Object.values(s.thumbs).forEach((u) => URL.revokeObjectURL(u))
        return emptyUc1
      }),
    [],
  )
  const setUc2 = useCallback((patch: Partial<Uc2State>) => setUc2State((s) => ({ ...s, ...patch })), [])
  const resetUc2 = useCallback(
    () =>
      setUc2State((s) => {
        if (s.previewUrl) URL.revokeObjectURL(s.previewUrl)
        return emptyUc2
      }),
    [],
  )

  const value = useMemo<AppState>(
    () => ({ uc1, setUc1, resetUc1, uc2, setUc2, resetUc2 }),
    [uc1, uc2, setUc1, resetUc1, setUc2, resetUc2],
  )
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export function useApp(): AppState {
  const v = useContext(Ctx)
  if (!v) throw new Error('AppProvider 밖에서 useApp을 썼어요')
  return v
}
