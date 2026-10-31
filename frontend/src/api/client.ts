import axios, { AxiosError } from 'axios'
import type {
  CheckResponse,
  Clue,
  JobCreated,
  JobStatus,
  MaskResponse,
  ServerStatus,
  UploadResponse,
  Region,
} from './types'

// 같은 주소에서 백엔드가 화면을 제공하므로 상대 경로. 개발 중에는 vite.config.ts 프록시가 넘겨 준다.
const http = axios.create({ baseURL: '/' })

// Establish the HttpOnly owner cookie before concurrent API calls can race.
let sessionReady: Promise<void> | undefined
http.interceptors.request.use(async (config) => {
  sessionReady ??= fetch('/api/session', { credentials: 'same-origin', cache: 'no-store' })
    .then((response) => { if (!response.ok) throw new Error('세션을 준비하지 못했어요.') })
    .catch((error: unknown) => { sessionReady = undefined; throw error })
  await sessionReady
  return config
})

/** 서버가 준 한국어 메시지(detail)를 꺼낸다. */
export function errorMessage(e: unknown): string {
  if (e instanceof AxiosError) {
    const detail = (e.response?.data as { detail?: unknown } | undefined)?.detail
    if (typeof detail === 'string') return detail
    if (e.response?.status === 413) return '파일이 너무 커요.'
    if (!e.response) return '서버에 연결하지 못했어요. 잠시 후 다시 시도해 주세요.'
  }
  return '문제가 생겼어요. 잠시 후 다시 시도해 주세요.'
}

export async function getStatus(): Promise<ServerStatus> {
  return (await http.get<ServerStatus>('/api/status')).data
}

export async function uploadExport(file: File, onProgress: (ratio: number) => void): Promise<UploadResponse> {
  const form = new FormData()
  form.append('file', file)
  const res = await http.post<UploadResponse>('/api/uc1/uploads', form, {
    onUploadProgress: (ev) => ev.total && onProgress(ev.loaded / ev.total),
  })
  return res.data
}

export async function fetchThumb(url: string): Promise<string> {
  const res = await http.get<Blob>(url, { responseType: 'blob' })
  return URL.createObjectURL(res.data)
}

export async function cancelUpload(uploadId: string): Promise<void> {
  await http.delete(`/api/uc1/uploads/${uploadId}`).catch(() => undefined)
}

export async function startJob(uploadId: string, photoIds: string[]): Promise<JobCreated> {
  return (await http.post<JobCreated>('/api/uc1/jobs', { upload_id: uploadId, photo_ids: photoIds })).data
}

export async function getJob(jobId: string): Promise<JobStatus> {
  return (await http.get<JobStatus>(`/api/uc1/jobs/${jobId}`)).data
}

export async function checkDraft(file: File, caption: string, priorClues: Clue[]): Promise<CheckResponse> {
  const form = new FormData()
  form.append('file', file)
  form.append('meta', JSON.stringify({ caption, prior_clues: priorClues }))
  return (await http.post<CheckResponse>('/api/uc2/check', form)).data
}

export async function maskPhoto(file: File, regions: Region[]): Promise<MaskResponse> {
  const form = new FormData()
  form.append('file', file)
  form.append('meta', JSON.stringify({ regions }))
  return (await http.post<MaskResponse>('/api/uc2/mask', form)).data
}
