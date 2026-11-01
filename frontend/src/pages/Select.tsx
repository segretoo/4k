import { useMemo, useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { errorMessage, startJob } from '../api/client'
import { Bottom, Btn, C, ErrorNote, Frame, Header, Heading, JUA, Notes, Px } from '../components/wf'
import { useApp } from '../state/AppState'
import { TYPE_LABEL } from '../lib/labels'
import type { EntityType } from '../api/types'

export default function Select() {
  const nav = useNavigate()
  const { uc1, setUc1 } = useApp()
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [manualDrafts, setManualDrafts] = useState<Record<string, string>>({})
  const [manualTypes, setManualTypes] = useState<Record<string, EntityType>>({})

  const photos = useMemo(
    () => (uc1.upload?.posts ?? []).flatMap((p) => p.photos.map((ph) => ({ ...ph, post: p }))),
    [uc1.upload],
  )
  if (!uc1.upload) return <Navigate to="/uc1/upload" replace />

  const max = uc1.upload.max_select
  const selected = new Set(uc1.selected)
  const candidateIds = (postId: string) => {
    const post = uc1.upload!.posts.find((p) => p.post_id === postId)
    if (Object.prototype.hasOwnProperty.call(uc1.candidateSelections, postId)) return uc1.candidateSelections[postId]
    return (post?.candidates ?? []).filter((c) => c.selected_by_default).map((c) => c.id)
  }

  const toggle = (id: string) => {
    setError(null)
    if (selected.has(id)) return setUc1({ selected: uc1.selected.filter((x) => x !== id) })
    if (selected.size >= max) return setError(`사진은 ${max}장까지 고를 수 있어요. 다른 사진을 먼저 빼 주세요.`)
    setUc1({ selected: [...uc1.selected, id] })
  }

  const toggleCandidate = (postId: string, id: string) => {
    const current = candidateIds(postId)
    const next = current.includes(id) ? current.filter((value) => value !== id) : [...current, id]
    setUc1({ candidateSelections: { ...uc1.candidateSelections, [postId]: next } })
  }

  const addManualCandidate = (postId: string) => {
    const post = uc1.upload!.posts.find((item) => item.post_id === postId)
    const value = (manualDrafts[postId] ?? '').trim()
    if (!post || !value) return
    if (!post.caption.toLocaleLowerCase().includes(value.toLocaleLowerCase())) {
      setError('직접 추가하는 글자는 해당 게시물 캡션에 실제로 있어야 해요.')
      return
    }
    const type = manualTypes[postId] ?? 'school'
    const current = uc1.manualCandidates[postId] ?? []
    if (current.some((item) => item.type === type && item.value.toLocaleLowerCase() === value.toLocaleLowerCase())) return
    setError(null)
    setUc1({ manualCandidates: { ...uc1.manualCandidates, [postId]: [...current, { type, value }] } })
    setManualDrafts({ ...manualDrafts, [postId]: '' })
  }

  const start = async () => {
    setBusy(true)
    try {
      const selections = Object.fromEntries(uc1.upload!.posts.map((post) => [post.post_id, candidateIds(post.post_id)]))
      const job = await startJob(uc1.upload!.upload_id, uc1.selected, selections, uc1.manualCandidates)
      setUc1({ jobId: job.job_id, result: null })
      nav('/uc1/analyze')
    } catch (e) {
      setError(errorMessage(e))
      setBusy(false)
    }
  }

  return (
    <Frame>
      <Header title="게시물 건강검진" back="/uc1/upload" step={[2, 3]} />
      <Heading
        lines={['점검할 사진을', '골라 주세요']}
        sub={`게시물 ${uc1.upload.total_posts}개를 찾았어요. 캡션에 단서가 보이는 사진과 최근 사진을 먼저 골라 뒀어요.`}
      />

      <section aria-label="게시물 단서 후보" style={{ display: 'flex', flexDirection: 'column', gap: 9, padding: '12px 14px', background: C.white, border: `3px solid ${C.ink}`, borderRadius: 12 }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          <strong style={{ fontFamily: JUA, fontWeight: 400, fontSize: 16 }}>게시물에서 찾은 단서 후보</strong>
          <span style={{ fontSize: 12, color: C.sub, lineHeight: 1.5 }}>사진 분석 전에 캡션·해시태그 후보를 확인하고 켜거나 끄세요. 후보 점검은 CPU에서 처리해 GPU 분석을 시작하지 않습니다.</span>
        </div>
        {uc1.upload.posts.filter((post) => post.candidates.length > 0 || post.photos.some((photo) => selected.has(photo.photo_id))).map((post) => {
          const active = new Set(candidateIds(post.post_id))
          return (
            <div key={post.post_id} style={{ display: 'flex', flexDirection: 'column', gap: 6, paddingTop: 8, borderTop: `1px dashed ${C.dash}` }}>
              <span style={{ fontSize: 12, color: C.sub }}>{post.posted_at ?? '게시일 정보 없음'} · 사진 {post.photos.length}장</span>
              <span style={{ fontSize: 13, lineHeight: 1.45, overflowWrap: 'anywhere' }}>{post.caption}</span>
              {post.hashtags.length > 0 && <span style={{ fontSize: 12, color: C.sub }}>{post.hashtags.map((tag) => `#${tag}`).join(' ')}</span>}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {post.candidates.map((candidate) => {
                  const on = active.has(candidate.id)
                  return (
                    <button key={candidate.id} type="button" aria-pressed={on}
                      onClick={() => toggleCandidate(post.post_id, candidate.id)}
                      style={{ padding: '5px 8px', border: `2px solid ${C.ink}`, borderRadius: 8, background: on ? C.coral : C.white, color: on ? C.white : C.ink, fontSize: 12, cursor: 'pointer' }}>
                      {on ? '✓ ' : '+ '}{TYPE_LABEL[candidate.type]} · {candidate.source === 'hashtag' ? '#' : ''}{candidate.value}
                    </button>
                  )
                })}
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 6 }}>
                <select aria-label="직접 추가할 단서 종류" value={manualTypes[post.post_id] ?? 'school'}
                  onChange={(event) => setManualTypes({ ...manualTypes, [post.post_id]: event.target.value as EntityType })}
                  style={{ minHeight: 34, border: `2px solid ${C.ink}`, borderRadius: 6, background: C.white }}>
                  {(['name', 'age', 'school', 'area', 'time', 'contact'] as EntityType[]).map((type) => <option key={type} value={type}>{TYPE_LABEL[type]}</option>)}
                </select>
                <input aria-label="캡션에서 직접 추가할 단서" value={manualDrafts[post.post_id] ?? ''}
                  onChange={(event) => setManualDrafts({ ...manualDrafts, [post.post_id]: event.target.value })}
                  onKeyDown={(event) => { if (event.key === 'Enter') { event.preventDefault(); addManualCandidate(post.post_id) } }}
                  placeholder="캡션 글자 추가" style={{ flex: 1, minWidth: 100, minHeight: 30, border: `2px solid ${C.ink}`, borderRadius: 6, padding: '2px 7px' }} />
                <button type="button" onClick={() => addManualCandidate(post.post_id)} style={{ minHeight: 34, padding: '4px 9px', border: `2px solid ${C.ink}`, borderRadius: 6, background: C.peach, cursor: 'pointer' }}>추가</button>
                {(uc1.manualCandidates[post.post_id] ?? []).map((item, index) => (
                  <button key={`${item.type}-${item.value}-${index}`} type="button" aria-label={`${TYPE_LABEL[item.type]} ${item.value} 제거`}
                    onClick={() => setUc1({ manualCandidates: { ...uc1.manualCandidates, [post.post_id]: (uc1.manualCandidates[post.post_id] ?? []).filter((_, i) => i !== index) } })}
                    style={{ padding: '4px 8px', border: `2px solid ${C.ink}`, borderRadius: 8, background: C.mint, cursor: 'pointer', fontSize: 12 }}>직접 추가: {TYPE_LABEL[item.type]} · {item.value} ×</button>
                ))}
              </div>
            </div>
          )
        })}
        {!uc1.upload.posts.some((post) => post.candidates.length > 0) && <span style={{ fontSize: 12, color: C.sub }}>자동으로 추린 단서는 없어요. 아래에서 필요한 사진을 직접 추가해 주세요.</span>}
      </section>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
        <span style={{ fontFamily: JUA, fontSize: 18 }}>
          {selected.size} / {max}장 선택
        </span>
        <span style={{ fontSize: 13, color: C.sub }}>추천 먼저 · 최근순</span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
        {photos.map((ph, i) => {
          const on = selected.has(ph.photo_id)
          const hint = ph.post.recommended ? ph.post.hints[0] || '추천' : on ? '최근' : ''
          const thumb = uc1.thumbs[ph.photo_id]
          return (
            <button
              key={ph.photo_id}
              type="button"
              role="checkbox"
              aria-checked={on}
              aria-label={`사진 ${i + 1}, ${on ? '선택됨' : '선택 안 됨'}${hint ? `, 추천 이유 ${hint}` : ''}`}
              onClick={() => toggle(ph.photo_id)}
              style={{
                position: 'relative',
                aspectRatio: '1 / 1',
                padding: 0,
                boxSizing: 'border-box',
                border: `3px solid ${C.ink}`,
                background: on ? C.photo : C.empty,
                opacity: on ? 1 : 0.55,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                overflow: 'hidden',
                cursor: 'pointer',
              }}
            >
              {thumb ? (
                <img src={thumb} alt="" style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover' }} />
              ) : (
                <Px name="photoTile" size={30} />
              )}
              <span
                style={{
                  position: 'absolute',
                  left: 6,
                  top: 6,
                  width: 24,
                  height: 24,
                  boxSizing: 'border-box',
                  border: `2px solid ${C.ink}`,
                  background: on ? C.coral : C.white,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                {on && <Px name="tick" size={14} />}
              </span>
              {hint && on && (
                <span
                  style={{
                    position: 'absolute',
                    left: 6,
                    bottom: 6,
                    maxWidth: 'calc(100% - 12px)',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    padding: '1px 6px',
                    background: C.white,
                    border: `2px solid ${C.ink}`,
                    fontSize: 11,
                    lineHeight: 1.4,
                    color: C.ink,
                  }}
                >
                  {hint}
                </span>
              )}
            </button>
          )
        })}
      </div>

      {error && <ErrorNote>{error}</ErrorNote>}
      <Notes items={[['lock', '고른 사진만 분석하고, 나머지는 바로 지워요']]} />

      <Bottom>
        <Btn onClick={start} disabled={selected.size === 0 || busy}>
          {selected.size === 0 ? '사진을 1장 이상 골라 주세요' : busy ? '시작하는 중...' : `점검 시작 (${selected.size}장)`}
        </Btn>
      </Bottom>
    </Frame>
  )
}
