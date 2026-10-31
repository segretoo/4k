import type { Clue } from '../api/types'

// sessionStorage: 탭을 닫으면 사라진다 (동의 화면의 "화면을 닫으면 사라져요"와 일치)
const CONSENT = 'kk.consent'
const CLUES = 'kk.uc1.clues'

function read<T>(key: string, fallback: T): T {
  try {
    const raw = sessionStorage.getItem(key)
    return raw ? (JSON.parse(raw) as T) : fallback
  } catch {
    return fallback
  }
}

function write(key: string, value: unknown): void {
  try {
    sessionStorage.setItem(key, JSON.stringify(value))
  } catch {
    // 저장소를 못 쓰면 이번 화면에서만 기억
  }
}

export const session = {
  hasConsent: () => read<boolean>(CONSENT, false),
  setConsent: () => write(CONSENT, true),
  clues: () => read<Clue[]>(CLUES, []),
  setClues: (clues: Clue[]) => write(CLUES, clues),
}
