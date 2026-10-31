import { Navigate, useNavigate } from 'react-router-dom'
import { Bottom, Btn, C, Chip, Frame, Header, Heading, JUA, MeterRow, Panel, Px } from '../components/wf'
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
      <Heading lines={[`${r.analyzed_posts}개 중 ${r.cleanup.length}개만`, '정리하면 돼요']} sub="위험한 조합을 끊는 게시물만 골랐어요." size={25} gap={6} />

      <Panel style={{ gap: 10, padding: '12px 14px' }}>
        <MeterRow label="지금" level={r.level} />
        <MeterRow label="정리 후" level={r.level_after_cleanup} />
        <span style={{ fontSize: 12, color: C.sub }}>
          {remain ? `정리 후 남는 단서: ${remain} (어디 있는지는 알 수 없어요)` : '정리하면 남는 단서가 없어요'}
        </span>
      </Panel>

      <ul style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 10 }}>
        {r.cleanup_items.map((it) => {
          const thumb = it.photo_ids.map((id) => uc1.thumbs[id]).find(Boolean)
          return (
            <li
              key={it.post_id}
              style={{ display: 'flex', gap: 12, padding: 10, background: C.white, border: `3px solid ${C.ink}`, borderRadius: 12 }}
            >
              <div
                style={{
                  flex: 'none',
                  width: 60,
                  height: 60,
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
              <div style={{ display: 'flex', flexDirection: 'column', gap: 5, minWidth: 0 }}>
                <span style={{ fontFamily: JUA, fontSize: 15 }}>
                  {shortTitle(it.caption)}
                  {it.posted_at && ` · ${formatDate(it.posted_at)}`}
                </span>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {it.clues.map((c) => (
                    <Chip key={`${c.type}-${c.value}`}>
                      {TYPE_LABEL[c.type]} · {c.value}
                    </Chip>
                  ))}
                </div>
                {it.cuts.length > 0 && (
                  <span style={{ fontSize: 12, color: C.sub }}>
                    끊기는 연결: <b style={{ color: C.ink }}>{it.cuts.join(', ')}</b>
                  </span>
                )}
                <button
                  type="button"
                  onClick={() => fixPost(it.caption, shortTitle(it.caption))}
                  style={{
                    alignSelf: 'flex-start',
                    marginTop: 2,
                    padding: '3px 10px',
                    border: `2px solid ${C.ink}`,
                    borderRadius: 8,
                    background: C.white,
                    color: C.coralDark,
                    fontFamily: JUA,
                    fontSize: 13,
                    cursor: 'pointer',
                  }}
                >
                  이 게시물 가려서 다시 올리기 →
                </button>
              </div>
            </li>
          )
        })}
      </ul>

      <p style={{ margin: 0, fontSize: 12, lineHeight: 1.6, color: C.sub }}>
        앱이 게시물을 직접 지우거나 바꾸지 않아요. 삭제보다 <b style={{ color: C.ink }}>비공개 전환</b>을 먼저 권해요.
      </p>

      <Bottom>
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
