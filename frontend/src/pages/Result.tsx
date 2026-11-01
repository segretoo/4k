import { Navigate } from 'react-router-dom'
import type { EntityType } from '../api/types'
import { Bottom, Btn, C, ErrorNote, Frame, Header, JUA, LevelTag, Meter, Px } from '../components/wf'
import { CLUE_ICON, LEVELS, LEVEL_LABEL, TYPE_LABEL, TYPE_ORDER } from '../lib/labels'
import { useApp } from '../state/AppState'


/** 엔진 설명문 "이름 + 유치원 + 등원 시간이 이어져서 ..." 에서 앞부분만 굵게 */
function Explain({ reason, text }: { reason: EntityType[]; text: string }) {
  const head = reason.map((t) => TYPE_LABEL[t]).join(' + ')
  if (!head || !text.startsWith(head)) return <>{text}</>
  return (
    <>
      <b style={{ fontFamily: JUA, fontWeight: 400 }}>{head}</b>
      {text.slice(head.length)}
    </>
  )
}

export default function Result() {
  const { uc1 } = useApp()
  const r = uc1.result
  if (!r) return <Navigate to="/uc1/upload" replace />

  const subline = [r.card.age, r.card.school, r.card.area].filter(Boolean).join(' · ')
  const rows = TYPE_ORDER.filter((t) => r.card[t])
  const canClean = r.cleanup.length > 0 && !!r.level_after_cleanup

  return (
    <Frame gap={12}>
      <Header title="게시물 건강검진" back="/" step={[2, 3]} />

      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        <span style={{ fontSize: 14, color: C.sub }}>게시물 {r.analyzed_posts}개를 이어 보면</span>
        <h1 style={{ margin: 0, fontFamily: JUA, fontWeight: 400, fontSize: 25, lineHeight: 1.3 }}>
          {r.level === 'safe' ? (
            <>
              낯선 사람이 알아낼 수 있는
              <br />
              단서가 없어요
            </>
          ) : (
            <>
              낯선 사람은 이만큼
              <br />
              알아낼 수 있어요
            </>
          )}
        </h1>
      </div>

      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: 12,
          padding: '14px 16px',
          background: C.white,
          border: `3px solid ${C.ink}`,
          borderRadius: 12,
          boxShadow: `4px 4px 0 ${C.ink}`,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div
            style={{
              flex: 'none',
              width: 52,
              height: 52,
              boxSizing: 'border-box',
              border: `3px solid ${C.ink}`,
              background: C.photo,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Px name="kidFace" size={36} label="아이 얼굴 픽셀 아이콘" />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 2, flex: 1, minWidth: 0 }}>
            <span style={{ fontFamily: JUA, fontSize: 22 }}>{r.card.name ?? '이름 모름'}</span>
            <span style={{ fontSize: 13, color: C.sub }}>{subline || '다른 단서는 찾지 못했어요'}</span>
          </div>
          <LevelTag level={r.level} />
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          <div style={{ display: 'flex' }}>
            <Meter level={r.level} h={14} mode="scale" />
          </div>
          <div aria-hidden="true" style={{ display: 'flex', gap: 4, fontSize: 11, color: C.sub, textAlign: 'center' }}>
            {LEVELS.map((lv) => (
              <span key={lv} style={{ flex: 1, ...(lv === r.level ? { fontFamily: JUA, fontSize: 12, color: C.ink } : {}) }}>
                {LEVEL_LABEL[lv]}
              </span>
            ))}
          </div>
          <p style={{ margin: 0, padding: '8px 10px', background: C.bg, border: `2px dashed ${C.dash}`, fontSize: 13, lineHeight: 1.55 }}>
            <Explain reason={r.reason} text={r.explanation} />
          </p>
        </div>

        {rows.length > 0 && (
          <ul style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column' }}>
            {rows.map((t, i) => (
              <li
                key={t}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  padding: i === rows.length - 1 ? '6px 0 0' : '6px 0',
                  borderTop: `2px dashed ${C.dash}`,
                }}
              >
                <span
                  style={{
                    flex: 'none',
                    width: 34,
                    height: 34,
                    boxSizing: 'border-box',
                    border: `2px solid ${C.ink}`,
                    borderRadius: 6,
                    background: C.bg,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <Px name={CLUE_ICON[t]} size={22} />
                </span>
                <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minWidth: 0 }}>
                  <span style={{ fontSize: 12, color: C.sub }}>{TYPE_LABEL[t]}</span>
                  <span style={{ fontFamily: JUA, fontSize: 16 }}>{r.card[t]}</span>
                </div>
                <span style={{ padding: '2px 8px', border: `2px solid ${C.ink}`, borderRadius: 6, background: C.peach, fontFamily: JUA, fontSize: 13 }}>
                  게시물 {r.sources[t]?.length ?? 0}개
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>

      {r.post_results?.length > 0 && (
        <section aria-label="게시물별 분석 결과" style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <h2 style={{ margin: 0, fontFamily: JUA, fontWeight: 400, fontSize: 18 }}>게시물별 결과</h2>
          {r.post_results.map((post) => (
            <details key={post.post_id} style={{ padding: '10px 12px', background: C.white, border: `2px solid ${C.ink}`, borderRadius: 10 }}>
              <summary style={{ cursor: 'pointer', fontFamily: JUA }}>{post.posted_at ?? '게시일 정보 없음'} · 사진 {post.photos.length}장 · {LEVEL_LABEL[post.risk_level]}</summary>
              <p style={{ margin: '8px 0', fontSize: 12, lineHeight: 1.5, overflowWrap: 'anywhere' }}>{post.caption}</p>
              {post.hashtags.length > 0 && <p style={{ margin: '4px 0 8px', fontSize: 12, color: C.sub }}>{post.hashtags.map((tag) => `#${tag}`).join(' ')}</p>}
              {post.photos.map((photo) => (
                <div key={photo.photo_id} style={{ padding: '8px 0', borderTop: `1px dashed ${C.dash}`, fontSize: 12 }}>
                  <b>{photo.source || photo.photo_id}</b>{photo.analysis_failed ? <span> · 분석 실패</span> : null}
                  {photo.entities.length > 0 ? <ul style={{ margin: '4px 0 0', paddingLeft: 18 }}>{photo.entities.map((entity, index) => <li key={`${entity.type}-${entity.value}-${index}`}>{TYPE_LABEL[entity.type]}: {entity.value} · {entity.evidence === 'caption' ? '게시글' : '사진'}</li>)}</ul> : !photo.analysis_failed ? <span> · 검출 단서 없음</span> : null}
                </div>
              ))}
            </details>
          ))}
        </section>
      )}

      {r.failed_photo_ids.length > 0 && <ErrorNote>사진 {r.failed_photo_ids.length}장은 분석하지 못해서 결과에서 빠져 있어요.</ErrorNote>}

      <div
        style={{
          marginTop: 'auto',
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          padding: '12px 14px',
          background: canClean ? C.peach : C.mint,
          border: `3px solid ${C.ink}`,
          borderRadius: 12,
        }}
      >
        <Px name={canClean ? 'bulb' : 'check'} size={24} style={{ flex: 'none' }} />
        <span style={{ fontSize: 14, lineHeight: 1.5 }}>
          {canClean ? (
            <>
              <b style={{ fontFamily: JUA, fontWeight: 400, fontSize: 15 }}>{r.cleanup.length}장만 정리하면</b> {LEVEL_LABEL[r.level]} →{' '}
              {LEVEL_LABEL[r.level_after_cleanup!]}로 내려가요
            </>
          ) : r.level === 'safe' ? (
            '지금은 정리할 게시물이 없어요. 새 게시물은 올리기 전 체크로 확인해 보세요.'
          ) : (
            '이름과 장소가 이어지지 않아 정리할 게시물은 없어요.'
          )}
        </span>
      </div>

      <Bottom gap={0} style={{ marginTop: 0 }}>
        {canClean ? <Btn to="/uc1/cleanup">정리할 게시물 보기</Btn> : <Btn to="/uc2">올리기 전 체크하기</Btn>}
      </Bottom>
    </Frame>
  )
}
