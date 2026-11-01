import { useState } from 'react'
import { Navigate } from 'react-router-dom'
import { errorMessage, maskPhoto, recordDownload } from '../api/client'
import type { MaskResponse, Region } from '../api/types'
import RegionPreview from '../components/RegionPreview'
import { Bottom, Btn, C, ErrorNote, Frame, Header, JUA, Px } from '../components/wf'
import { TYPE_LABEL } from '../lib/labels'
import { applyEdits } from '../lib/caption'
import { useApp } from '../state/AppState'

interface Item {
  id: string
  label: string
  group: 'photo' | 'caption'
}

/** 가린 사진을 기기에 저장 (게시는 사용자가 직접) */
function download(dataUrl: string, regionCount: number) {
  void recordDownload(1, regionCount).catch(() => undefined)
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
    () => new Set([...(c?.regions.filter((r) => r.type !== 'unreadable').map((r) => r.id) ?? []), ...(c?.caption_edits?.map((e) => e.id) ?? [])]),
  )
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [masked, setMasked] = useState<MaskResponse | null>(null)
  const [maskedUrl, setMaskedUrl] = useState<string | null>(null)
  const [retryRegions, setRetryRegions] = useState<Region[]>([])
  const [manualConfirmed, setManualConfirmed] = useState(false)
  const [leakConfirmed, setLeakConfirmed] = useState(false)
  const [copied, setCopied] = useState(false)

  if (!c || !uc2.file || !uc2.previewUrl) return <Navigate to="/uc2" replace />
  const edits = c.caption_edits ?? [] // 옛 백엔드 응답에는 없을 수 있음

  const allRegions = [...c.regions, ...retryRegions]
  const items: Item[] = [
    ...allRegions.map((r) => ({
      id: r.id,
-      label: r.type === 'unreadable' ? '읽기 불확실한 글자' : r.type === 'name' ? `이름표 "${r.text}"` : `${TYPE_LABEL[r.type]} "${r.text}"`,
      group: 'photo' as const,
    })),
    ...edits.map((e) => ({
      id: e.id,
      label: e.text.startsWith('#') ? e.text : `"${e.text}"`,
      group: 'caption' as const,
    })),
  ]

  const chosen = allRegions.filter((r) => on.has(r.id))
  const caption = applyEdits(
    uc2.caption,
    edits.filter((e) => on.has(e.id)).map((e) => e.text),
  )

  const toggle = (id: string) => {
    const next = new Set(on)
    if (next.has(id)) next.delete(id)
    else next.add(id)
    setOn(next)
    setMasked(null) // 고른 곳이 바뀌면 다시 가려야 함
    setMaskedUrl(null)
    setManualConfirmed(false)
    setLeakConfirmed(false)
    setCopied(false)
  }

  const save = async () => {
    setBusy(true)
    setError(null)
    try {
      const res = await maskPhoto(uc2.file!, chosen)
      const composite = await composeFragments(uc2.file!, res.fragments, c.image_size)
      if (res.retry_regions.length) {
        setRetryRegions((current) => {
          const byId = new Map(current.map((region) => [region.id, region]))
          res.retry_regions.forEach((region) => byId.set(region.id, region))
          return [...byId.values()]
        })
        setOn((current) => new Set([...current, ...res.retry_regions.map((region) => region.id)]))
      }
      setMasked(res)
      setMaskedUrl(composite)
      setManualConfirmed(false)
      setLeakConfirmed(false)
      if (res.rescan_passed && !res.requires_review) download(composite, chosen.length)
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
    masked && (masked.leaked.length
      ? leakConfirmed
      : (masked.rescan_passed && !masked.requires_review) || (masked.requires_review && manualConfirmed)),
  )

  return (
    <Frame gap={12}>
      <Header title="가리고 수정하기" back="/uc2" />

      {maskedUrl ? (
        <RegionPreview src={maskedUrl} size={c.image_size} regions={masked?.retry_regions ?? []} mode={masked?.retry_regions.length ? 'check' : 'none'} caption={masked?.retry_regions.length ? '추가 마스킹 위치 · 다시 읽힌 글자' : '가린 사진 · 주변 배경으로 채웠어요'} />
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

      {/* 가릴 곳: 짧은 칩으로 묶어서 목록이 길어지지 않게 */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10, padding: '12px 14px', background: C.white, border: `3px solid ${C.ink}`, borderRadius: 12 }}>
        <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between' }}>
          <span style={{ fontFamily: JUA, fontSize: 16 }}>
            가릴 곳 {on.size} / {items.length}
          </span>
          <button
            type="button"
            onClick={() => {
              setOn(on.size === items.length ? new Set() : new Set(items.map((i) => i.id)))
              setMasked(null)
              setCopied(false)
            }}
            style={{ padding: 4, border: 0, background: 'none', color: C.coral, fontSize: 13, cursor: 'pointer' }}
          >
            {on.size === items.length ? '모두 끄기' : '모두 켜기'}
          </button>
        </div>
        {(['photo', 'caption'] as const).map((g) => {
          const list = items.filter((i) => i.group === g)
          if (!list.length) return null
          return (
            <div key={g} style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              <span style={{ fontSize: 12, color: C.sub }}>{g === 'photo' ? '사진에서 가리기' : '캡션에서 빼기'}</span>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {list.map((it) => {
                  const active = on.has(it.id)
                  return (
                    <button
                      key={it.id}
                      type="button"
                      aria-pressed={active}
                      onClick={() => toggle(it.id)}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 6,
                        minHeight: 36,
                        padding: '4px 12px',
                        border: `2px solid ${C.ink}`,
                        borderRadius: 8,
                        background: active ? C.coral : C.white,
                        color: active ? C.white : C.ink,
                        fontFamily: JUA,
                        fontSize: 14,
                        cursor: 'pointer',
                      }}
                    >
                      {active ? <Px name="tick" size={12} /> : <span style={{ width: 12, height: 12, boxSizing: 'border-box', border: `2px solid ${C.ink}` }} />}
                      {it.label}
                    </button>
                  )
                })}
              </div>
            </div>
          )
        })}
      </div>

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
            <span>{masked.retry_regions.length
              ? `재검사에서 읽힌 문구: ${masked.leaked.join(', ')} · 추가 후보 위치를 자동 선택했어요. 추가로 가리거나 확인 후 이대로 진행할 수 있어요.`
              : `재검사에서 읽힌 문구: ${masked.leaked.join(', ')} · 자동으로 위치를 찾지 못했어요. 확인 후 이대로 진행할 수 있어요.`}</span>
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

      <Bottom sticky>
        {masked ? (
          <Btn kind="plain" onClick={() => download(maskedUrl!)}>
            저장 완료 · 다시 받기
          </Btn>
        ) : masked ? (
          <Btn kind="plain" disabled>
            {masked.leaked.length ? '추가 위치를 직접 확인해 주세요' : '직접 확인 후 체크해 주세요'}
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
