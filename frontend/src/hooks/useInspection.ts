import { useState, useEffect, useCallback } from 'react'
import type { Inspection, InspectionCreate } from '@/types'
import { getInspection, getInspections, createInspection } from '@/services/api'

export function useInspection(id?: string) {
  const [inspection, setInspection] = useState<Inspection | null>(null)
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  const fetchInspection = useCallback(async (inspectionId: string) => {
    setLoading(true)
    setError(null)
    try {
      const data = await getInspection(inspectionId)
      setInspection(data)
    } catch (err: any) {
      setError(err.message || 'Failed to fetch inspection')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (id) {
      fetchInspection(id)
    }
  }, [id, fetchInspection])

  return { inspection, loading, error, refetch: () => id && fetchInspection(id) }
}

export function useInspectionsList(initialPage = 1, limit = 10) {
  const [inspections, setInspections] = useState<Inspection[]>([])
  const [total, setTotal] = useState<number>(0)
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  const fetchList = useCallback(async (page: number) => {
    setLoading(true)
    setError(null)
    try {
      const data = await getInspections(page, limit)
      setInspections(data.items)
      setTotal(data.total)
    } catch (err: any) {
      setError(err.message || 'Failed to load inspections')
    } finally {
      setLoading(false)
    }
  }, [limit])

  useEffect(() => {
    fetchList(initialPage)
  }, [initialPage, fetchList])

  return { inspections, total, loading, error, refetch: () => fetchList(initialPage) }
}
