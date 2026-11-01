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

function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const image = new Image()
    image.onload = () => resolve(image)
    image.onerror = () => reject(new Error('사진 조각을 불러오지 못했어요.'))
    image.src = src
  })
}

/** 서버가 돌려준 작은 조각만 원본에 합성한다. 좌표는 검사 시 서버가 돌려준 크기 기준이다. */
async function composeFragments(
  file: File,
  fragments: MaskResponse['fragments'],
  checkedSize: [number, number],
): Promise<string> {
  if (fragments.length === 0) throw new Error('서버에서 마스킹 조각을 받지 못했어요.')
  const originalUrl = URL.createObjectURL(file)
  try {
    const original = await loadImage(originalUrl)
    const canvas = document.createElement('canvas')
    canvas.width = original.naturalWidth
    canvas.height = original.naturalHeight
    const ctx = canvas.getContext('2d')
    if (!ctx) throw new Error('사진을 합성할 수 없어요.')
    ctx.drawImage(original, 0, 0)

    const sx = canvas.width / checkedSize[0]
    const sy = canvas.height / checkedSize[1]
    for (const fragment of fragments) {
      const patchUrl = `data:${fragment.media_type};base64,${fragment.patch_base64}`
      const alphaUrl = `data:image/png;base64,${fragment.alpha_base64}`
      const [left, top, right, bottom] = fragment.crop_box_original_pixels
      const dx = Math.round(left * sx)
      const dy = Math.round(top * sy)
      const dw = Math.max(1, Math.round((right - left) * sx))
      const dh = Math.max(1, Math.round((bottom - top) * sy))
      const [patch, alpha] = await Promise.all([loadImage(patchUrl), loadImage(alphaUrl)])
      const piece = document.createElement('canvas')
      piece.width = dw
      piece.height = dh
      const pieceCtx = piece.getContext('2d')
      if (!pieceCtx) throw new Error('마스킹 조각을 합성할 수 없어요.')
      // alpha_base64 is a grayscale PNG, not a PNG with an alpha channel.
      // Turn its luminance into opacity before applying it to the colour layer.
      pieceCtx.drawImage(alpha, 0, 0, dw, dh)
      const opacity = pieceCtx.getImageData(0, 0, dw, dh)
      for (let index = 0; index < opacity.data.length; index += 4) {
        opacity.data[index + 3] = opacity.data[index]
      }
      pieceCtx.putImageData(opacity, 0, 0)
      pieceCtx.globalCompositeOperation = 'source-in'
      pieceCtx.drawImage(patch, 0, 0, dw, dh)
      ctx.drawImage(piece, dx, dy)
    }
    return canvas.toDataURL('image/jpeg', 0.94)
  } finally {
    URL.revokeObjectURL(originalUrl)
  }
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
  const [maskedUrl, setMaskedUrl] = useState<string | null>(null)
  const [manualConfirmed, setManualConfirmed] = useState(false)
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
    setMaskedUrl(null)
    setManualConfirmed(false)
    setCopied(false)
  }

  const save = async () => {
    setBusy(true)
    setError(null)
    try {
      const res = await maskPhoto(uc2.file!, chosen)
      const composite = await composeFragments(uc2.file!, res.fragments, c.image_size)
      setMasked(res)
      setMaskedUrl(composite)
      setManualConfirmed(false)
      if (res.rescan_passed && !res.requires_review) download(composite)
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

  const canDownload = Boolean(
    masked && masked.leaked.length === 0 &&
      ((masked.rescan_passed && !masked.requires_review) || (masked.requires_review && manualConfirmed)),
  )

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
          caption="미리보기 · 선택한 단서만 주변 배경색으로 가려요"
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
            background: canDownload ? '#E5F4EC' : '#FDE8E4',
            border: `3px solid ${C.ink}`,
            borderRadius: 12,
            fontSize: 13,
          }}
        >
          <span style={{ fontFamily: JUA, fontSize: 15 }}>{masked.leaked.length ? '재검사에서 글자가 다시 읽혔어요' : masked.requires_review ? '자동 확인이 어려운 위치가 있어요' : '재검사 통과'}</span>
          {masked.leaked.length ? (
            <span>다시 읽힌 글자: {masked.leaked.join(', ')} · 영역을 바꿔 다시 검사해 주세요.</span>
          ) : masked.requires_review ? (
            <label style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
              <input type="checkbox" checked={manualConfirmed} onChange={(event) => setManualConfirmed(event.target.checked)} />
              <span>사진에서 선택한 위치를 직접 확인했고, 이 상태로 저장하겠습니다.</span>
            </label>
          ) : masked.rescan_passed ? (
            <span>✓ 가린 사진을 다시 읽어 봤어요. 가린 글자가 읽히지 않아요.</span>
          ) : (
            <span>읽을 글자가 확인되지 않아 자동으로 통과를 확인할 수 없어요.</span>
          )}
          {masked.meta_clean && <span>✓ 사진 속 위치 정보(GPS)도 함께 지웠어요.</span>}
        </div>
      )}
      {error && <ErrorNote>{error}</ErrorNote>}

      <Bottom>
        {canDownload ? (
          <Btn kind="plain" onClick={() => maskedUrl && download(maskedUrl)}>
            저장 완료 · 다시 받기
          </Btn>
        ) : masked ? (
          <Btn kind="plain" disabled>
            {masked.leaked.length ? '영역을 바꿔 다시 검사해 주세요' : '직접 확인 후 체크해 주세요'}
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
