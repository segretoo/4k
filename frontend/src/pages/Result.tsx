import { Link, Navigate } from 'react-router-dom'
import { ErrorBox, LevelMeter, Panel, Screen, Title, TopBar } from '../components/ui'
import { LEVEL_LABEL, TYPE_LABEL, TYPE_ORDER } from '../lib/labels'
import { useApp } from '../state/AppState'

export default function Result() {
  const { uc1 } = useApp()
  const r = uc1.result
  if (!r) return <Navigate to="/uc1/upload" replace />

  const headline = [r.card.age, r.card.school, r.card.area].filter(Boolean).join(' · ')
  const reasonSet = new Set(r.reason)

  return (
    <Screen>
      <TopBar title="지난 게시물 점검" back="/" />
      <Title>{`게시물 ${r.analyzed_posts}개를 이어 보면\n낯선 사람은 이만큼\n알아낼 수 있어요`}</Title>

      <Panel>
        {r.card.name && <h2 style={{ fontSize: 26 }}>{r.card.name}</h2>}
        {headline && <p className="sub">{headline}</p>}
        <LevelMeter level={r.level} />
        <p style={{ margin: 0, fontSize: 14, lineHeight: 1.6 }}>{r.explanation}</p>
      </Panel>

      {TYPE_ORDER.some((t) => r.card[t]) && (
        <Panel>
          <div className="rows">
            {TYPE_ORDER.filter((t) => r.card[t]).map((t) => (
              <div key={t} className={`row ${reasonSet.has(t) ? 'hit' : ''}`}>
                <span className="label">{TYPE_LABEL[t]}</span>
                <span className="value">{r.card[t]}</span>
                <span className="small">게시물 {r.sources[t]?.length ?? 0}개</span>
              </div>
            ))}
          </div>
        </Panel>
      )}

      {r.failed_photo_ids.length > 0 && <ErrorBox>사진 {r.failed_photo_ids.length}장은 분석하지 못했어요. 결과에서 빠져 있어요.</ErrorBox>}

      <div className="bottom">
        {r.cleanup.length > 0 && r.level_after_cleanup ? (
          <>
            <p style={{ margin: 0, textAlign: 'center', fontFamily: 'var(--font-title)', fontSize: 18 }}>
              {r.cleanup.length}개만 정리하면 {LEVEL_LABEL[r.level]} → {LEVEL_LABEL[r.level_after_cleanup]}로 내려가요
            </p>
            <Link to="/uc1/cleanup" className="btn">
              정리할 게시물 보기
            </Link>
          </>
        ) : (
          <p className="sub" style={{ textAlign: 'center' }}>
            {r.level === 'safe' ? '지금은 아이를 특정할 단서가 없어요.' : '이름과 장소가 이어지지 않아 정리할 게시물은 없어요.'}
          </p>
        )}
        <Link to="/uc2" className="btn btn-light">
          새 게시물 올리기 전에 확인하기
        </Link>
      </div>
    </Screen>
  )
}
