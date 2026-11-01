import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { cancelUpload, errorMessage, fetchThumb, getStatus, uploadExport } from '../api/client'
import { Bottom, Btn, C, Cells, ErrorNote, FilePick, Frame, Header, Heading, JUA, Notes, Panel } from '../components/wf'
import { useApp } from '../state/AppState'

const GUIDE = [
  '계정 센터 → 내 정보 및 권한',
  '내 정보 내보내기 → 기기로 내보내기',
  "'미디어'만 체크, 나머지 모두 지우기",
  'JSON 형식으로 받은 .zip 올리기',
]

type Phase = 'idle' | 'uploading' | 'recommending' | 'thumbs'
const PHASE_LABEL: Record<Phase, string> = {
  idle: '올리기',
  uploading: '올리는 중',
  recommending: '점검할 사진 고르는 중',
  thumbs: '사진 불러오는 중',
}

export default function Upload() {
  const nav = useNavigate()
  const { uc1, setUc1, resetUc1 } = useApp()
  const [file, setFile] = useState<File | null>(null)
  const [maxMb, setMaxMb] = useState(300)
  const [maxPhotos, setMaxPhotos] = useState(10)
  const [phase, setPhase] = useState<Phase>('idle')
  const [ratio, setRatio] = useState(0)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getStatus()
      .then((s) => {
        setMaxMb(s.max_zip_mb)
        setMaxPhotos(s.max_photos)
      })
      .catch(() => undefined)
  }, [])

  const pick = (f: File | undefined) => {
    setError(null)
    if (!f) return
    // 보내기 전에 브라우저에서 먼저 검사 (서버도 다시 검사함)
    if (!f.name.toLowerCase().endsWith('.zip')) return setError('zip 파일만 올릴 수 있어요.')
    if (f.size > maxMb * 1024 * 1024) return setError(`파일이 너무 커요. ${maxMb}MB 이하로 올려 주세요.`)
    setFile(f)
  }

  const submit = async () => {
    if (!file) return
    setError(null)
    if (uc1.upload) await cancelUpload(uc1.upload.upload_id) // 이전 업로드는 지우고 새로
    resetUc1()
    try {
      setPhase('uploading')
      const res = await uploadExport(file, (r) => {
        setRatio(r)
        if (r >= 1) setPhase('recommending')
      })
      setPhase('thumbs')
      const entries = await Promise.all(
        res.posts.flatMap((p) => p.photos).map(async (ph) => [ph.photo_id, await fetchThumb(ph.thumb_url)] as const),
      )
      setUc1({ upload: res, thumbs: Object.fromEntries(entries), selected: res.recommended_photo_ids })
      nav('/uc1/select')
    } catch (e) {
      setError(errorMessage(e))
      setPhase('idle')
    }
  }

  const busy = phase !== 'idle'

  return (
    <Frame>
      <Header title="게시물 건강검진" back="/" step={[1, 3]} />
      <Heading lines={['지난 게시물을', '한 번에 점검해요']} sub="인스타그램 내보내기 파일을 올려 주세요. 건강검진처럼 처음 한 번만 하면 돼요." />

      <ol
        style={{
          margin: 0,
          padding: '14px 16px',
          listStyle: 'none',
          background: C.white,
          border: `3px solid ${C.ink}`,
          borderRadius: 12,
          boxShadow: `4px 4px 0 ${C.ink}`,
          display: 'flex',
          flexDirection: 'column',
          gap: 10,
          fontSize: 14,
        }}
      >
        {GUIDE.map((g, i) => (
          <li key={g} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span
              style={{
                flex: 'none',
                width: 26,
                height: 26,
                boxSizing: 'border-box',
                border: `2px solid ${C.ink}`,
                background: C.peach,
                fontFamily: JUA,
                fontSize: 14,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              {i + 1}
            </span>
            {g}
          </li>
        ))}
      </ol>

      <FilePick
        title={file ? file.name : '압축 파일 선택'}
        hint={file ? `${(file.size / 1024 / 1024).toFixed(1)}MB · 다른 파일을 고르려면 눌러 주세요` : `instagram-내보내기.zip · ${maxMb}MB 이하`}
        accept=".zip,application/zip"
        disabled={busy}
        onPick={pick}
      />

      {busy && (
        <Panel style={{ gap: 10, padding: '12px 14px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
            <span style={{ fontFamily: JUA, fontSize: 16 }}>
              {PHASE_LABEL[phase]}
              <span className="blink">...</span>
            </span>
            {phase === 'uploading' && <span style={{ fontFamily: JUA, fontSize: 16 }}>{Math.round(ratio * 100)}%</span>}
          </div>
          <Cells ratio={phase === 'uploading' ? ratio : 0.9} label={PHASE_LABEL[phase]} />
        </Panel>
      )}
      {error && <ErrorNote>{error}</ErrorNote>}

      <Notes
        items={[
          ['lock', '게시물과 사진만 꺼내고 나머지는 바로 지워요'],
          ['check', `점검할 사진은 다음 화면에서 최대 ${maxPhotos}장 골라요`],
        ]}
      />

      <Bottom>
        <Btn onClick={submit} disabled={!file || busy}>
          {busy ? `${PHASE_LABEL[phase]}...` : '올리기'}
        </Btn>
      </Bottom>
    </Frame>
  )
}
