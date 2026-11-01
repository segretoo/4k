import type { ReactNode } from 'react'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { endSession, errorMessage } from '../api/client'
import type { PixelName } from '../components/pixels'
import { Bottom, Btn, C, ErrorNote, Frame, JUA, Px } from '../components/wf'
import { session } from '../lib/session'

// 문구는 실제 구현과 같아야 한다 (docs/data-policy.md 10번). 구현을 바꾸면 여기도 같이 고친다.
const SECTIONS: [PixelName, string, ReactNode][] = [
  [
    'photo',
    '무엇을 읽나요',
    <>
      <b>게시물 건강검진:</b> 인스타그램 내보내기 zip 안의 게시물 목록(posts_*.json 또는 posts*.html)과 사진만 꺼내요. 캡션·게시 날짜를 함께 읽어요. DM·댓글·팔로워·프로필 같은 다른 파일은 열지 않고 분석하지 않아요.
      <br />
      <b>올리기 전 체크:</b> 고른 사진 1장과 입력한 캡션만 받아요.
    </>,
  ],
  ['eye', '왜 쓰나요', '아이를 특정할 수 있는 단서(이름·나이·유치원·동네·등원 시간)를 찾아 위험을 알려 드리는 데에만 써요. AI 학습·광고·통계에는 쓰지 않아요.'],
  [
    'server',
    '어디서 처리하나요',
    '꼭꼭 서버와, 같은 내부망에 있는 분석 서버에서만 처리해요. 사진을 외부 AI 회사(API)로 보내지 않아요. 얼굴 인식은 하지 않아요.',
  ],
  [
    'trash',
    '언제 지우나요',
    <>
      올린 zip은 사진을 꺼낸 즉시 지워요. 고르지 않은 사진은 점검을 시작할 때, 고른 사진은 분석이 끝나면 지워요. 끝나지 않고 30분이 지난 파일과 서버를 다시 켤 때 남아 있던 파일도 자동으로 지워요.
      <br />
      올리기 전 체크 사진은 디스크에 저장하지 않고 메모리에서만 처리해요.
    </>,
  ],
  [
    'lock',
    '결과는 어디에 남나요',
    '결과와 찾은 단서는 지금 쓰는 브라우저 탭에만 있고, 탭을 닫으면 사라져요. 앱 운영 로그에는 연결 이벤트의 시각과 업로드·검출·다운로드 개수만 남기며, 사진·캡션·읽은 글자·파일명·IP·세션 ID는 남기지 않아요.',
  ],
  [
    'noEntry',
    '하지 않는 것',
    '다른 사람 계정·주소 분석, 게시물 자동 삭제·자동 게시, 제3자 제공을 하지 않아요. 저장한 가린 사진은 직접 올려 주세요.',
  ],
  [
    'shield',
    '동의를 안 하거나 멈추고 싶다면',
    '동의하지 않아도 되지만 이 경우 점검을 할 수 없어요. 점검 중에도 화면을 닫으면 결과가 사라지고, 올린 파일은 위 시간 안에 지워져요.',
  ],
]

export default function Privacy() {
  const nav = useNavigate()
  const [error, setError] = useState<string | null>(null)
  const [ended, setEnded] = useState(false)
  const disconnect = async () => {
    setError(null)
    try {
      await endSession()
      session.clear()
      setEnded(true)
    } catch (e) {
      setError(errorMessage(e))
    }
  }
  return (
    <Frame gap={14}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, minHeight: 44 }}>
        <button
          type="button"
          onClick={() => nav(-1)}
          aria-label="뒤로"
          style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: 44, height: 44, marginLeft: -10, padding: 0, border: 0, background: 'none', cursor: 'pointer' }}
        >
          <Px name="back" size={20} />
        </button>
        <span style={{ fontFamily: JUA, fontSize: 19 }}>개인정보 처리방침</span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <div
          style={{
            flex: 'none',
            width: 52,
            height: 52,
            boxSizing: 'border-box',
            border: `3px solid ${C.ink}`,
            background: C.pink,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Px name="lock" size={30} />
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <h1 style={{ margin: 0, fontFamily: JUA, fontWeight: 400, fontSize: 24, lineHeight: 1.3 }}>아이 정보, 이렇게 다뤄요</h1>
          <span style={{ fontSize: 13, color: C.sub }}>꼭꼭(팀 4K) · 해커톤 시연용 서비스</span>
        </div>
      </div>

      <ul style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 10 }}>
        {SECTIONS.map(([icon, head, body]) => (
          <li
            key={head}
            style={{ display: 'flex', gap: 12, alignItems: 'flex-start', padding: '12px 14px', background: C.white, border: `3px solid ${C.ink}`, borderRadius: 12 }}
          >
            <Px name={icon} size={24} style={{ flex: 'none' }} />
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <span style={{ fontFamily: JUA, fontSize: 16 }}>{head}</span>
              <span style={{ fontSize: 13, lineHeight: 1.6, color: C.sub }}>{body}</span>
            </div>
          </li>
        ))}
      </ul>

      <p style={{ margin: 0, fontSize: 12, lineHeight: 1.6, color: C.sub }}>
        시연에는 실제 아이 사진이 아닌 합성 이미지와 가상 이름·유치원·동네만 써요.
      </p>

      <Link to="/admin/logs" style={{ fontSize: 13, color: C.sub, textDecoration: 'underline' }}>운영 로그 보기</Link>
      {error && <ErrorNote>{error}</ErrorNote>}

      <Bottom>
        {ended ? (
          <Btn kind="plain" onClick={() => nav('/')}>연결이 해제됐어요 · 홈으로</Btn>
        ) : (
          <>
            <Btn kind="plain" onClick={() => nav(-1)}>확인했어요</Btn>
            <Btn kind="light" onClick={disconnect}>서버 연결 해제</Btn>
          </>
        )}
      </Bottom>
    </Frame>
  )
}
