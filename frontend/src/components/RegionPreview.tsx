import type { ReactNode } from 'react'
import type { Region } from '../api/types'
import { TYPE_LABEL } from '../lib/labels'
import { C, JUA } from './wf'

/**
 * 와이어프레임 Draft/Mask의 350×200 사진 틀.
 * 상자 좌표는 원본 픽셀 기준이라, 사진을 감싼 상자에 대한 비율(%)로 바꿔서 그린다.
 * mode=check: 단서 상자는 빨간 실선 + 깜빡임, 확인 필요는 노란 점선
 * mode=mask : 켠 상자는 주변 배경처럼 흐리게 덮어서 "가린 뒤" 모습을 미리 보여 줌
 */
export default function RegionPreview({
  src,
  size,
  regions,
  mode,
  activeIds,
  caption,
}: {
  src: string
  size: [number, number]
  regions: Region[]
  mode: 'check' | 'mask' | 'none'
  activeIds?: Set<string>
  caption: ReactNode
}) {
  const [w, h] = size
  return (
    <div
      style={{
        position: 'relative',
        width: '100%',
        height: 200,
        flex: 'none',
        boxSizing: 'border-box',
        border: `3px solid ${C.ink}`,
        background: C.photo,
        overflow: 'hidden',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <div style={{ position: 'relative', display: 'inline-flex', maxWidth: '100%', maxHeight: '100%' }}>
        <img src={src} alt="고른 사진 미리보기" style={{ display: 'block', maxWidth: '100%', maxHeight: 194, objectFit: 'contain' }} />
        {mode !== 'none' &&
          regions.map((r) => {
            const [x1, y1, x2, y2] = r.box
            const unk = r.type === 'unreadable'
            const on = activeIds?.has(r.id) ?? true
            const pos = {
              left: `${(x1 / w) * 100}%`,
              top: `${(y1 / h) * 100}%`,
              width: `${((x2 - x1) / w) * 100}%`,
              height: `${((y2 - y1) / h) * 100}%`,
            }
            if (mode === 'mask') {
              return (
                <div
                  key={r.id}
                  aria-hidden="true"
                  style={{
                    position: 'absolute',
                    ...pos,
                    boxSizing: 'border-box',
                    border: on ? 'none' : unk ? '3px dashed #A16207' : `3px solid ${C.coral}`,
                    background: on ? 'rgba(255,227,211,.55)' : 'transparent',
                    backdropFilter: on ? 'blur(6px)' : undefined,
                    WebkitBackdropFilter: on ? 'blur(6px)' : undefined,
                  }}
                />
              )
            }
            return (
              <div key={r.id} aria-hidden="true">
                <div
                  className={unk ? undefined : 'blink'}
                  style={{ position: 'absolute', ...pos, boxSizing: 'border-box', border: unk ? '3px dashed #A16207' : `3px solid ${C.coral}` }}
                />
                <span
                  style={{
                    position: 'absolute',
                    left: pos.left,
                    ...(unk ? { top: `calc(${((y2 / h) * 100).toFixed(2)}% + 4px)` } : { bottom: `calc(${(100 - (y1 / h) * 100).toFixed(2)}% + 2px)` }),
                    padding: '1px 7px',
                    background: unk ? '#FEF3C7' : C.coral,
                    border: `2px solid ${C.ink}`,
                    color: unk ? '#713F12' : C.white,
                    fontFamily: JUA,
                    fontSize: 12,
                    whiteSpace: 'nowrap',
                  }}
                >
                  {unk ? '확인 필요' : r.type === 'name' ? '이름표' : TYPE_LABEL[r.type]}
                </span>
              </div>
            )
          })}
      </div>
      <span
        style={{
          position: 'absolute',
          left: 10,
          bottom: 8,
          right: 10,
          fontSize: 11,
          color: C.ink,
          textShadow: '0 0 3px #FFF, 0 0 3px #FFF',
        }}
      >
        {caption}
      </span>
    </div>
  )
}
