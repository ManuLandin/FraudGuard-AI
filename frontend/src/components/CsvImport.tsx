import { useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { Upload } from 'lucide-react'
import { api } from '../services/api'
export function CsvImport({onImported, disabled}: {onImported: (id: number) => void; disabled: boolean}) {
  const [file, setFile] = useState<File | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const input = useRef<HTMLInputElement>(null)
  async function upload(event: FormEvent) {
    event.preventDefault(); setError(''); setSuccess('')
    if (!file) { setError('Selecciona un archivo CSV.'); return }
    if (!file.name.toLowerCase().endsWith('.csv')) {setError('El archivo debe tener extensión .csv.'); return}
    if (file.size > 5*1024*1024) {setError('El archivo supera el límite de 5 MiB de la interfaz.'); return}
    const form = new FormData(); form.append('file',file)
    setBusy(true)
    try {
      const result = await api<{batch_id:number; row_count:number}>('/api/transactions/upload',{method:'POST',body:form})
      setSuccess(`Lote ${result.batch_id} guardado: ${result.row_count} transacciones. Ya puedes analizarlo.`)
      onImported(result.batch_id); setFile(null); if(input.current) input.current.value=''
    } catch(reason) {setError(reason instanceof Error ? reason.message : 'No se pudo importar el CSV.')}
    finally {setBusy(false)}
  }
  return <section id="importar" className="dashboard-panel import-panel"><div><h2>Importa tus transacciones</h2><p>CSV UTF-8 · Hasta 5 MiB · Solo datos sintéticos</p></div><form onSubmit={upload}><label htmlFor="csv-file" className="sr-only">Archivo CSV</label><input ref={input} id="csv-file" type="file" accept=".csv,text/csv" disabled={busy || disabled} onChange={e => {setFile(e.target.files?.[0] || null); setError('');setSuccess('')}}/><button className="button button-primary" disabled={busy || disabled || !file}><Upload size={16} aria-hidden="true"/>{busy ? 'Importando…' : 'Importar CSV'}</button></form><details><summary>Formato requerido</summary><p>Columnas: transaction_id, amount y timestamp (ISO 8601 con zona). Opcionales: account_id y label. También se acepta el demo con user_id, transaction_type, merchant_category, location e is_anomaly (etiqueta de referencia, no predicción). Montos positivos con punto decimal. No uses datos bancarios reales. La previsualización de la importación corresponde a registros ya guardados.</p></details>{error && <p role="alert" className="error-message">{error}</p>}{success && <p role="status" className="success-message">{success}</p>}</section>
}
