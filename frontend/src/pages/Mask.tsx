import { useState } from 'react'
import { Navigate } from 'react-router-dom'
import { errorMessage, maskPhoto } from '../api/client'
import type { MaskResponse } from '../api/types'
import RegionPreview from '../components/RegionPreview'
import { ErrorBox, Note, Panel, PixelIcon, Screen, Title, TopBar } from '../components/ui'
import { TYPE_LABEL } from '../lib/labels'
import { useApp } from '../state/AppState'

export default function Mask() {
  const { uc2 } = useApp()
  const c = uc2.check
  // 확실한 단서는 기본으로 켜고, 확인 필요(읽기 불확실)는 꺼 둔다
  const [active, setActive] = useState<Set<string>>(() => new Set(c?.regions.filter((r) => r.type !== 'unreadable').map((r) => r.id)))
  const [useSuggestion, setUseSuggestion] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [masked, setMasked] = useState<MaskResponse | null>(null)
  const [copied, setCopied] = useState(false)

  if (!c || !uc2.file || !uc2.previewUrl) return <Navigate to="/uc2" replace />

  const caption = useSuggestion ? c.caption_suggestion : uc2.caption
  const chosen = c.regions.filter((r) => active.has(r.id))

  const toggle = (id: string) => {
    const next = new Set(active)
    if (next.has(id)) next.delete(id)
    else next.add(id)
    setActive(next)
    setMasked(null)
  }

  const apply = async () => {
    setBusy(true)
    setError(null)
    try {
      setMasked(await maskPhoto(uc2.file!, chosen.map((r) => r.box), chosen.map((r) => r.text)))
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(caption)
      setCopied(true)
    } catch {
      setCopied(false)
    }
  }

  const dataUrl = masked ? `data:image/jpeg;base64,${masked.image_base64}` : null

  return (
    <Screen>
      <TopBar title="가리고 수정하기" back="/uc2" />
      <Title sub="주변 배경으로 자연스럽게 채워요. 사진은 우리 서버 밖으로 나가지 않아요.">{'가릴 곳을\n골라 주세요'}</Title>

      {dataUrl ? (
        <div className="preview">
          <img src={dataUrl} alt="가린 사진 미리보기" />
        </div>
      ) : (
        <RegionPreview src={uc2.previewUrl} size={c.image_size} regions={c.regions} activeIds={active} />
      )}

      <Panel>
        {c.regions.map((r) => (
          <label key={r.id} className="toggle">
            <input type="checkbox" checked={active.has(r.id)} onChange={() => toggle(r.id)} />
            <span className="t">
              <strong>
                {r.type === 'unreadable' ? '읽을 수 없는 글자' : `${TYPE_LABEL[r.type]} "${r.text}"`} 가리기
              </strong>
              <span className="small">사진 · {r.type === 'unreadable' ? '확인 필요' : `${TYPE_LABEL[r.type]} 단서`}</span>
            </span>
          </label>
        ))}
        {c.caption_suggestion !== uc2.caption && (
          <label className="toggle">
            <input type="checkbox" checked={useSuggestion} onChange={(e) => setUseSuggestion(e.target.checked)} />
            <span className="t">
              <strong>캡션에서 단서 빼기</strong>
              <span className="small">캡션 · 시간·이름 해시태그 등</span>
            </span>
          </label>
        )}
      </Panel>

      <Panel>
        <span className="small">수정한 캡션</span>
        <p style={{ margin: 0 }}>{caption || '(캡션 없음)'}</p>
        <button type="button" className="btn btn-light btn-small" onClick={copy}>
          {copied ? '복사했어요' : '복사'}
        </button>
      </Panel>

      {masked && (
        <Panel>
          <strong>{masked.rescan_passed ? '재검사 통과' : '재검사에서 글자가 다시 읽혔어요'}</strong>
          {masked.rescan_passed ? (
            <Note icon="check">가린 사진을 다시 읽어 봤어요. 가린 글자가 읽히지 않아요.</Note>
          ) : (
            <ErrorBox>다시 읽힌 글자: {masked.leaked.join(', ')} · 영역을 넓혀 다시 가려 주세요.</ErrorBox>
          )}
          {masked.meta_clean && <Note icon="check">사진 속 위치 정보(GPS)도 함께 지웠어요.</Note>}
        </Panel>
      )}
      {error && <ErrorBox>{error}</ErrorBox>}

      <div className="bottom">
        {!masked ? (
          <button type="button" className="btn" disabled={busy || chosen.length === 0} onClick={apply}>
            {busy ? '가리는 중...' : chosen.length ? `${chosen.length}곳 가리기` : '가릴 곳을 골라 주세요'}
          </button>
        ) : (
          <a className="btn" href={dataUrl!} download="kkokkok_masked.jpg">
            <PixelIcon name="upload" /> 가린 사진 저장하기
          </a>
        )}
        <Note icon="warn">게시는 직접 해 주세요. 앱이 대신 올리지 않아요.</Note>
      </div>
    </Screen>
  )
}
