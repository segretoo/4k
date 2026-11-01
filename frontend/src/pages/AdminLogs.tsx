import { useState } from 'react'
import { errorMessage, getAuditEvents } from '../api/client'
import type { AuditEvent } from '../api/types'
import { Btn, C, ErrorNote, Frame, Header, JUA } from '../components/wf'

const EVENT_LABEL: Record<AuditEvent['event'], string> = {
  connected: '연결됨',
  disconnected: '연결 해제됨',
  zip_uploaded: 'ZIP 업로드 완료',
  analysis_completed: '게시물 분석 완료',
  analysis_failed: '게시물 분석 실패',
  photo_checked: '사진 진단 완료',
  mask_checked: '마스킹 재검사 완료',
  download_started: '가린 사진 다운로드 시작',
}

function counts(event: AuditEvent): string {
  return [
    event.posts !== undefined ? `게시물 ${event.posts}` : '',
    event.photos !== undefined ? `사진 ${event.photos}` : '',
    event.detections !== undefined ? `검출 ${event.detections}` : '',
    event.warnings !== undefined ? `경고 ${event.warnings}` : '',
    event.failed !== undefined ? `실패 ${event.failed}` : '',
    event.regions !== undefined ? `영역 ${event.regions}` : '',
    event.residuals !== undefined ? `잔여 ${event.residuals}` : '',
    event.fragments !== undefined ? `조각 ${event.fragments}` : '',
  ].filter(Boolean).join(' · ')
}

export default function AdminLogs() {
  const [token, setToken] = useState('')
  const [events, setEvents] = useState<AuditEvent[]>([])
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const load = async () => {
    setBusy(true)
    setError(null)
    try {
      setEvents(await getAuditEvents(token.trim()))
    } catch (e) {
      setError(errorMessage(e))
      setEvents([])
    } finally {
      setBusy(false)
    }
  }

  return (
    <Frame gap={14}>
      <Header title="서버 운영 로그" back="/" />
      <p style={{ margin: 0, fontSize: 13, lineHeight: 1.6, color: C.sub }}>
        로그에는 연결과 작업 수만 있어요. 사진, 캡션, OCR 문구, 파일명, IP 주소는 기록하지 않습니다.
      </p>
      <label style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: 13 }}>
        운영자 조회 키
        <input
          type="password"
          autoComplete="off"
          value={token}
          onChange={(event) => setToken(event.target.value)}
          placeholder="서버 AUDIT_VIEW_TOKEN"
          style={{ padding: 12, border: `2px solid ${C.ink}`, borderRadius: 8, fontSize: 14 }}
        />
      </label>
      <Btn onClick={load} disabled={busy || !token.trim()}>
        {busy ? '불러오는 중...' : '최근 로그 불러오기'}
      </Btn>
      {error && <ErrorNote>{error}</ErrorNote>}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {events.map((event, index) => (
          <article key={`${event.at}-${event.event}-${index}`} style={{ padding: 12, background: C.white, border: `2px solid ${C.ink}`, borderRadius: 8 }}>
            <div style={{ fontFamily: JUA, fontSize: 15 }}>{EVENT_LABEL[event.event]}</div>
            <time style={{ fontSize: 12, color: C.sub }}>{new Date(event.at).toLocaleString()}</time>
            {counts(event) && <div style={{ marginTop: 4, fontSize: 13 }}>{counts(event)}</div>}
          </article>
        ))}
      </div>
      {!events.length && !error && <p style={{ margin: 0, fontSize: 13, color: C.sub }}>표시할 기록이 없어요.</p>}
    </Frame>
  )
}
