import type { Region } from '../api/types'
import { TYPE_LABEL } from '../lib/labels'

/** 사진 위에 가릴 영역 상자를 그린다. 좌표는 원본 픽셀 기준이라 비율로 바꿔서 표시. */
export default function RegionPreview({
  src,
  size,
  regions,
  activeIds,
}: {
  src: string
  size: [number, number]
  regions: Region[]
  activeIds?: Set<string>
}) {
  const [w, h] = size
  return (
    <div className="preview">
      <img src={src} alt="점검할 사진 미리보기" />
      {regions.map((r) => {
        const [x1, y1, x2, y2] = r.box
        const off = activeIds ? !activeIds.has(r.id) : false
        return (
          <div
            key={r.id}
            className={`region ${r.type === 'unreadable' ? 'unreadable' : ''} ${off ? 'off' : ''}`}
            style={{ left: `${(x1 / w) * 100}%`, top: `${(y1 / h) * 100}%`, width: `${((x2 - x1) / w) * 100}%`, height: `${((y2 - y1) / h) * 100}%` }}
          >
            <span className="region-tag">{r.type === 'unreadable' ? '확인 필요' : TYPE_LABEL[r.type]}</span>
          </div>
        )
      })}
    </div>
  )
}
