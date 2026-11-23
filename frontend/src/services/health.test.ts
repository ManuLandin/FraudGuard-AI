import { afterEach, describe, expect, it, vi } from 'vitest'
import { getHealth } from './health'

afterEach(() => vi.useRealTimers())

describe('Cliente de salud', () => {
  it('rechaza JSON malformado con un mensaje comprensible', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('not-json')))

    await expect(getHealth()).rejects.toThrow('La API devolvió una respuesta no válida.')
  })

  it('cancela solicitudes que exceden cinco segundos', async () => {
    vi.useFakeTimers()
    let requestSignal: AbortSignal | undefined
    vi.stubGlobal('fetch', vi.fn((_url: string, options: RequestInit) => {
      requestSignal = options.signal as AbortSignal
      return new Promise((_resolve, reject) => {
        requestSignal?.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')))
      })
    }))

    const request = expect(getHealth()).rejects.toThrow('La API tardó más de 5 segundos en responder.')
    await vi.advanceTimersByTimeAsync(5000)

    await request
    expect(requestSignal?.aborted).toBe(true)
  })
})
