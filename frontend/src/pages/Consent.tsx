import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Panel, PixelIcon, Screen, Title, TopBar } from '../components/ui'
import { session } from '../lib/session'

const PROMISES = [
  ['게시물 사진·캡션·날짜만 읽어요', 'DM·댓글·팔로워 같은 다른 데이터는 열지 않고 바로 버려요.'],
  ['위험 경고에만 써요', 'AI 학습이나 광고에는 쓰지 않아요.'],
  ['우리 서버 안에서만 분석해요', '사진을 외부 AI 회사로 보내지 않아요.'],
  ['분석이 끝나면 바로 지워요', '올린 파일은 삭제하고, 결과는 화면을 닫으면 사라져요.'],
]

export default function Consent() {
  const nav = useNavigate()
  const [params] = useSearchParams()
  const next = params.get('next') === 'uc2' ? '/uc2' : '/uc1/upload'
  const [agree, setAgree] = useState(false)
  const [guardian, setGuardian] = useState(false)
  const [tried, setTried] = useState(false)

  const submit = () => {
    setTried(true)
    if (!agree || !guardian) return
    session.setConsent()
    nav(next)
  }

  return (
    <Screen>
      <TopBar title="시작하기 전에" back="/" />
      <Title sub="아이 정보를 지키려고 만든 서비스니까요">꼭꼭 약속할게요</Title>

      <Panel>
        {PROMISES.map(([head, body]) => (
          <div key={head} style={{ display: 'flex', gap: 10 }}>
            <PixelIcon name="check" size={18} color="var(--coral)" />
            <div>
              <strong>{head}</strong>
              <p className="sub" style={{ fontSize: 13 }}>
                {body}
              </p>
            </div>
          </div>
        ))}
        <p className="small">하지 않는 것: 얼굴 인식, 다른 사람 계정 분석, 게시물 자동 삭제·게시</p>
      </Panel>

      <label className="toggle">
        <input type="checkbox" checked={agree} onChange={(e) => setAgree(e.target.checked)} />
        <span>[필수] 위 내용을 확인했고, 개인정보 수집·이용에 동의해요</span>
      </label>
      <label className="toggle">
        <input type="checkbox" checked={guardian} onChange={(e) => setGuardian(e.target.checked)} />
        <span>[필수] 사진 속 아이의 보호자(법정대리인)예요</span>
      </label>
      <p className="small">동의하지 않을 수 있어요. 이 경우 점검을 진행할 수 없어요.</p>

      <div className="bottom">
        {tried && (!agree || !guardian) && <p className="small" style={{ color: 'var(--coral)' }}>필수 항목에 동의해 주세요</p>}
        <button type="button" className="btn" onClick={submit}>
          동의하고 시작하기
        </button>
      </div>
    </Screen>
  )
}
