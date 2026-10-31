import { useEffect, useState } from 'react'
import { errorMessage, getJob } from '../api/client'
import type { JobStatus } from '../api/types'

/** 2초마다 작업 상태를 묻고, 끝나거나 실패하면 멈춘다. */
export function useJobProgress(jobId: string | null, intervalMs = 2000) {
  const [job, setJob] = useState<JobStatus | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!jobId) return
    let stopped = false
    let timer: number | undefined

    const tick = async () => {
      try {
        const st = await getJob(jobId)
        if (stopped) return
        setJob(st)
        if (st.status === 'done' || st.status === 'failed') return
      } catch (e) {
        if (stopped) return
        setError(errorMessage(e))
        return
      }
      timer = window.setTimeout(tick, intervalMs)
    }
    tick()
    return () => {
      stopped = true
      window.clearTimeout(timer)
    }
  }, [jobId, intervalMs])

  return { job, error }
}
