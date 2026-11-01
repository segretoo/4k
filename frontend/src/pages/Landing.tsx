import { useLayoutEffect, useRef, useState, type CSSProperties } from 'react'
import { Link } from 'react-router-dom'
import { Btn, C, GOWUN, JUA, Px } from '../components/wf'

const NAME = '꼭꼭'

// 와이어프레임 Landing: 픽셀 모서리 분홍 판
const PIXEL_CORNER =
  'polygon(0 12px, 6px 12px, 6px 6px, 12px 6px, 12px 0, calc(100% - 12px) 0, calc(100% - 12px) 6px, calc(100% - 6px) 6px, calc(100% - 6px) 12px, 100% 12px, 100% calc(100% - 12px), calc(100% - 6px) calc(100% - 12px), calc(100% - 6px) calc(100% - 6px), calc(100% - 12px) calc(100% - 6px), calc(100% - 12px) 100%, 12px 100%, 12px calc(100% - 6px), 6px calc(100% - 6px), 6px calc(100% - 12px), 0 calc(100% - 12px))'

// 떠다니는 물음표 칩: [글자, 위치, 애니메이션 지연 클래스]
const FLOATS: [string, CSSProperties, string][] = [
  ['동네 ?', { left: 10, top: 44 }, 'd1'],
  ['유치원 ?', { right: 8, top: 110 }, 'd2'],
  ['이름 ?', { left: 4, top: 214 }, 'd3'],
  ['등원 시간 ?', { right: 12, top: 262 }, 'd4'],
  ['나이 ?', { left: 64, top: 300 }, 'd5'],
]

const CLOUDS: CSSProperties[] = [
  { left: 22, top: 24, width: 36 },
  { left: 13, top: 33, width: 54 },
  { left: 160, top: 42, width: 27 },
  { left: 151, top: 51, width: 45 },
]

const lineIcon = { width: 16, height: 16, viewBox: '0 0 24 24', fill: 'none', stroke: C.sub, strokeWidth: 2, strokeLinecap: 'round', strokeLinejoin: 'round', 'aria-hidden': true } as const

/** 그림 영역(350×390)을 남는 공간에 맞춰 줄인다 → 어떤 폰에서도 첫 화면에 버튼까지 보임 */
function useFitScale() {
  const ref = useRef<HTMLDivElement>(null)
  const [s, setS] = useState(0.7)
  useLayoutEffect(() => {
    const el = ref.current
    if (!el) return
    const fit = () => {
      const { width, height } = el.getBoundingClientRect()
      setS(Math.max(0.5, Math.min(1.1, width / 350, height / 390)))
    }
    fit()
    const ro = new ResizeObserver(fit)
    ro.observe(el)
    return () => ro.disconnect()
  }, [])
  return { ref, s }
}

export default function Landing() {
  const { ref, s } = useFitScale()
  return (
    <main
      style={{
        width: '100%',
        maxWidth: 390,
        height: '100dvh',
        minHeight: 560,
        margin: '0 auto',
        boxSizing: 'border-box',
        padding: '16px 20px calc(16px + env(safe-area-inset-bottom))',
        background: C.bg,
        color: C.ink,
        display: 'flex',
        flexDirection: 'column',
        gap: 12,
      }}
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 4, flex: 'none' }}>
        <h1 style={{ margin: 0, fontFamily: JUA, fontWeight: 400, fontSize: 28, lineHeight: 1.25, display: 'flex', alignItems: 'flex-start', gap: 10 }}>
          <span style={{ flex: 1 }}>
            꼭꼭 숨어라,
            <br />
            이름표 보일라
          </span>
          <Px name="heart" size={26} label={NAME} style={{ flex: 'none', marginTop: 6 }} />
        </h1>
        <p style={{ margin: 0, fontSize: 14, lineHeight: 1.5, color: C.sub }}>한 장은 안전해도, 모으면 아이가 드러나요.</p>
      </div>

      <div ref={ref} style={{ flex: 1, minHeight: 0, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
      <div style={{ width: 350 * s, height: 390 * s, flex: 'none' }}>
      <div style={{ position: 'relative', width: 350, height: 390, transform: `scale(${s})`, transformOrigin: 'top left' }}>
        <div style={{ position: 'absolute', inset: 0, background: C.pink, clipPath: PIXEL_CORNER }} />

        <div
          style={{
            position: 'absolute',
            left: 45,
            top: 24,
            width: 260,
            height: 300,
            background: C.white,
            boxShadow: '6px 6px 0 #D9786F',
            boxSizing: 'border-box',
            padding: '14px 14px 0',
          }}
        >
          <div style={{ position: 'relative', width: 232, height: 210, background: C.photo, overflow: 'hidden' }}>
            {CLOUDS.map((s, i) => (
              <div key={i} style={{ position: 'absolute', height: 9, background: C.white, ...s }} />
            ))}
            <div style={{ position: 'absolute', left: 0, bottom: 0, width: 232, height: 36, background: C.mint }} />
            <div style={{ position: 'absolute', left: 4, bottom: 6 }}>
              <Px name="kidTag" size={108} label="이름표를 단 픽셀 아이 일러스트" />
            </div>
            <div style={{ position: 'absolute', left: 120, bottom: 6 }}>
              <Px name="kidRibbon" size={108} label="리본 모자를 쓴 픽셀 아이 일러스트" />
            </div>
          </div>
          <p style={{ margin: '14px 0 0', textAlign: 'center', fontFamily: JUA, fontSize: 17, color: C.sub }}>오늘도 등원 완료!</p>
        </div>

        {FLOATS.map(([text, pos, d]) => (
          <span
            key={text}
            className={`fl ${d}`}
            style={{
              position: 'absolute',
              ...pos,
              padding: '6px 14px',
              background: C.peach,
              border: `3px solid ${C.ink}`,
              boxShadow: `3px 3px 0 ${C.ink}`,
              fontFamily: JUA,
              fontSize: 17,
            }}
          >
            {text}
          </span>
        ))}

        <span
          style={{
            position: 'absolute',
            right: 22,
            bottom: 14,
            fontFamily: JUA,
            fontSize: 34,
            color: C.white,
            textShadow: `3px 0 0 ${C.ink}, -3px 0 0 ${C.ink}, 0 3px 0 ${C.ink}, 0 -3px 0 ${C.ink}`,
          }}
        >
          {NAME}
        </span>
      </div>
      </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 10, flex: 'none' }}>
        <Btn to="/consent?next=uc1" style={{ height: 'auto', flexDirection: 'column', alignItems: 'flex-start', gap: 2, padding: '11px 18px' }}>
          <span style={{ fontSize: 18 }}>게시물 건강검진</span>
          <span style={{ fontFamily: GOWUN, fontSize: 13 }}>지난 게시물을 한 번에 점검해요</span>
        </Btn>
        <Btn
          to="/consent?next=uc2"
          kind="plain"
          style={{ height: 'auto', flexDirection: 'column', alignItems: 'flex-start', gap: 2, padding: '11px 18px' }}
        >
          <span style={{ fontSize: 18, color: C.coral }}>올리기 전 체크</span>
          <span style={{ fontFamily: GOWUN, fontSize: 13, color: C.sub }}>새 사진과 캡션을 미리 확인해요</span>
        </Btn>
      </div>

      <p style={{ flex: 'none', margin: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6, fontSize: 12, color: C.sub }}>
        <svg {...lineIcon} width={14} height={14}>
          <rect x="4" y="11" width="16" height="10" rx="2" />
          <path d="M8 11V7a4 4 0 0 1 8 0v4" />
        </svg>
        원본은 서버 밖으로 안 나가요 · 자동 게시 없음 ·{' '}
        <Link to="/privacy" style={{ color: C.sub, textDecoration: 'underline' }}>
          처리방침
        </Link>
      </p>
    </main>
  )
}
