import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import type { PixelName } from '../components/pixels'
import { Btn, Bottom, C, Frame, Header, JUA, Px } from '../components/wf'
import { session } from '../lib/session'

const PROMISES: [PixelName, string, string][] = [
  ['photo', '게시물 사진·캡션·날짜만 읽어요', 'DM·댓글·팔로워는 열지 않고 버려요'],
  ['eye', '위험 경고에만 써요', 'AI 학습·광고에 쓰지 않아요'],
  ['server', '우리 서버에서만 분석해요', '외부 AI 회사로 보내지 않아요'],
  ['trash', '끝나면 바로 지워요', '결과도 화면을 닫으면 사라져요'],
  ['noEntry', '하지 않는 것', '얼굴 인식 · 남의 계정 분석 · 자동 게시'],
]

const checkLabel = { display: 'flex', alignItems: 'center', gap: 10, minHeight: 40, fontSize: 13, lineHeight: 1.45, cursor: 'pointer' } as const
const checkBox = { flex: 'none', width: 22, height: 22, margin: 0, accentColor: C.coral } as const
const must = <b style={{ fontFamily: JUA, fontWeight: 400, color: C.coralDark }}>[필수]</b>

export default function Consent() {
  const nav = useNavigate()
  const [params] = useSearchParams()
  const next = params.get('next') === 'uc2' ? '/uc2' : '/uc1/upload'
  // 같은 탭에서 이미 동의했으면 체크된 채로 보여 준다 (탭을 닫으면 다시 물어봄)
  const [agreeA, setA] = useState(session.hasConsent)
  const [agreeB, setB] = useState(session.hasConsent)
  const canGo = agreeA && agreeB

  const go = () => {
    session.setConsent()
    nav(next)
  }

  return (
    <Frame gap={12}>
      <Header title="시작하기 전에" back="/" />

      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <div
          style={{
            flex: 'none',
            width: 44,
            height: 44,
            boxSizing: 'border-box',
            border: `3px solid ${C.ink}`,
            background: C.pink,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Px name="shield" size={26} />
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <h1 style={{ margin: 0, fontFamily: JUA, fontWeight: 400, fontSize: 22, lineHeight: 1.25 }}>꼭꼭 약속할게요</h1>
          <span style={{ fontSize: 13, color: C.sub }}>아이 정보를 지키려고 만든 서비스니까요</span>
        </div>
      </div>

      <ul
        style={{
          margin: 0,
          padding: '12px 14px',
          listStyle: 'none',
          background: C.white,
          border: `3px solid ${C.ink}`,
          borderRadius: 12,
          boxShadow: `4px 4px 0 ${C.ink}`,
          display: 'flex',
          flexDirection: 'column',
          gap: 10,
        }}
      >
        {PROMISES.map(([icon, head, body]) => (
          <li key={head} style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            <Px name={icon} size={20} style={{ flex: 'none' }} />
            <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
              <span style={{ fontFamily: JUA, fontSize: 14 }}>{head}</span>
              <span style={{ fontSize: 12, lineHeight: 1.4, color: C.sub }}>{body}</span>
            </div>
          </li>
        ))}
      </ul>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        <label style={checkLabel}>
          <input type="checkbox" checked={agreeA} onChange={() => setA(!agreeA)} style={checkBox} />
          <span>
            {must} 위 내용을 확인했고, 개인정보 수집·이용에 동의해요
          </span>
        </label>
        <label style={checkLabel}>
          <input type="checkbox" checked={agreeB} onChange={() => setB(!agreeB)} style={checkBox} />
          <span>
            {must} 사진 속 아이의 보호자(법정대리인)예요
          </span>
        </label>
        <span style={{ fontSize: 12, lineHeight: 1.5, color: C.sub }}>
          동의하지 않을 수 있어요. 이 경우 점검을 진행할 수 없어요.{' '}
          <Link to="/privacy">개인정보 처리방침 전문 보기</Link>
        </span>
      </div>

      <Bottom gap={0}>
        <Btn onClick={go} disabled={!canGo}>
          {canGo ? '동의하고 시작하기' : '필수 항목에 동의해 주세요'}
        </Btn>
      </Bottom>
    </Frame>
  )
}
