import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi } from 'vitest'
import App from './App'
vi.mock('./components/DashboardCharts', () => ({ DashboardCharts: () => null }))
const summary = {total:1, analyzed:1, pending:0, anomalies:1, anomaly_percentage:100, amount_cents:'12000', distribution:[], daily:[], amount_distribution:[]}
function server() {
  const fetchMock = vi.fn((input: string, options?: RequestInit) => {
    const path=String(input)
    if (path.endsWith('/upload')) return Promise.resolve(new Response(JSON.stringify({detail:'Columnas inválidas.'}),{status:422}))
    if(path.includes('/summary')) return Promise.resolve(new Response(JSON.stringify(summary)))
    if(path.includes('/batches')) return Promise.resolve(new Response(JSON.stringify([{id:1,filename:'synthetic.csv',row_count:1,created_at:'2026-01-01'}])))
    if(path.includes('/status')) return Promise.resolve(new Response(JSON.stringify({ready:true,fit_rows:180,calibration_rows:60})))
    if(options?.method==='POST') return Promise.resolve(new Response('{}'))
    return Promise.resolve(new Response(JSON.stringify({items:[{id:1,batch_id:1,transaction_id:'demo-api',amount_cents:12000,timestamp:'2026-01-01T12:00:00Z',account_id:null,anomaly_score:100,risk_level:'alto',model_created_at:'2026-01-01'}],total:21,page:1,page_size:10})))
  })
  vi.stubGlobal('fetch',fetchMock)
  return fetchMock
}
describe('Dashboard conectado', () => {
  it('muestra registros de la respuesta y solicita filtros/páginas en servidor', async () => {
    const fetchMock=server(); const user=userEvent.setup();render(<App/>);
    expect(await screen.findByText('demo-api')).toBeInTheDocument()
    await user.selectOptions(screen.getByLabelText('Nivel de anomalía'),'alto')
    await waitFor(()=>expect(fetchMock.mock.calls.some(([url])=>url.includes('risk_level=alto'))).toBe(true))
    await screen.findByText('demo-api')
    await user.click(screen.getByRole('button',{name:'Siguiente'}))
    await waitFor(()=>expect(fetchMock.mock.calls.some(([url])=>url.includes('page=2'))).toBe(true))
  })
  it('conserva el error de validación del CSV sin inventar resultados',async()=>{
    server();const user=userEvent.setup();render(<App/>);await screen.findByText('demo-api')
    await user.upload(screen.getByLabelText('Archivo CSV'), new File(['bad'], 'invalid.csv',{type:'text/csv'}))
    await user.click(screen.getByRole('button',{name:'Importar CSV'}))
    expect(await screen.findByRole('alert')).toHaveTextContent('Columnas inválidas.')
  })
  it('regresa a la primera página cuando el análisis reduce los resultados filtrados',async()=>{
    const fetchMock=server(); const original=fetchMock.getMockImplementation()!;let analyzed=false
    fetchMock.mockImplementation((input,options)=>{
      if(String(input).includes('/ml/analyze')) analyzed=true
      if(analyzed && String(input).includes('/api/transactions?')) return Promise.resolve(new Response(JSON.stringify({items:[],total:0,page:1,page_size:10})))
      return original(input,options)
    })
    const user=userEvent.setup();render(<App/>);await screen.findByText('demo-api')
    await new Promise(resolve => setTimeout(resolve,350))
    await user.selectOptions(screen.getByLabelText('Lote de análisis'),'1');await screen.findByText('demo-api')
    await user.selectOptions(screen.getByLabelText('Nivel de anomalía'),'pendiente');await screen.findByText('demo-api')
    await user.click(screen.getByRole('button',{name:'Siguiente'}));await screen.findByText(/Página 2 de 3/)
    await user.click(screen.getByRole('button',{name:'Analizar lote'}))
    expect(await screen.findByText(/Página 1 de 1/)).toBeInTheDocument()
  })

  it('informa la desconexión y ofrece reintento',async()=>{
    vi.stubGlobal('fetch',vi.fn().mockRejectedValue(new TypeError('Failed to fetch')));render(<App/>);
    expect(await screen.findByRole('alert')).toHaveTextContent('No se pudo conectar')
    expect(screen.getByRole('button',{name:'Reintentar carga'})).toBeInTheDocument()
    expect(screen.queryByText('demo-api')).not.toBeInTheDocument()
  })
})
