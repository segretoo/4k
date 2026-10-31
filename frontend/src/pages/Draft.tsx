import { useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { checkDraft, errorMessage, getStatus } from '../api/client'
import type { Warning } from '../api/types'
import RegionPreview from '../components/RegionPreview'
import { Bottom, Btn, C, ErrorNote, FilePick, Frame, Header, JUA, MeterRow, Notes, Panel, Px } from '../components/wf'
import { CLUE_ICON, TYPE_LABEL } from '../lib/labels'
import { session } from '../lib/session'
import { useApp } from '../state/AppState'

const SEVERITY: Record<Warning['severity'], [string, string, string]> = {
  high: ['높음', C.coral, C.white],
  medium: ['중간', C.peach, C.ink],
  check: ['확인', '#FEF3C7', '#713F12'],
}

export default function Draft() {
  const nav = useNavigate()
  const from = (useLocation().state as { from?: string } | null)?.from
  const { uc2, setUc2, resetUc2 } = useApp()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const prior = session.clues()
  const [mock, setMock] = useState(false)

  useEffect(() => {
    getStatus()
      .then((s) => setMock(s.gpu_mock))
      .catch(() => undefined)
  }, [])

  const pick = (f: File | undefined) => {
    setError(null)
    if (!f) return
    if (!['image/jpeg', 'image/png'].includes(f.type)) return setError('JPG나 PNG 사진만 올릴 수 있어요.')
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

  // ---------- 1) 사진·캡션 입력 ----------
  if (!c || !uc2.previewUrl) {
    return (
      <Frame gap={12}>
        <Header title="올리기 전 진단" back="/" />
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          <h1 style={{ margin: 0, fontFamily: JUA, fontWeight: 400, fontSize: 25, lineHeight: 1.3 }}>
            올리기 전에
            <br />
            한 번 확인해요
          </h1>
          <p style={{ margin: 0, fontSize: 14, lineHeight: 1.6, color: C.sub }}>
            {from
              ? `'${from}' 게시물의 원본 사진을 골라 주세요. 캡션은 채워 뒀어요.`
              : prior.length
                ? '지난 게시물 점검 결과와 이어서 봐요.'
                : '이 사진과 캡션만으로 진단해요.'}
          </p>
        </div>

        {uc2.previewUrl ? (
          <RegionPreview src={uc2.previewUrl} size={[1, 1]} regions={[]} mode="none" caption="고른 사진" />
        ) : (
          <FilePick title="올릴 사진 선택" hint="JPG · PNG" accept="image/jpeg,image/png" onPick={pick}>
            <Px name="photoTile" size={32} />
          </FilePick>
        )}
        {uc2.previewUrl && (
          <FilePick title="다른 사진 고르기" hint={uc2.file?.name ?? ''} accept="image/jpeg,image/png" onPick={pick}>
            <span />
          </FilePick>
        )}

        <label style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          <span style={{ fontSize: 12, color: C.sub }}>쓸 캡션</span>
          <textarea
            value={uc2.caption}
            rows={3}
            maxLength={2200}
            placeholder="예: 오늘도 8시 40분에 등원 완료 #하늘이"
            onChange={(e) => setUc2({ caption: e.target.value })}
            style={{
              boxSizing: 'border-box',
              width: '100%',
              padding: '10px 12px',
              border: `3px solid ${C.ink}`,
              borderRadius: 12,
              background: C.white,
              color: C.ink,
              font: 'inherit',
              fontSize: 14,
              lineHeight: 1.5,
              resize: 'vertical',
            }}
          />
        </label>

        {error && <ErrorNote>{error}</ErrorNote>}
        <Notes items={[['lock', '사진은 진단 후 서버에 남지 않아요']]} />

        <Bottom>
          <Btn onClick={run} disabled={!uc2.file || busy}>
            {busy ? '진단 중...' : uc2.file ? '진단하기' : '사진을 먼저 골라 주세요'}
          </Btn>
        </Bottom>
      </Frame>
    )
  }

  // ---------- 2) 진단 결과 (와이어프레임 Draft) ----------
  const added = c.added.map((t) => TYPE_LABEL[t])
  return (
    <Frame gap={12}>
      <Header title="올리기 전 진단" back="/" />

      <RegionPreview src={uc2.previewUrl} size={c.image_size} regions={c.regions} mode="check" caption={c.regions.length ? '' : '사진에서 단서를 찾지 못했어요'} />

      <Panel style={{ gap: 8, padding: '12px 14px' }}>
        {c.level_now && <MeterRow label="지금" level={c.level_now} labelW={44} valueW={60} />}
        <MeterRow label="올리면" level={c.level_if_posted} labelW={44} valueW={60} blinkTop={c.level_if_posted === 'high' || c.level_if_posted === 'very_high'} />
        <span style={{ fontSize: 13 }}>
          {added.length ? (
            <>
              이 게시물로 <b style={{ fontFamily: JUA, fontWeight: 400 }}>{added.join(', ')}</b>이(가) 더해져요.
            </>
          ) : c.warnings.length ? (
            '새로 더해지는 단서는 없어요.'
          ) : (
            '아이를 특정할 단서가 보이지 않아요.'
          )}
        </span>
      </Panel>

      {mock && c.regions.length === 0 && (
        <div style={{ display: 'flex', gap: 10, alignItems: 'center', padding: '10px 12px', background: '#FEF3C7', border: `3px solid ${C.ink}`, borderRadius: 12, fontSize: 12, lineHeight: 1.5 }}>
          <Px name="bulb" size={20} style={{ flex: 'none' }} />
          <span>
            <b style={{ fontFamily: JUA, fontWeight: 400, fontSize: 14 }}>지금은 가짜 GPU 모드예요.</b> 사진 속 글자는 시연용 사진(uc2_demo.jpg)에서만 찾아요. GPU 서버를 연결하면 어떤 사진이든 읽어요.
          </span>
        </div>
      )}

      <ul style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 8 }}>
        {c.warnings.map((w) => {
          const [sev, bg, fg] = SEVERITY[w.severity]
          return (
            <li
              key={w.type}
              style={{ display: 'flex', flexDirection: 'column', gap: 3, padding: '9px 12px', background: C.white, border: `3px solid ${C.ink}`, borderRadius: 12 }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Px name={w.type === 'unreadable' ? 'bulb' : CLUE_ICON[w.type]} size={18} />
                <span style={{ flex: 1, fontFamily: JUA, fontSize: 15 }}>{w.type === 'unreadable' ? '읽을 수 없는 글자' : `${TYPE_LABEL[w.type]} 노출`}</span>
                <span style={{ padding: '0 7px', background: bg, border: `2px solid ${C.ink}`, color: fg, fontFamily: JUA, fontSize: 12 }}>{sev}</span>
              </div>
              <span style={{ fontSize: 12, lineHeight: 1.5, color: C.sub }}>{w.why}</span>
              <span style={{ fontSize: 13 }}>
                <b style={{ fontFamily: JUA, fontWeight: 400, color: C.coralDark }}>권장</b> {w.action}
              </span>
            </li>
          )
        })}
      </ul>

      <span style={{ fontSize: 11, color: C.sub }}>위험 단계는 단서 조합 규칙으로 계산해요 · 이름+장소 = 위험, +시간 = 매우 위험</span>

      <Bottom>
        {c.warnings.length > 0 ? (
          <Btn onClick={() => nav('/uc2/mask')}>가리고 수정하기</Btn>
        ) : (
          <Btn kind="plain" onClick={resetUc2}>
            다른 사진 진단하기
          </Btn>
        )}
        {c.warnings.length > 0 && (
          <button
            type="button"
            onClick={resetUc2}
            style={{ alignSelf: 'center', padding: 4, border: 0, background: 'none', color: C.sub, fontSize: 12, textDecoration: 'underline', cursor: 'pointer' }}
          >
            다른 사진으로 다시 진단하기
          </button>
        )}
      </Bottom>
    </Frame>
  )
}
