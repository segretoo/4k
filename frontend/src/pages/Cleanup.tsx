import { Navigate, useNavigate } from 'react-router-dom'
import { Bottom, Btn, C, Chip, Frame, Header, JUA, LevelTag, Px } from '../components/wf'
import { TYPE_LABEL, formatDate } from '../lib/labels'
import { useApp } from '../state/AppState'

/** 캡션 앞부분을 게시물 이름처럼 짧게 (해시태그·이모지 제외) */
function shortTitle(caption: string): string {
  const plain = caption
    .replace(/#\S+/g, '')
    .replace(/\p{Extended_Pictographic}/gu, '')
    .replace(/\s+/g, ' ')
    .trim()
  if (!plain) return '캡션 없는 게시물'
  return plain.length > 12 ? `${plain.slice(0, 12)}…` : plain
}

export default function Cleanup() {
  const nav = useNavigate()
  const { uc1, resetUc2, setUc2 } = useApp()
  const r = uc1.result
  if (!r || !r.level_after_cleanup) return <Navigate to="/uc1/result" replace />

  // 이 게시물을 가려서 다시 올리기: 캡션은 채워 두고, 원본 사진은 사용자가 다시 고른다
  // (서버에는 원본이 남아 있지 않음 — 분석 후 삭제)
  const fixPost = (caption: string, title: string) => {
    resetUc2()
    setUc2({ caption })
    nav('/uc2', { state: { from: title } })
  }

  const remain = r.remaining_after_cleanup.map((t) => TYPE_LABEL[t]).join(', ')

  return (
    <Frame gap={12}>
      <Header title="게시물 건강검진" back="/uc1/result" step={[3, 3]} />
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        <h1 style={{ margin: 0, fontFamily: JUA, fontWeight: 400, fontSize: 22, lineHeight: 1.3 }}>
          {r.analyzed_posts}개 중 {r.cleanup.length}개만 정리하면 돼요
        </h1>
        {/* 지금 → 정리 후 한 줄 */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          <LevelTag level={r.level} size={13} />
          <span style={{ fontFamily: JUA, fontSize: 16 }}>→</span>
          <LevelTag level={r.level_after_cleanup} size={13} />
          <span style={{ fontSize: 12, color: C.sub }}>{remain ? `남는 단서: ${remain}` : '남는 단서 없음'}</span>
        </div>
      </div>

      <ul style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 8 }}>
        {r.cleanup_items.map((it) => {
          const thumb = it.photo_ids.map((id) => uc1.thumbs[id]).find(Boolean)
          return (
            <li
              key={it.post_id}
              style={{ display: 'flex', alignItems: 'center', gap: 10, padding: 8, background: C.white, border: `3px solid ${C.ink}`, borderRadius: 12 }}
            >
              <div
                style={{
                  flex: 'none',
                  width: 52,
                  height: 52,
                  boxSizing: 'border-box',
                  border: `2px solid ${C.ink}`,
                  background: C.photo,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  overflow: 'hidden',
                }}
              >
                {thumb ? (
                  <img src={thumb} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                ) : (
                  <Px name="photo" size={30} label="사진 자리" />
                )}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4, minWidth: 0, flex: 1 }}>
                <span style={{ fontFamily: JUA, fontSize: 14 }}>
                  {shortTitle(it.caption)}
                  {it.posted_at && ` · ${formatDate(it.posted_at)}`}
                </span>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                  {it.clues.map((c) => (
                    <Chip key={`${c.type}-${c.value}`} size={11} pad="0 6px">
                      {TYPE_LABEL[c.type]} · {c.value}
                    </Chip>
                  ))}
                </div>
                {it.cuts.length > 0 && (
                  <span style={{ fontSize: 11, color: C.sub }}>
                    끊기는 연결: <b style={{ color: C.ink }}>{it.cuts.join(', ')}</b>
                  </span>
                )}
              </div>
              <button
                type="button"
                onClick={() => fixPost(it.caption, shortTitle(it.caption))}
                style={{
                  flex: 'none',
                  alignSelf: 'stretch',
                  padding: '0 8px',
                  border: `2px solid ${C.ink}`,
                  borderRadius: 8,
                  background: C.white,
                  color: C.coralDark,
                  fontFamily: JUA,
                  fontSize: 12,
                  lineHeight: 1.3,
                  cursor: 'pointer',
                }}
              >
                가려서
                <br />
                다시 →
              </button>
            </li>
          )
        })}
      </ul>

      <Bottom>
        <p style={{ margin: 0, fontSize: 12, lineHeight: 1.5, color: C.sub, textAlign: 'center' }}>
          앱이 직접 지우지 않아요. 삭제보다 <b style={{ color: C.ink }}>비공개 전환</b>을 먼저 권해요.
        </p>
        <div style={{ display: 'flex', gap: 10 }}>
          <Btn kind="light" href="https://help.instagram.com/" style={{ flex: 1, fontSize: 16 }}>
            비공개 전환 방법
          </Btn>
          <Btn onClick={() => fixPost(r.cleanup_items[0]?.caption ?? '', shortTitle(r.cleanup_items[0]?.caption ?? ''))} style={{ flex: 1, fontSize: 16 }}>
            가려서 다시 올리기
          </Btn>
        </div>
      </Bottom>
    </Frame>
  )
}
