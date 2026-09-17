import { useState, useEffect, useRef } from 'react'
import type { ProcessingStatus } from '@/types'
import { getProcessingStatus } from '@/services/api'

export function useProcessing(inspectionId: string, enabled = true, intervalMs = 1500) {
  const [status, setStatus] = useState<ProcessingStatus | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [isDone, setIsDone] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const timerRef = useRef<any>(null)

  useEffect(() => {
    if (!enabled || !inspectionId) return

    const poll = async () => {
      try {
        const res = await getProcessingStatus(inspectionId)
        setStatus(res)
        if (res.overall_progress >= 100) {
          setIsDone(true)
          clearInterval(timerRef.current)
        }
      } catch (err: any) {
        // Continue simulation if endpoint not ready
      } finally {
        setLoading(false)
      }
    }

    poll()
    timerRef.current = setInterval(poll, intervalMs)

    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [inspectionId, enabled, intervalMs])

  return { status, loading, isDone, error }
}
