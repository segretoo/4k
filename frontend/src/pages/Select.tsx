import { useMemo, useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { errorMessage, startJob } from '../api/client'
import { Bottom, Btn, C, ErrorNote, Frame, Header, Heading, JUA, Notes, Px } from '../components/wf'
import { useApp } from '../state/AppState'

export default function Select() {
  const nav = useNavigate()
  const { uc1, setUc1 } = useApp()
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const photos = useMemo(
    () => (uc1.upload?.posts ?? []).flatMap((p) => p.photos.map((ph) => ({ ...ph, post: p }))),
    [uc1.upload],
  )
  if (!uc1.upload) return <Navigate to="/uc1/upload" replace />

  const max = uc1.upload.max_select
  const selected = new Set(uc1.selected)

  const toggle = (id: string) => {
    setError(null)
    if (selected.has(id)) return setUc1({ selected: uc1.selected.filter((x) => x !== id) })
    if (selected.size >= max) return setError(`사진은 ${max}장까지 고를 수 있어요. 다른 사진을 먼저 빼 주세요.`)
    setUc1({ selected: [...uc1.selected, id] })
  }

  const start = async () => {
    setBusy(true)
    try {
      const job = await startJob(uc1.upload!.upload_id, uc1.selected)
      setUc1({ jobId: job.job_id, result: null })
      nav('/uc1/analyze')
    } catch (e) {
      setError(errorMessage(e))
      setBusy(false)
    }
  }

  return (
    <Frame>
      <Header title="게시물 건강검진" back="/uc1/upload" step={[2, 3]} />
      <Heading
        lines={['점검할 사진을', '골라 주세요']}
        sub={`게시물 ${uc1.upload.total_posts}개를 찾았어요. 캡션에 단서가 보이는 사진과 최근 사진을 먼저 골라 뒀어요.`}
      />

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
        <span style={{ fontFamily: JUA, fontSize: 18 }}>
          {selected.size} / {max}장 선택
        </span>
        <span style={{ fontSize: 13, color: C.sub }}>추천 먼저 · 최근순</span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
        {photos.map((ph, i) => {
          const on = selected.has(ph.photo_id)
          const hint = ph.post.recommended ? ph.post.hints[0] || '추천' : on ? '최근' : ''
          const thumb = uc1.thumbs[ph.photo_id]
          return (
            <button
              key={ph.photo_id}
              type="button"
              role="checkbox"
              aria-checked={on}
              aria-label={`사진 ${i + 1}, ${on ? '선택됨' : '선택 안 됨'}${hint ? `, 추천 이유 ${hint}` : ''}`}
              onClick={() => toggle(ph.photo_id)}
              style={{
                position: 'relative',
                aspectRatio: '1 / 1',
                padding: 0,
                boxSizing: 'border-box',
                border: `3px solid ${C.ink}`,
                background: on ? C.photo : C.empty,
                opacity: on ? 1 : 0.55,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                overflow: 'hidden',
                cursor: 'pointer',
              }}
            >
              {thumb ? (
                <img src={thumb} alt="" style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover' }} />
              ) : (
                <Px name="photoTile" size={30} />
              )}
              <span
                style={{
                  position: 'absolute',
                  left: 6,
                  top: 6,
                  width: 24,
                  height: 24,
                  boxSizing: 'border-box',
                  border: `2px solid ${C.ink}`,
                  background: on ? C.coral : C.white,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                {on && <Px name="tick" size={14} />}
              </span>
              {hint && on && (
                <span
                  style={{
                    position: 'absolute',
                    left: 6,
                    bottom: 6,
                    maxWidth: 'calc(100% - 12px)',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    padding: '1px 6px',
                    background: C.white,
                    border: `2px solid ${C.ink}`,
                    fontSize: 11,
                    lineHeight: 1.4,
                    color: C.ink,
                  }}
                >
                  {hint}
                </span>
              )}
            </button>
          )
        })}
      </div>

      {error && <ErrorNote>{error}</ErrorNote>}
      <Notes items={[['lock', '고른 사진만 분석하고, 나머지는 바로 지워요']]} />

      <Bottom>
        <Btn onClick={start} disabled={selected.size === 0 || busy}>
          {selected.size === 0 ? '사진을 1장 이상 골라 주세요' : busy ? '시작하는 중...' : `점검 시작 (${selected.size}장)`}
        </Btn>
      </Bottom>
    </Frame>
  )
}
