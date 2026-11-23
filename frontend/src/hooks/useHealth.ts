import { useEffect, useState } from 'react'
import { getHealth } from '../services/health'
import type { HealthResponse } from '../types/api'

export type HealthState =
  | { status: 'loading' }
  | { status: 'available'; data: HealthResponse }
  | { status: 'error'; message: string }

export function useHealth() {
  const [state, setState] = useState<HealthState>({ status: 'loading' })
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    setState({ status: 'loading' })
    getHealth(controller.signal).then(
      (data) => {
        if (!controller.signal.aborted) setState({ status: 'available', data })
      },
      (error: unknown) => {
        if (!controller.signal.aborted) {
          setState({
            status: 'error',
            message: error instanceof Error ? error.message : 'No se pudo comprobar la conexión. Vuelve a intentarlo.',
          })
        }
      },
    )
    return () => controller.abort()
  }, [attempt])

  return { state, retry: () => setAttempt((current) => current + 1) }
}
