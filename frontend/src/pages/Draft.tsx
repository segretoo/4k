import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { checkDraft, errorMessage } from '../api/client'
import RegionPreview from '../components/RegionPreview'
import { Chip, ErrorBox, LevelBadge, Note, Panel, PixelIcon, Screen, Title, TopBar } from '../components/ui'
import { TYPE_LABEL } from '../lib/labels'
import { session } from '../lib/session'
import { useApp } from '../state/AppState'

const SEVERITY = { high: '높음', medium: '중간', check: '확인' } as const

export default function Draft() {
  const nav = useNavigate()
  const { uc2, setUc2, resetUc2 } = useApp()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const prior = session.clues()

  const pick = (f: File | undefined) => {
    setError(null)
    if (!f) return
    if (!f.type.startsWith('image/')) return setError('사진 파일만 올릴 수 있어요.')
    if (uc2.previewUrl) URL.revokeObjectURL(uc2.previewUrl)
    setUc2({ file: f, previewUrl: URL.createObjectURL(f), check: null })
  }

  const run = async () => {
    if (!uc2.file) return
    setBusy(true)
    setError(null)
    try {
      setUc2({ check: await checkDraft(uc2.file, uc2.caption, prior) })
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  const c = uc2.check

  return (
    <Screen>
      <TopBar title="올리기 전 진단" back="/" />

      {!c && (
        <>
          <Title sub={prior.length ? '지난 게시물 점검 결과와 이어서 봐요.' : '이 사진과 캡션만으로 진단해요.'}>{'올리기 전에\n한 번 확인해요'}</Title>
          <label className="dropzone">
            {uc2.previewUrl ? <img src={uc2.previewUrl} alt="고른 사진" style={{ maxHeight: 240 }} /> : <PixelIcon name="upload" size={32} color="var(--coral)" />}
            <strong>{uc2.file ? '다른 사진 고르기' : '올릴 사진 선택'}</strong>
            <input className="sr-only" type="file" accept="image/jpeg,image/png" onChange={(e) => pick(e.target.files?.[0])} />
          </label>
          <label>
            <span className="small">쓸 캡션</span>
            <textarea value={uc2.caption} placeholder="예: 오늘도 8시 40분에 등원 완료 #하늘이" onChange={(e) => setUc2({ caption: e.target.value })} />
          </label>
          {error && <ErrorBox>{error}</ErrorBox>}
          <Note>사진은 진단 후 서버에 남지 않아요</Note>
          <div className="bottom">
            <button type="button" className="btn" disabled={!uc2.file || busy} onClick={run}>
              {busy ? '진단 중...' : '진단하기'}
            </button>
          </div>
        </>
      )}

      {c && uc2.previewUrl && (
        <>
          <RegionPreview src={uc2.previewUrl} size={c.image_size} regions={c.regions} />
          <Panel>
            <div className="big-level">
              {c.level_now && (
                <>
                  지금 <LevelBadge level={c.level_now} /> →
                </>
              )}
              올리면 <LevelBadge level={c.level_if_posted} />
            </div>
            {c.added.length > 0 && <p className="small">이 게시물로 {c.added.map((t) => TYPE_LABEL[t]).join(', ')}이(가) 더해져요.</p>}
          </Panel>

          {c.warnings.length === 0 && <p className="sub">아이를 특정할 단서가 보이지 않아요.</p>}
          {c.warnings.map((w) => (
            <Panel key={w.type} className={`warn-card ${w.severity}`}>
              <div className="warn-head">
                <h2>{TYPE_LABEL[w.type]} 노출</h2>
                <Chip tone={w.severity === 'high' ? 'coral' : 'white'}>{SEVERITY[w.severity]}</Chip>
              </div>
              <p className="sub">{w.why}</p>
              <p style={{ margin: 0, fontSize: 14 }}>
                <strong>권장</strong> {w.action}
              </p>
            </Panel>
          ))}
          <p className="small">위험 단계는 단서 조합 표로 표기해요 · 이름+장소 = 위험, +시간 = 매우 위험</p>

          <div className="bottom">
            {c.warnings.length > 0 && (
              <button type="button" className="btn" onClick={() => nav('/uc2/mask')}>
                가리고 수정하기
              </button>
            )}
            <button type="button" className="btn btn-light" onClick={resetUc2}>
              다른 사진 진단하기
            </button>
          </div>
        </>
      )}
    </Screen>
  )
}
