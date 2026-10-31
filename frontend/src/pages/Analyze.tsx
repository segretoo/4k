import { useEffect } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { Bottom, Btn, C, Cells, ErrorNote, Frame, Header, Heading, JUA, Notes, Panel, Px } from '../components/wf'
import { useJobProgress } from '../hooks/useJobProgress'
import { session } from '../lib/session'
import { useApp } from '../state/AppState'

const STEPS = ['사진 속 글자 찾기 (VLM)', '작은 글자 다시 읽기 (OCR)', '단서와 위험 판단하기 (AI)', '게시물끼리 단서 연결하기']

export default function Analyze() {
  const nav = useNavigate()
  const { uc1, setUc1 } = useApp()
  const { job, error } = useJobProgress(uc1.jobId)

  useEffect(() => {
    if (job?.status === 'done' && job.result) {
      setUc1({ result: job.result })
      session.setClues(job.result.clues) // UC2에서 이어 보기 위해 브라우저에만 보관
    }
  }, [job, setUc1])

  if (!uc1.jobId) return <Navigate to="/uc1/upload" replace />

  const done = job?.done ?? 0
  const total = job?.total ?? uc1.selected.length
  const finished = job?.status === 'done'
  const failed = job?.status === 'failed' || !!error
  // 진행률은 사진 단위. 사진 한 장 안의 VLM → OCR → AI는 서버에서 연달아 돈다.
  const stepIdx = finished ? 4 : done >= total ? 3 : 2

  return (
    <Frame>
      <Header title="지난 게시물 점검" back="/uc1/select" step={[3, 3]} />
      <Heading
        lines={finished ? ['점검이', '끝났어요'] : ['사진을', '점검하고 있어요']}
        sub={finished ? '결과를 확인해 보세요. 올린 파일은 이미 지웠어요.' : '화면을 열어 둔 채 잠시 기다려 주세요. 사진은 한 장씩 차례로 읽어요.'}
      />

      <Panel>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
          <span style={{ fontFamily: JUA, fontSize: 17 }}>
            {finished ? '분석 완료' : failed ? '분석 멈춤' : '분석 중'}
            {!finished && !failed && <span className="blink">...</span>}
          </span>
          <span style={{ fontFamily: JUA, fontSize: 17 }}>
            {done} / {total}장
          </span>
        </div>
        <Cells ratio={total ? done / total : 0} label={`사진 ${total}장 중 ${done}장 완료`} />
        <ul style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 8, fontSize: 14 }}>
          {STEPS.map((s, i) => {
            const state = i < stepIdx ? 'done' : i === stepIdx ? 'now' : 'todo'
            return (
              <li key={s} style={{ display: 'flex', alignItems: 'center', gap: 8, color: state === 'done' ? C.sub : state === 'now' ? C.ink : '#B29A93' }}>
                {state === 'done' ? (
                  <Px name="check" size={16} />
                ) : (
                  <span
                    className={state === 'now' && !failed ? 'blink' : undefined}
                    style={{
                      width: 12,
                      height: 12,
                      margin: 2,
                      boxSizing: 'border-box',
                      border: `2px solid ${state === 'now' ? C.ink : '#C9B3AC'}`,
                      background: state === 'now' ? C.peach : C.white,
                    }}
                  />
                )}
                {s}
              </li>
            )
          })}
        </ul>
      </Panel>

      {failed && <ErrorNote>{job?.error ?? error}</ErrorNote>}

      <Notes
        items={[
          ['lock', '모든 분석은 꼭꼭 서버 안에서만 해요'],
          ['lock', '끝나면 올린 파일은 모두 지워요'],
        ]}
      />

      <Bottom>
        {failed ? (
          <Btn to="/uc1/upload">처음부터 다시 하기</Btn>
        ) : (
          <Btn onClick={() => nav('/uc1/result')} disabled={!finished}>
            {finished ? '결과 보기' : '분석이 끝나면 결과를 볼 수 있어요'}
          </Btn>
        )}
      </Bottom>
    </Frame>
  )
}
