// 와이어프레임(Design 아티팩트 v2.1)의 인라인 스타일을 그대로 옮긴 화면 부품.
// 값(크기·테두리·그림자·색)을 바꾸면 와이어프레임과 달라지니, 바꿀 때는 와이어프레임도 같이 고친다.
import type { CSSProperties, ReactNode } from 'react'
import { Link } from 'react-router-dom'
import type { Level } from '../api/types'
import { LEVELS, LEVEL_LABEL } from '../lib/labels'
import { PIXELS, type PixelName } from './pixels'

export const C = {
  bg: '#FFF4EE',
  ink: '#3B2420',
  sub: '#7A5048',
  coral: '#C8483E',
  coralDark: '#9E352D',
  pink: '#F6A5A0',
  peach: '#FFD3B5',
  mint: '#CDEBD9',
  empty: '#F3E3DC',
  photo: '#FFE3D3',
  dash: '#EBCFC4',
  white: '#FFFFFF',
  off: '#EBD9D2',
  offLine: '#B9A39B',
  offText: '#6E5852',
} as const

export const JUA = "'Jua', sans-serif"
export const GOWUN = "'Gowun Dodum', sans-serif"
export const LV_COLOR: Record<Level, string> = { safe: '#CDEBD9', caution: '#F6C945', high: '#F59E6B', very_high: '#C8483E' }
export const LV_TEXT: Record<Level, string> = { safe: C.ink, caution: C.ink, high: C.ink, very_high: C.white }

const row: CSSProperties = { display: 'flex', alignItems: 'center' }
const col: CSSProperties = { display: 'flex', flexDirection: 'column' }

// ---------- 픽셀 아이콘 ----------
export function Px({ name, size, color, label, style }: { name: PixelName; size: number; color?: string; label?: string; style?: CSSProperties }) {
  const { vb, r } = PIXELS[name]
  const h = (size * vb[1]) / vb[0]
  return (
    <svg
      width={size}
      height={h}
      viewBox={`0 0 ${vb[0]} ${vb[1]}`}
      shapeRendering="crispEdges"
      style={style}
      {...(label ? { role: 'img', 'aria-label': label } : { 'aria-hidden': true })}
    >
      {r.map(([x, y, w, hh, fill], i) => (
        <rect key={i} x={x} y={y} width={w} height={hh} fill={color ?? fill} />
      ))}
    </svg>
  )
}

// ---------- 화면 틀 ----------
export function Frame({ children, gap = 16 }: { children: ReactNode; gap?: number }) {
  return (
    <main
      style={{
        ...col,
        width: '100%',
        maxWidth: 390,
        minHeight: '100dvh',
        margin: '0 auto',
        boxSizing: 'border-box',
        padding: '20px 20px 24px',
        background: C.bg,
        color: C.ink,
        gap,
      }}
    >
      {children}
    </main>
  )
}

export function Header({ title, back, step }: { title: string; back?: string; step?: [number, number] }) {
  return (
    <div style={{ ...row, gap: 6, minHeight: 44 }}>
      {back && (
        <Link to={back} aria-label="뒤로" style={{ ...row, justifyContent: 'center', width: 44, height: 44, marginLeft: -10 }}>
          <Px name="back" size={20} />
        </Link>
      )}
      <span style={{ fontFamily: JUA, fontSize: 19 }}>{title}</span>
      {step && (
        <>
          <span style={{ flex: 1 }} />
          <div role="img" aria-label={`${step[1]}단계 중 ${step[0]}단계`} style={{ display: 'flex', gap: 4 }}>
            {Array.from({ length: step[1] }, (_, i) => (
              <span
                key={i}
                style={{ width: 14, height: 14, boxSizing: 'border-box', border: `2px solid ${C.ink}`, background: i < step[0] ? C.coral : C.white }}
              />
            ))}
          </div>
        </>
      )}
    </div>
  )
}

export function Heading({ lines, sub, size = 26, gap = 8 }: { lines: ReactNode[]; sub?: ReactNode; size?: number; gap?: number }) {
  return (
    <div style={{ ...col, gap }}>
      <h1 style={{ margin: 0, fontFamily: JUA, fontWeight: 400, fontSize: size, lineHeight: 1.3 }}>
        {lines.map((l, i) => (
          <span key={i}>
            {i > 0 && <br />}
            {l}
          </span>
        ))}
      </h1>
      {sub && <p style={{ margin: 0, fontSize: 14, lineHeight: 1.6, color: C.sub }}>{sub}</p>}
    </div>
  )
}

/** 그림자 있는 흰 카드 (와이어프레임의 4px 4px 0 그림자) */
export function Panel({ children, style }: { children: ReactNode; style?: CSSProperties }) {
  return (
    <div
      style={{
        ...col,
        gap: 12,
        padding: 16,
        background: C.white,
        border: `3px solid ${C.ink}`,
        borderRadius: 12,
        boxShadow: `4px 4px 0 ${C.ink}`,
        ...style,
      }}
    >
      {children}
    </div>
  )
}

/** 그림자 없는 흰 카드 (목록 항목) */
export const boxStyle: CSSProperties = { background: C.white, border: `3px solid ${C.ink}`, borderRadius: 12 }

// ---------- 버튼 ----------
const btnBase: CSSProperties = {
  ...row,
  justifyContent: 'center',
  width: '100%',
  height: 56,
  boxSizing: 'border-box',
  border: `3px solid ${C.ink}`,
  borderRadius: 14,
  boxShadow: `0 5px 0 ${C.ink}`,
  fontFamily: JUA,
  fontSize: 18,
  cursor: 'pointer',
  textDecoration: 'none',
}
const tone = {
  primary: { background: C.coral, color: C.white },
  light: { background: C.white, color: C.coralDark },
  plain: { background: C.white, color: C.ink },
}
const disabledStyle: CSSProperties = { border: `3px solid ${C.offLine}`, background: C.off, color: C.offText, boxShadow: 'none', cursor: 'not-allowed' }

type BtnProps = {
  children: ReactNode
  kind?: keyof typeof tone
  to?: string
  href?: string
  download?: string
  onClick?: () => void
  disabled?: boolean
  style?: CSSProperties
}

export function Btn({ children, kind = 'primary', to, href, download, onClick, disabled, style }: BtnProps) {
  const s: CSSProperties = { ...btnBase, ...tone[kind], ...(disabled ? disabledStyle : {}), ...style }
  if (to && !disabled) return <Link to={to} style={s}>{children}</Link>
  if (href && !disabled)
    return (
      <a href={href} download={download} target={download ? undefined : '_blank'} rel="noreferrer" style={s}>
        {children}
      </a>
    )
  return (
    <button type="button" onClick={onClick} disabled={disabled} style={s}>
      {children}
    </button>
  )
}

/** 화면 맨 아래 버튼 묶음 (margin-top: auto 로 바닥에 붙음) */
export function Bottom({ children, gap = 8, style, sticky = true }: { children: ReactNode; gap?: number; style?: CSSProperties; sticky?: boolean }) {
  // sticky: 목록이 길어도 버튼이 화면 아래에 붙어 있음 (스크롤 없이 바로 누를 수 있게)
  const stick: CSSProperties = sticky
    ? {
        position: 'sticky',
        bottom: 0,
        zIndex: 5,
        margin: '0 -20px -24px',
        padding: '16px 20px calc(16px + env(safe-area-inset-bottom))',
        background: `linear-gradient(to bottom, rgba(255,244,238,0), ${C.bg} 22%)`,
      }
    : { marginBottom: 5 }
  return <div style={{ ...col, gap, marginTop: 'auto', ...stick, ...style }}>{children}</div>
}

// ---------- 안내 줄 ----------
export function Notes({ items, size = 13 }: { items: [PixelName, ReactNode][]; size?: number }) {
  return (
    <ul style={{ margin: 0, padding: 0, listStyle: 'none', ...col, gap: 8, fontSize: size, color: C.sub }}>
      {items.map(([icon, text], i) => (
        <li key={i} style={{ ...row, gap: 8 }}>
          <Px name={icon} size={16} style={{ flex: 'none' }} />
          <span>{text}</span>
        </li>
      ))}
    </ul>
  )
}

export function ErrorNote({ children }: { children: ReactNode }) {
  return (
    <div role="alert" style={{ ...row, gap: 10, padding: '10px 12px', background: '#FDE8E4', border: `3px solid ${C.coral}`, borderRadius: 12, fontSize: 13, lineHeight: 1.5 }}>
      <Px name="noEntry" size={18} style={{ flex: 'none' }} />
      <span>{children}</span>
    </div>
  )
}

// ---------- 위험 단계 ----------
/** scale: 네 칸을 모두 단계 색으로(결과 카드) / upto: 현재 단계까지만 칠함(비교 줄) */
export function Meter({ level, h = 12, mode = 'upto', blinkTop }: { level: Level; h?: number; mode?: 'scale' | 'upto'; blinkTop?: boolean }) {
  const idx = LEVELS.indexOf(level)
  return (
    <div role="img" aria-label={`위험 단계: ${LEVEL_LABEL[level]}`} style={{ flex: 1, display: 'flex', gap: mode === 'scale' ? 4 : 3 }}>
      {LEVELS.map((lv, i) => (
        <span
          key={lv}
          className={blinkTop && i === idx ? 'blink' : undefined}
          style={{
            flex: 1,
            height: h,
            boxSizing: 'border-box',
            border: `2px solid ${C.ink}`,
            background: mode === 'scale' || i <= idx ? LV_COLOR[lv] : C.empty,
          }}
        />
      ))}
    </div>
  )
}

export function MeterRow({
  label,
  level,
  labelW = 52,
  valueW = 64,
  blinkTop,
}: {
  label: string
  level: Level
  labelW?: number
  valueW?: number
  blinkTop?: boolean
}) {
  return (
    <div style={{ ...row, gap: labelW > 48 ? 10 : 8 }}>
      <span style={{ width: labelW, fontSize: 12, color: C.sub }}>{label}</span>
      <Meter level={level} blinkTop={blinkTop} />
      <span
        className={blinkTop ? 'blink' : undefined}
        style={{ width: valueW, textAlign: 'right', fontFamily: JUA, fontSize: 15, color: level === 'very_high' ? C.coralDark : C.ink }}
      >
        {LEVEL_LABEL[level]}
      </span>
    </div>
  )
}

export function LevelTag({ level, size = 14 }: { level: Level; size?: number }) {
  return (
    <span
      style={{
        flex: 'none',
        padding: '3px 9px',
        background: LV_COLOR[level],
        border: `2px solid ${C.ink}`,
        color: LV_TEXT[level],
        fontFamily: JUA,
        fontSize: size,
      }}
    >
      {LEVEL_LABEL[level]}
    </span>
  )
}

export function Chip({ children, bg = C.peach, size = 12, pad = '1px 7px' }: { children: ReactNode; bg?: string; size?: number; pad?: string }) {
  return (
    <span style={{ padding: pad, border: `2px solid ${C.ink}`, borderRadius: 6, background: bg, fontFamily: JUA, fontSize: size, whiteSpace: 'nowrap' }}>
      {children}
    </span>
  )
}

/** 픽셀 스위치 (가리기 화면) */
export function Toggle({ on, onClick, label }: { on: boolean; onClick: () => void; label: string }) {
  return (
    <button
      type="button"
      aria-pressed={on}
      aria-label={label}
      onClick={onClick}
      style={{
        flex: 'none',
        position: 'relative',
        width: 56,
        height: 32,
        padding: 0,
        border: `3px solid ${C.ink}`,
        borderRadius: 4,
        background: on ? C.coral : C.off,
        cursor: 'pointer',
      }}
    >
      <span
        style={{
          position: 'absolute',
          top: 4,
          left: on ? 28 : 4,
          width: 18,
          height: 18,
          boxSizing: 'border-box',
          border: `2px solid ${C.ink}`,
          background: C.white,
          transition: 'left .12s steps(2, end)',
        }}
      />
    </button>
  )
}

/** 분석 진행 막대 (칸 10개, 다음 칸은 깜빡임) */
export function Cells({ ratio, cells = 10, label }: { ratio: number; cells?: number; label: string }) {
  const filled = Math.min(cells, Math.floor(ratio * cells))
  return (
    <div role="img" aria-label={label} style={{ display: 'flex', gap: 3, padding: 3, border: `3px solid ${C.ink}`, background: C.white }}>
      {Array.from({ length: cells }, (_, i) => {
        const next = i === filled && ratio < 1
        return <span key={i} className={next ? 'blink' : undefined} style={{ flex: 1, height: 12, background: i < filled ? C.coral : next ? C.pink : C.empty }} />
      })}
    </div>
  )
}

/** 파일 고르기 상자 (점선) */
export function FilePick({
  title,
  hint,
  accept,
  disabled,
  onPick,
  children,
}: {
  title: string
  hint: string
  accept: string
  disabled?: boolean
  onPick: (f: File | undefined) => void
  children?: ReactNode
}) {
  return (
    <label
      style={{
        position: 'relative',
        ...col,
        alignItems: 'center',
        gap: 6,
        padding: '18px 16px',
        border: `3px dashed ${C.ink}`,
        borderRadius: 12,
        background: C.white,
        cursor: disabled ? 'not-allowed' : 'pointer',
      }}
    >
      {children ?? <Px name="upload" size={32} />}
      <span style={{ fontFamily: JUA, fontSize: 17, textAlign: 'center', wordBreak: 'break-all' }}>{title}</span>
      <span style={{ fontSize: 12, color: C.sub }}>{hint}</span>
      <input
        type="file"
        accept={accept}
        disabled={disabled}
        onChange={(e) => {
          onPick(e.target.files?.[0])
          e.target.value = ''
        }}
        style={{ position: 'absolute', width: 1, height: 1, opacity: 0 }}
      />
    </label>
  )
}
