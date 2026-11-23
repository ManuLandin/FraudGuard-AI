import { useEffect, useState } from 'react'
import { api } from '../services/api'
import type { Batch, DashboardData, ModelStatus, Summary, TransactionPage } from '../types/dashboard'

export function useDashboard(batch: string, risk: string, search: string, page: number, revision: number) {
  const [data, setData] = useState<DashboardData | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  useEffect(() => {
    const controller = new AbortController()
    setLoading(true); setError(''); setData(null)
    const params = new URLSearchParams({page: String(page), page_size: '10'})
    if (batch) params.set('batch_id', batch)
    if (risk) params.set('risk_level', risk)
    if (search) params.set('search', search)
    const summaryParams = batch ? `?batch_id=${batch}` : ''
    const options = {signal: controller.signal}
    Promise.all([
      api<Summary>(`/api/dashboard/summary${summaryParams}`, options),
      api<TransactionPage>(`/api/transactions?${params}`, options),
      api<Batch[]>('/api/transactions/batches', options),
      api<ModelStatus>('/api/ml/status', options),
    ]).then(([summary, transactions, batches, model]) => {
      if (!controller.signal.aborted) {
        if (typeof summary.total !== 'number' || !Array.isArray(transactions.items) || !Array.isArray(batches) || typeof model.ready !== 'boolean') throw new Error('Respuesta de API incompatible. Reinicia el backend actualizado.')
        setData({summary, transactions, batches, model})
      }
    }).catch((reason: unknown) => {
      if (!controller.signal.aborted) setError(reason instanceof Error ? reason.message : 'No se pudieron cargar los datos.')
    }).finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [batch, risk, search, page, revision])
  return {data, error, loading}
}
