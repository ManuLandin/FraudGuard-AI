import type { HealthResponse } from '../types/api'

export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL?.trim() || 'http://127.0.0.1:8000').replace(/\/+$/, '')

function isHealthResponse(value: unknown): value is HealthResponse {
  return typeof value === 'object' && value !== null
    && 'status' in value && value.status === 'ok'
    && 'service' in value && value.service === 'FraudGuard AI'
    && 'version' in value && typeof value.version === 'string' && value.version.trim().length > 0
}

export async function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  signal?.throwIfAborted()
  const controller = new AbortController()
  const cancel = () => controller.abort()
  signal?.addEventListener('abort', cancel, { once: true })
  let timedOut = false
  const timeout = setTimeout(() => {
    timedOut = true
    controller.abort()
  }, 5000)

  try {
    const response = await fetch(`${API_BASE_URL}/health`, {
      signal: controller.signal,
      headers: { Accept: 'application/json' },
      cache: 'no-store',
    })
    if (!response.ok) {
      throw new Error(`La API respondió con el código ${response.status}. Vuelve a comprobar la conexión.`)
    }
    let data: unknown
    try {
      data = await response.json()
    } catch (error) {
      if (controller.signal.aborted) throw error
      throw new Error('La API devolvió una respuesta no válida.')
    }
    if (!isHealthResponse(data)) throw new Error('La API devolvió una respuesta no válida.')
    return data
  } catch (error) {
    if (timedOut) throw new Error('La API tardó más de 5 segundos en responder.')
    if (signal?.aborted) throw error
    if (error instanceof TypeError) {
      throw new Error('No se pudo contactar con la API. Comprueba que el backend esté iniciado y vuelve a intentarlo.')
    }
    throw error
  } finally {
    clearTimeout(timeout)
    signal?.removeEventListener('abort', cancel)
  }
}
