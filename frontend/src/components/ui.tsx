import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import type { Level } from '../api/types'
import { LEVELS, LEVEL_LABEL } from '../lib/labels'

// ---------- 픽셀 아이콘 (와이어프레임과 같은 8x8 격자) ----------
const ICONS: Record<string, [number, number, number, number][]> = {
  back: [[4, 0, 2, 1], [3, 1, 2, 1], [2, 2, 2, 1], [1, 3, 2, 1], [2, 4, 2, 1], [3, 5, 2, 1], [4, 6, 2, 1]],
  check: [[7, 1, 1, 1], [6, 2, 2, 1], [1, 3, 1, 1], [5, 3, 2, 1], [1, 4, 2, 1], [4, 4, 2, 1], [2, 5, 3, 1], [3, 6, 1, 1]],
  lock: [[2, 0, 4, 1], [1, 1, 1, 3], [6, 1, 1, 3], [0, 4, 8, 4]],
  upload: [[3, 0, 2, 1], [2, 1, 4, 1], [1, 2, 6, 1], [3, 3, 2, 1], [3, 4, 2, 1], [0, 6, 8, 2]],
  warn: [[3, 0, 2, 1], [2, 1, 4, 2], [1, 3, 6, 2], [0, 5, 8, 2]],
  heart: [[1, 1, 2, 1], [5, 1, 2, 1], [0, 2, 8, 2], [1, 4, 6, 1], [2, 5, 4, 1], [3, 6, 2, 1]],
}

export function PixelIcon({ name, size = 16, color = 'currentColor' }: { name: keyof typeof ICONS; size?: number; color?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 8 8" shapeRendering="crispEdges" aria-hidden="true">
      {ICONS[name].map(([x, y, w, h], i) => (
        <rect key={i} x={x} y={y} width={w} height={h} fill={color} />
      ))}
      {name === 'lock' && <rect x={3} y={5} width={2} height={2} fill="var(--bg)" />}
      {name === 'warn' && <rect x={3.5} y={2} width={1} height={3} fill="var(--bg)" />}
    </svg>
  )
}

// ---------- 화면 틀 ----------
export function Screen({ children }: { children: ReactNode }) {
  return <main className="screen">{children}</main>
}

export function TopBar({ title, back, step }: { title: string; back?: string; step?: [number, number] }) {
  return (
    <header className="topbar">
      {back && (
        <Link to={back} className="icon-btn" aria-label="뒤로">
          <PixelIcon name="back" size={20} />
        </Link>
      )}
      <span className="topbar-title">{title}</span>
      <span className="grow" />
      {step && (
        <div className="steps" role="img" aria-label={`${step[1]}단계 중 ${step[0]}단계`}>
          {Array.from({ length: step[1] }, (_, i) => (
            <span key={i} className={i < step[0] ? 'on' : ''} />
          ))}
        </div>
      )}
    </header>
  )
}

export function Title({ children, sub }: { children: ReactNode; sub?: ReactNode }) {
  return (
    <div className="title-block">
      <h1>{children}</h1>
      {sub && <p className="sub">{sub}</p>}
    </div>
  )
}

export function Panel({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <section className={`panel ${className}`}>{children}</section>
}

export function Chip({ children, tone = 'peach' }: { children: ReactNode; tone?: 'peach' | 'white' | 'coral' }) {
  return <span className={`chip chip-${tone}`}>{children}</span>
}

export function Note({ icon = 'lock', children }: { icon?: keyof typeof ICONS; children: ReactNode }) {
  return (
    <p className="note">
      <PixelIcon name={icon} size={14} />
      <span>{children}</span>
    </p>
  )
}

export function ErrorBox({ children }: { children: ReactNode }) {
  return (
    <p className="error" role="alert">
      <PixelIcon name="warn" size={16} color="var(--coral)" />
      <span>{children}</span>
    </p>
  )
}

export function LevelBadge({ level }: { level: Level }) {
  return <span className={`level-badge lv-${level}`}>{LEVEL_LABEL[level]}</span>
}

/** 안전 → 매우 위험 4칸 막대 */
export function LevelMeter({ level }: { level: Level }) {
  const idx = LEVELS.indexOf(level)
  return (
    <div className="meter" role="img" aria-label={`위험 단계: ${LEVEL_LABEL[level]}`}>
      {LEVELS.map((lv, i) => (
        <div key={lv} className={`meter-cell ${i <= idx ? `lv-${lv}` : ''} ${i === idx ? 'current' : ''}`}>
          <span>{LEVEL_LABEL[lv]}</span>
        </div>
      ))}
    </div>
  )
}

export function ProgressCells({ ratio, cells = 10 }: { ratio: number; cells?: number }) {
  const filled = Math.round(ratio * cells)
  return (
    <div className="cells" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(ratio * 100)}>
      {Array.from({ length: cells }, (_, i) => (
        <span key={i} className={i < filled ? 'on' : i === filled && ratio < 1 ? 'next' : ''} />
      ))}
    </div>
  )
}
