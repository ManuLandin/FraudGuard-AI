import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { ConnectionStatus as App } from './components/ConnectionStatus'

const health = { status: 'ok', service: 'FraudGuard AI', version: '0.1.0' }

describe('Estado de conexión de la API', () => {
  it('indica que la comprobación está pendiente', () => {
    vi.stubGlobal('fetch', vi.fn(() => new Promise(() => {})))

    render(<App />)

    expect(screen.getByText('Comprobando conexión…')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Comprobando…' })).toBeDisabled()
  })

  it('muestra disponibilidad solo después de una respuesta válida', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify(health))))

    render(<App />)

    expect(await screen.findByText('API disponible')).toBeInTheDocument()
    expect(screen.getByText('Versión 0.1.0')).toBeInTheDocument()
  })

  it('permite recuperar la conexión después de un error de red', async () => {
    const fetchMock = vi.fn()
      .mockRejectedValueOnce(new TypeError('Failed to fetch'))
      .mockResolvedValueOnce(new Response(JSON.stringify(health)))
    vi.stubGlobal('fetch', fetchMock)
    const user = userEvent.setup()

    render(<App />)

    expect(await screen.findByText('Sin conexión con la API')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Volver a comprobar' }))
    expect(await screen.findByText('API disponible')).toBeInTheDocument()
  })

  it('rechaza una respuesta que no cumple el contrato de salud', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{"status":"error"}')))

    render(<App />)

    expect(await screen.findByText('Sin conexión con la API')).toBeInTheDocument()
    expect(screen.getByText(/La API devolvió una respuesta no válida/)).toBeInTheDocument()
    expect(screen.queryByText('API disponible')).not.toBeInTheDocument()
  })

  it('informa un error HTTP sin mostrar disponibilidad', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('Error', { status: 503 })))

    render(<App />)

    expect(await screen.findByText(/La API respondió con el código 503/)).toBeInTheDocument()
    expect(screen.queryByText('API disponible')).not.toBeInTheDocument()
  })

  it('cancela la consulta al abandonar la página', async () => {
    const fetchMock = vi.fn(() => new Promise(() => {}))
    vi.stubGlobal('fetch', fetchMock)

    const view = render(<App />)
    await waitFor(() => expect(fetchMock).toHaveBeenCalled())
    const signal = (fetchMock.mock.calls[0] as unknown as [string, RequestInit])[1].signal
    view.unmount()

    expect(signal?.aborted).toBe(true)
  })
})
