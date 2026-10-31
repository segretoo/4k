import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getStatus } from '../api/client'
import { Chip, Note, PixelIcon, Screen } from '../components/ui'

export default function Landing() {
  const [mock, setMock] = useState(false)
  useEffect(() => {
    getStatus().then((s) => setMock(s.gpu_mock)).catch(() => undefined)
  }, [])

  return (
    <Screen>
      <header className="topbar">
        <PixelIcon name="heart" size={24} color="var(--coral)" />
        <span className="topbar-title" style={{ color: 'var(--coral)', fontSize: 24 }}>
          꼭꼭
        </span>
      </header>
      {mock && (
        <span className="badge-mock">
          <Chip tone="white">개발 모드 · 가짜 분석 응답</Chip>
        </span>
      )}

      <div className="title-block">
        <h1 style={{ fontSize: 32 }}>{'꼭꼭 숨어라,\n이름표 보일라'}</h1>
        <p className="sub">게시물 하나는 안전해 보여도, 모으면 아이의 이름·유치원·동네가 맞춰질 수 있어요.</p>
      </div>

      <div className="hero" aria-hidden="true">
        <div className="polaroid">
          <div className="pic">
            <svg width="96" height="128" viewBox="0 0 12 16" shapeRendering="crispEdges">
              <rect x="3" y="0" width="6" height="2" fill="#F6C945" />
              <rect x="2" y="2" width="8" height="5" fill="#FBD9C0" />
              <rect x="3" y="4" width="1" height="1" fill="#3B2420" />
              <rect x="8" y="4" width="1" height="1" fill="#3B2420" />
              <rect x="2" y="7" width="8" height="6" fill="#9AA0C0" />
              <rect x="6" y="9" width="3" height="2" fill="#FFFFFF" />
              <rect x="3" y="13" width="2" height="3" fill="#5B3A29" />
              <rect x="7" y="13" width="2" height="3" fill="#5B3A29" />
            </svg>
          </div>
          <p>오늘도 등원 완료!</p>
        </div>
        <div className="floaters">
          {['이름 ?', '유치원 ?', '동네 ?', '등원 시간 ?', '나이 ?'].map((t) => (
            <span key={t} className="chip">
              {t}
            </span>
          ))}
        </div>
      </div>

      <div className="bottom">
        <Link to="/consent?next=uc1" className="cta">
          <strong>지난 게시물 한 번 점검하기</strong>
          <span>인스타그램 '내 정보 내보내기' 파일로 · 한 번만 해 두면 돼요</span>
        </Link>
        <Link to="/consent?next=uc2" className="cta light">
          <strong>올리기 전에 확인하기</strong>
          <span>새 사진과 캡션을 미리 진단해요</span>
        </Link>
        <Note>원본 사진은 우리 서버 밖으로 나가지 않아요</Note>
        <Note icon="check">내 계정 데이터만 분석하고, 자동으로 지우거나 올리지 않아요</Note>
      </div>
    </Screen>
  )
}
