import { useEffect } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { ErrorBox, Note, Panel, PixelIcon, ProgressCells, Screen, Title, TopBar } from '../components/ui'
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
  // 진행률은 사진 단위. 사진 한 장 안의 VLM → OCR → AI는 서버에서 연달아 돈다.
  const stepIdx = finished ? 4 : done >= total ? 3 : 2

  return (
    <Screen>
      <TopBar title="지난 게시물 점검" step={[3, 3]} />
      <Title sub="화면을 열어 둔 채 잠시 기다려 주세요. 사진은 한 장씩 차례로 읽어요.">{'사진을\n점검하고 있어요'}</Title>

      <Panel>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <h2>
            {finished ? '분석 완료' : '분석 중'}
            {!finished && <span className="blink">...</span>}
          </h2>
          <h2>
            {done} / {total}장
          </h2>
        </div>
        <ProgressCells ratio={total ? done / total : 0} />
        <ul className="steplist">
          {STEPS.map((s, i) => (
            <li key={s} className={i > stepIdx ? 'todo' : ''}>
              {i < stepIdx ? <PixelIcon name="check" color="var(--coral)" /> : <span className={`box-icon ${i === stepIdx ? 'blink' : ''}`} />}
              {s}
            </li>
          ))}
        </ul>
      </Panel>

      {(error || job?.status === 'failed') && (
        <>
          <ErrorBox>{job?.error ?? error}</ErrorBox>
          <Link to="/uc1/upload" className="btn btn-light">
            처음부터 다시 하기
          </Link>
        </>
      )}

      <Note>모든 분석은 꼭꼭 서버 안에서만 해요</Note>
      <Note>끝나면 올린 파일은 모두 지워요</Note>

      <div className="bottom">
        <button type="button" className="btn" disabled={!finished} onClick={() => nav('/uc1/result')}>
          결과 보기
        </button>
      </div>
    </Screen>
  )
}
