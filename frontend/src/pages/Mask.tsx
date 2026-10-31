import { useState } from 'react'
import { Navigate } from 'react-router-dom'
import { errorMessage, maskPhoto } from '../api/client'
import type { MaskResponse } from '../api/types'
import RegionPreview from '../components/RegionPreview'
import { Bottom, Btn, C, ErrorNote, Frame, Header, JUA, Toggle } from '../components/wf'
import { TYPE_LABEL } from '../lib/labels'
import { applyEdits } from '../lib/caption'
import { useApp } from '../state/AppState'

interface Item {
  id: string
  label: string
  sub: string
}

/** 가린 사진을 기기에 저장 (게시는 사용자가 직접) */
function download(dataUrl: string) {
  const a = document.createElement('a')
  a.href = dataUrl
  a.download = 'kkokkok_masked.jpg'
  a.click()
}

export default function Mask() {
  const { uc2 } = useApp()
  const c = uc2.check
  // 확실한 단서와 캡션 조각은 켜 두고, 확인 필요(판독 불확실)는 꺼 둔다 — 와이어프레임 기본값과 같음
  const [on, setOn] = useState<Set<string>>(
    () => new Set([...(c?.regions.filter((r) => r.type !== 'unreadable').map((r) => r.id) ?? []), ...(c?.caption_edits.map((e) => e.id) ?? [])]),
  )
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [masked, setMasked] = useState<MaskResponse | null>(null)
  const [copied, setCopied] = useState(false)

  if (!c || !uc2.file || !uc2.previewUrl) return <Navigate to="/uc2" replace />

  const items: Item[] = [
    ...c.regions.map((r) => ({
      id: r.id,
      label: r.type === 'unreadable' ? '읽을 수 없는 글자 가리기' : r.type === 'name' ? `이름표 "${r.text}" 가리기` : `${TYPE_LABEL[r.type]} "${r.text}" 가리기`,
      sub: r.type === 'unreadable' ? '사진 · 확인 필요' : `사진 · ${TYPE_LABEL[r.type]} 단서`,
    })),
    ...c.caption_edits.map((e) => ({
      id: e.id,
      label: e.text.startsWith('#') ? `${e.text} 빼기` : `"${e.text}" 빼기`,
      sub: `캡션 · ${TYPE_LABEL[e.type]} 단서`,
    })),
  ]

  const chosen = c.regions.filter((r) => on.has(r.id))
  const caption = applyEdits(
    uc2.caption,
    c.caption_edits.filter((e) => on.has(e.id)).map((e) => e.text),
  )

  const toggle = (id: string) => {
    const next = new Set(on)
    if (next.has(id)) next.delete(id)
    else next.add(id)
    setOn(next)
    setMasked(null) // 고른 곳이 바뀌면 다시 가려야 함
    setCopied(false)
  }

  const save = async () => {
    setBusy(true)
    setError(null)
    try {
      const res = await maskPhoto(uc2.file!, chosen.map((r) => r.box), chosen.map((r) => r.text))
      setMasked(res)
      download(`data:image/jpeg;base64,${res.image_base64}`)
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
      setError('복사하지 못했어요. 캡션을 길게 눌러 직접 복사해 주세요.')
    }
  }

  const maskedUrl = masked ? `data:image/jpeg;base64,${masked.image_base64}` : null

  return (
    <Frame gap={12}>
      <Header title="가리고 수정하기" back="/uc2" />

      {maskedUrl ? (
        <RegionPreview src={maskedUrl} size={c.image_size} regions={[]} mode="none" caption="가린 사진 · 주변 배경으로 채웠어요" />
      ) : (
        <RegionPreview
          src={uc2.previewUrl}
          size={c.image_size}
          regions={c.regions}
          mode="mask"
          activeIds={on}
          caption="미리보기 · 주변 배경으로 자연스럽게 채워요 (서버 밖으로 안 나가요)"
        />
      )}

      <ul style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 8 }}>
        {items.map((it) => (
          <li
            key={it.id}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 12,
              padding: '7px 12px',
              background: C.white,
              border: `3px solid ${C.ink}`,
              borderRadius: 12,
            }}
          >
            <div style={{ display: 'flex', flexDirection: 'column', gap: 1, minWidth: 0 }}>
              <span style={{ fontFamily: JUA, fontSize: 15 }}>{it.label}</span>
              <span style={{ fontSize: 12, color: C.sub }}>{it.sub}</span>
            </div>
            <Toggle on={on.has(it.id)} onClick={() => toggle(it.id)} label={it.label} />
          </li>
        ))}
      </ul>

      <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 12px', background: C.white, border: `3px solid ${C.ink}`, borderRadius: 12 }}>
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', fontSize: 14, lineHeight: 1.5, minWidth: 0 }}>
          <span style={{ fontSize: 12, color: C.sub }}>수정한 캡션</span>
          <span style={{ wordBreak: 'break-all' }}>{caption || '(캡션 없음)'}</span>
        </div>
        <button
          type="button"
          onClick={copy}
          disabled={!caption}
          style={{
            flex: 'none',
            height: 36,
            padding: '0 12px',
            border: `2px solid ${C.ink}`,
            borderRadius: 8,
            background: copied ? C.mint : C.peach,
            color: C.ink,
            fontFamily: JUA,
            fontSize: 14,
            cursor: 'pointer',
          }}
        >
          {copied ? '복사됨' : '복사'}
        </button>
      </div>

      {masked && (
        <div
          role="status"
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 4,
            padding: '10px 12px',
            background: masked.rescan_passed ? '#E5F4EC' : '#FDE8E4',
            border: `3px solid ${C.ink}`,
            borderRadius: 12,
            fontSize: 13,
          }}
        >
          <span style={{ fontFamily: JUA, fontSize: 15 }}>{masked.rescan_passed ? '재검사 통과' : '재검사에서 글자가 다시 읽혔어요'}</span>
          {masked.rescan_passed ? (
            <span>✓ 가린 사진을 다시 읽어 봤어요. 가린 글자가 읽히지 않아요.</span>
          ) : (
            <span>다시 읽힌 글자: {masked.leaked.join(', ')} · 가릴 곳을 더 켜고 다시 저장해 주세요.</span>
          )}
          {masked.meta_clean && <span>✓ 사진 속 위치 정보(GPS)도 함께 지웠어요.</span>}
        </div>
      )}
      {error && <ErrorNote>{error}</ErrorNote>}

      <Bottom>
        {masked ? (
          <Btn kind="plain" onClick={() => download(maskedUrl!)}>
            저장 완료 · 다시 받기
          </Btn>
        ) : (
          <Btn onClick={save} disabled={busy || chosen.length === 0}>
            {busy ? '가리는 중...' : chosen.length ? '가린 사진 저장하기' : c.regions.length ? '가릴 곳을 켜 주세요' : '사진에는 가릴 곳이 없어요'}
          </Btn>
        )}
        <span style={{ fontSize: 12, color: C.sub, textAlign: 'center' }}>게시는 직접 해 주세요. 앱이 대신 올리지 않아요.</span>
      </Bottom>
    </Frame>
  )
}
