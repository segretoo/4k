import { useEffect, useState, type CSSProperties } from 'react'
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

/** 그림 영역(350×390) 배율: 폭이 좁으면 맞추고, 화면이 낮으면 줄여서 첫 화면에 버튼까지 보이게 */
function useHeroScale() {
  const calc = () => {
    const w = Math.min(window.innerWidth, 390) - 40
    const byWidth = Math.min(1, w / 350)
    const byHeight = window.innerHeight < 900 ? 0.72 : 0.85
    return Math.min(byWidth, byHeight)
  }
  const [s, setS] = useState(calc)
  useEffect(() => {
    const on = () => setS(calc())
    window.addEventListener('resize', on)
    return () => window.removeEventListener('resize', on)
  }, [])
  return s
}

export default function Landing() {
  const s = useHeroScale()
  return (
    <main
      style={{
        width: '100%',
        maxWidth: 390,
        minHeight: '100dvh',
        margin: '0 auto',
        boxSizing: 'border-box',
        padding: '18px 20px 24px',
        background: C.bg,
        color: C.ink,
        display: 'flex',
        flexDirection: 'column',
        gap: 16,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <Px name="heart" size={24} />
        <span style={{ fontFamily: JUA, fontSize: 24, color: C.coral }}>{NAME}</span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        <h1 style={{ margin: 0, fontFamily: JUA, fontWeight: 400, fontSize: 30, lineHeight: 1.25 }}>
          꼭꼭 숨어라,
          <br />
          이름표 보일라
        </h1>
        <p style={{ margin: 0, fontSize: 15, lineHeight: 1.65, color: C.sub }}>
          게시물 하나는 안전해 보여도, 모으면 아이의 이름·유치원·동네가 맞춰질 수 있어요.
        </p>
      </div>

      <div style={{ width: 350 * s, height: 390 * s, flex: 'none', alignSelf: 'center' }}>
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

      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        <Btn to="/consent?next=uc1" style={{ height: 'auto', flexDirection: 'column', alignItems: 'flex-start', gap: 4, padding: '14px 20px' }}>
          <span style={{ fontSize: 19 }}>게시물 건강검진</span>
          <span style={{ fontFamily: GOWUN, fontSize: 13 }}>지난 게시물을 한 번에 점검해요 · 내보내기 파일로 한 번만</span>
        </Btn>
        <Btn
          to="/consent?next=uc2"
          kind="plain"
          style={{ height: 'auto', flexDirection: 'column', alignItems: 'flex-start', gap: 4, padding: '14px 20px' }}
        >
          <span style={{ fontSize: 19, color: C.coral }}>올리기 전 체크</span>
          <span style={{ fontFamily: GOWUN, fontSize: 13, color: C.sub }}>새 사진과 캡션을 미리 확인해요</span>
        </Btn>
      </div>

      <ul style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 8, fontSize: 13, color: C.sub }}>
        <li style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <svg {...lineIcon}>
            <rect x="4" y="11" width="16" height="10" rx="2" />
            <path d="M8 11V7a4 4 0 0 1 8 0v4" />
          </svg>
          원본 사진은 서버 밖으로 나가지 않아요
        </li>
        <li style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <svg {...lineIcon}>
            <circle cx="12" cy="8" r="4" />
            <path d="M4 21c0-4 4-6 8-6s8 2 8 6" />
          </svg>
          내 계정 데이터만 분석해요
        </li>
        <li style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <svg {...lineIcon}>
            <path d="M5 12l5 5L20 7" />
          </svg>
          자동으로 지우거나 올리지 않아요
        </li>
      </ul>
      <Link to="/privacy" style={{ fontSize: 12, color: C.sub, textDecoration: 'underline' }}>
        개인정보 처리방침
      </Link>
    </main>
  )
}
