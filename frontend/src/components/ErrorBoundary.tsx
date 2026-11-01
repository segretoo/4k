import { Component, type ReactNode } from 'react'

/** 화면 코드에서 오류가 나도 하얀 화면 대신 안내를 보여 준다. */
export default class ErrorBoundary extends Component<{ children: ReactNode }, { error: Error | null }> {
  state = { error: null as Error | null }

  static getDerivedStateFromError(error: Error) {
    return { error }
  }

  render() {
    if (!this.state.error) return this.props.children
    return (
      <main style={{ maxWidth: 390, margin: '0 auto', padding: 20, display: 'flex', flexDirection: 'column', gap: 12, color: '#3B2420' }}>
        <h1 style={{ margin: 0, fontFamily: "'Jua', sans-serif", fontWeight: 400, fontSize: 24 }}>화면을 그리다 문제가 생겼어요</h1>
        <p style={{ margin: 0, fontSize: 14, lineHeight: 1.6, color: '#7A5048' }}>
          백엔드를 다시 켠 뒤 처음부터 해 주세요. 계속되면 아래 내용을 팀 채널에 공유해 주세요.
        </p>
        <pre style={{ margin: 0, padding: 10, background: '#fff', border: '2px dashed #EBCFC4', fontSize: 12, whiteSpace: 'pre-wrap' }}>{this.state.error.message}</pre>
        <a href="/" style={{ color: '#C8483E' }}>처음 화면으로</a>
      </main>
    )
  }
}
