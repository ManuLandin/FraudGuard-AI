import { API_BASE_URL } from './health'

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const timeout = AbortSignal.timeout(60000)
  const signal = options.signal ? AbortSignal.any([options.signal, timeout]) : timeout
  let response: Response
  try { response = await fetch(`${API_BASE_URL}${path}`, { ...options, signal }) }
  catch (error) {
    if (options.signal?.aborted) throw error
    throw new Error(timeout.aborted ? 'La API tardó demasiado. Vuelve a intentarlo.' : 'No se pudo conectar con la API. Comprueba que el backend esté iniciado.')
  }
  let body: unknown
  try { body = await response.json() } catch { throw new Error('La API devolvió una respuesta no válida.') }
  if (!response.ok) {
    const detail = (body as {detail?: unknown})?.detail
    throw new Error(typeof detail === 'string' ? detail : `No se pudo completar la solicitud (${response.status}). Revisa los datos e inténtalo de nuevo.`)
  }
  return body as T
}

export function batchAction(action: 'train' | 'analyze', batchId: number) {
  return api(`/api/ml/${action}`, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({batch_id: batchId})})
}
