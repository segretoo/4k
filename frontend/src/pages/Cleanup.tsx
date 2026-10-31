import { Link, Navigate } from 'react-router-dom'
import { Chip, LevelBadge, Note, Panel, Screen, Title, TopBar } from '../components/ui'
import { TYPE_LABEL, formatDate } from '../lib/labels'
import { useApp } from '../state/AppState'

export default function Cleanup() {
  const { uc1 } = useApp()
  const r = uc1.result
  if (!r || !r.level_after_cleanup) return <Navigate to="/uc1/result" replace />

  return (
    <Screen>
      <TopBar title="지난 게시물 점검" back="/uc1/result" />
      <Title sub="위험한 조합을 끊는 게시물만 골랐어요.">{`${r.analyzed_posts}개 중 ${r.cleanup.length}개만\n정리하면 돼요`}</Title>

      <Panel>
        <div className="big-level">
          지금 <LevelBadge level={r.level} /> → 정리 후 <LevelBadge level={r.level_after_cleanup} />
        </div>
        {r.remaining_after_cleanup.length > 0 && (
          <p className="small">정리 후 남는 단서: {r.remaining_after_cleanup.map((t) => TYPE_LABEL[t]).join(', ')} (이름과 장소가 이어지지 않아요)</p>
        )}
      </Panel>

      {r.cleanup_items.map((it) => {
        const thumb = it.photo_ids.map((id) => uc1.thumbs[id]).find(Boolean)
        return (
          <Panel key={it.post_id}>
            <div className="item">
              {thumb ? <img src={thumb} alt="" /> : <div className="ph" />}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                <strong>
                  {it.caption || '캡션 없음'}
                  {it.posted_at && <span className="small"> · {formatDate(it.posted_at)}</span>}
                </strong>
                <div className="chips">
                  {it.clues.map((c) => (
                    <Chip key={`${c.type}-${c.value}`}>
                      {TYPE_LABEL[c.type]} {c.value}
                    </Chip>
                  ))}
                </div>
                {it.cuts.length > 0 && <span className="small">끊기는 연결: {it.cuts.join(', ')}</span>}
              </div>
            </div>
          </Panel>
        )
      })}

      <Note icon="warn">앱이 게시물을 직접 지우거나 바꾸지 않아요. 삭제보다 비공개 전환을 먼저 권해요.</Note>

      <div className="bottom">
        <a className="btn btn-light" href="https://help.instagram.com/" target="_blank" rel="noreferrer">
          비공개 전환 방법 (인스타그램 도움말)
        </a>
        <Link to="/uc2" className="btn">
          가려서 다시 올리기
        </Link>
      </div>
    </Screen>
  )
}
