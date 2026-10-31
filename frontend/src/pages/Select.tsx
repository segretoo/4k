import { useMemo, useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { errorMessage, startJob } from '../api/client'
import { Chip, ErrorBox, Note, PixelIcon, Screen, Title, TopBar } from '../components/ui'
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
    if (selected.size >= max) return setError(`사진은 ${max}장까지 고를 수 있어요.`)
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
    <Screen>
      <TopBar title="지난 게시물 점검" back="/uc1/upload" step={[2, 3]} />
      <Title sub={`게시물 ${uc1.upload.total_posts}개를 찾았어요. 캡션에 단서가 보이는 사진과 최근 사진을 먼저 골라 뒀어요.`}>
        {'점검할 사진을\n골라 주세요'}
      </Title>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
        <h2>
          {selected.size} / {max}장 선택
        </h2>
        <span className="small">추천 먼저 · 최근순</span>
      </div>

      <div className="grid">
        {photos.map((ph) => {
          const on = selected.has(ph.photo_id)
          const hint = ph.post.recommended ? ph.post.hints[0] : ''
          return (
            <button
              key={ph.photo_id}
              type="button"
              className={`tile ${on ? 'on' : 'off'}`}
              aria-pressed={on}
              aria-label={`${ph.post.caption || '캡션 없음'}${hint ? `, 추천 이유 ${hint}` : ''}`}
              onClick={() => toggle(ph.photo_id)}
            >
              {uc1.thumbs[ph.photo_id] && <img src={uc1.thumbs[ph.photo_id]} alt="" />}
              <span className="tick">{on && <PixelIcon name="check" size={14} color="#fff" />}</span>
              {hint && <Chip tone="white">{hint}</Chip>}
            </button>
          )
        })}
      </div>

      {error && <ErrorBox>{error}</ErrorBox>}
      <Note>고른 사진만 분석하고, 나머지는 바로 지워요</Note>

      <div className="bottom">
        <button type="button" className="btn" disabled={selected.size === 0 || busy} onClick={start}>
          점검 시작 ({selected.size}장)
        </button>
      </div>
    </Screen>
  )
}
