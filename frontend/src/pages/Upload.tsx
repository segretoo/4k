import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { cancelUpload, errorMessage, fetchThumb, getStatus, uploadExport } from '../api/client'
import { ErrorBox, Note, Panel, PixelIcon, ProgressCells, Screen, Title, TopBar } from '../components/ui'
import { useApp } from '../state/AppState'

const GUIDE = [
  '계정 센터 → 내 정보 및 권한',
  '내 정보 내보내기 → 기기로 내보내기',
  "'미디어'만 체크, 나머지 모두 지우기",
  'JSON 형식으로 받은 .zip 올리기',
]

type Phase = 'idle' | 'uploading' | 'recommending' | 'thumbs'

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
  const label = { idle: '올리기', uploading: '올리는 중...', recommending: '점검할 사진 고르는 중...', thumbs: '사진 불러오는 중...' }[phase]

  return (
    <Screen>
      <TopBar title="지난 게시물 점검" back="/" step={[1, 3]} />
      <Title sub="인스타그램 내보내기 파일을 올려 주세요. 건강검진처럼 처음 한 번만 하면 돼요.">{'지난 게시물을\n한 번에 점검해요'}</Title>

      <Panel>
        <ol className="guide">
          {GUIDE.map((g, i) => (
            <li key={g}>
              <span className="num">{i + 1}</span>
              {g}
            </li>
          ))}
        </ol>
      </Panel>

      <label className="dropzone">
        <PixelIcon name="upload" size={32} color="var(--coral)" />
        <strong>{file ? file.name : '압축 파일 선택'}</strong>
        <span className="small">{file ? `${(file.size / 1024 / 1024).toFixed(1)}MB` : `.zip · ${maxMb}MB 이하`}</span>
        <input className="sr-only" type="file" accept=".zip,application/zip" disabled={busy} onChange={(e) => pick(e.target.files?.[0])} />
      </label>

      {busy && (
        <Panel>
          <span>{label}</span>
          <ProgressCells ratio={phase === 'uploading' ? ratio : 1} />
        </Panel>
      )}
      {error && <ErrorBox>{error}</ErrorBox>}

      <Note>게시물과 사진만 꺼내고 나머지는 바로 지워요</Note>
      <Note icon="check">점검할 사진은 다음 화면에서 최대 {maxPhotos}장 골라요</Note>

      <div className="bottom">
        <button type="button" className="btn" disabled={!file || busy} onClick={submit}>
          {label}
        </button>
      </div>
    </Screen>
  )
}
