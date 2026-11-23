import { lazy, Suspense, useEffect, useState } from 'react'
import { Activity, AlertTriangle, ArrowUpRight, Database, RefreshCw, ScanLine, Wallet } from 'lucide-react'
const DashboardCharts = lazy(() => import('../components/DashboardCharts').then(module => ({default: module.DashboardCharts})))
import { CsvImport } from '../components/CsvImport'
import { TransactionTable, money } from '../components/TransactionTable'
import { useDashboard } from '../hooks/useDashboard'
import { batchAction } from '../services/api'

export function DashboardPage() {
  const [batch, setBatch] = useState('')
  const [risk, setRisk] = useState('')
  const [search, setSearch] = useState('')
  const [query, setQuery] = useState('')
  const [page, setPage] = useState(1)
  const [revision, refresh] = useState(0)
  const [busy, setBusy] = useState('')
  const [message, setMessage] = useState('')
  const [actionError, setActionError] = useState('')
  const {data, loading, error} = useDashboard(batch, risk, query, page, revision)
  useEffect(() => {if (search === query) return; const timer=setTimeout(() => {setQuery(search);setPage(1)},300);return () => clearTimeout(timer)},[search, query])
  async function action(kind: 'train' | 'analyze') {
    if (!batch) return
    setBusy(kind); setActionError(''); setMessage('')
    try {await batchAction(kind,Number(batch));setPage(1);setMessage(kind==='train' ? 'Modelo entrenado. Selecciona un lote posterior para analizar; este ajuste no mide precisión.' : 'Análisis guardado. Resultados actualizados.');refresh(x=>x+1)}
    catch(reason) {setActionError(reason instanceof Error ? reason.message : 'No se pudo completar la operación.')}
    finally {setBusy('')}
  }
  const summary=data?.summary
  const kpis=[{label:'Transacciones analizadas',value:summary?.analyzed.toLocaleString('es-MX') ?? '—',note:summary ? `${summary.total} importadas · ${summary.pending} pendientes` : 'Consultando API',icon:Database}, {label:'Anomalías identificadas',value:summary?.anomalies.toLocaleString('es-MX') ?? '—',note:'Puntuación igual o superior a 99',icon:AlertTriangle}, {label:'Porcentaje de anomalías',value:summary?.anomaly_percentage == null ? '—' : `${summary.anomaly_percentage.toFixed(1)} %`,note:'Sobre transacciones analizadas',icon:Activity}, {label:'Monto importado',value:summary ? money(summary.amount_cents) : '—',note:'Total del lote · MXN',icon:Wallet}]
  return <><header className="topbar"><span className="topbar-location">Espacio de trabajo <span>/</span><strong>Dashboard</strong></span><span className="local-label"><span/>Datos de la API local</span></header><main id="inicio" tabIndex={-1} className="main-content dashboard-content"><div className="page-heading"><div><h1>Dashboard de anomalías</h1><p>Una perspectiva clara de tus transacciones y sus patrones atípicos.</p></div><button className="button button-secondary refresh-button" disabled={loading || !!busy} onClick={()=>refresh(x=>x+1)}><RefreshCw size={15}/>Actualizar</button></div>
  <div className="synthetic-banner"><ScanLine size={18}/><p><strong>Uso académico · Solo datos sintéticos.</strong> Los datos y resultados se consultan en la API real. No hay valores simulados en esta pantalla.</p></div>
  <div className="dataset-toolbar"><label>Lote de análisis<select value={batch} disabled={!!busy || loading} onChange={e=>{setBatch(e.target.value);setPage(1);setMessage('')}}><option value="">Todos los lotes</option>{data?.batches.map(b=><option key={b.id} value={b.id}>#{b.id} · {b.filename} ({b.row_count})</option>)}</select></label><p>Los indicadores y gráficas reflejan el lote completo.<br/>Los filtros inferiores se aplican a la tabla.</p></div>
  {error && <div role="alert" className="error-message">{error} <button onClick={()=>refresh(x=>x+1)}>Reintentar carga</button></div>}
  <section className="kpi-grid" aria-label="Indicadores del lote" aria-busy={loading}>{kpis.map(({label,value,note,icon:Icon})=><article className="kpi-card" key={label}><div><span>{label}</span><Icon size={18} aria-hidden="true"/></div><strong>{value}</strong><p>{note}</p></article>)}</section>
  <Suspense fallback={<p role="status">Cargando gráficas…</p>}><DashboardCharts summary={summary}/></Suspense>
  <CsvImport disabled={!!busy} onImported={id=>{setBatch(String(id));setPage(1);setRisk('');setSearch('');refresh(x=>x+1)}}/>
  <section id="modelo" className="dashboard-panel model-strip"><div><h2><ScanLine size={18}/>Isolation Forest</h2><p>{loading ? 'Consultando modelo…' : data?.model.ready ? `Modelo disponible · ${data.model.fit_rows} filas de ajuste · ${data.model.calibration_rows} de calibración` : 'Sin modelo compatible. Importa un lote de referencia de al menos 80 filas.'}</p><small>Entrenar reemplaza el modelo local. Para evaluar, usa datos posteriores separados. Los resultados anteriores conservan la fecha de su modelo.</small></div><div className="model-actions"><button className="button button-secondary" disabled={!batch || loading || !!busy} onClick={()=>action('train')}>{busy==='train' ? 'Entrenando…' : 'Entrenar con este lote'}</button><button className="button button-primary" disabled={!batch || !data?.model.ready || loading || !!busy} onClick={()=>action('analyze')}>{busy==='analyze' ? 'Analizando…' : 'Analizar lote'}<ArrowUpRight size={15}/></button></div>{!batch && <small>Selecciona un lote para entrenar o analizar.</small>}{actionError && <p role="alert" className="error-message">{actionError}</p>}{message && <p role="status" className="success-message">{message}</p>}</section>
  <section id="transacciones" className="dashboard-panel transactions-panel"><div className="table-heading"><div><h2>Transacciones</h2><p>Explora operaciones y niveles orientativos de anomalía.</p></div><div className="table-filters"><label>Buscar<input type="search" value={search} maxLength={100} disabled={!!busy} placeholder="Identificador o cuenta" onChange={e=>setSearch(e.target.value)}/></label><label>Nivel de anomalía<select value={risk} disabled={!!busy} onChange={e=>{setRisk(e.target.value);setPage(1)}}><option value="">Todos los niveles</option><option value="alto">Alto</option><option value="medio">Medio</option><option value="bajo">Bajo</option><option value="pendiente">Sin analizar</option></select></label></div></div><TransactionTable data={data?.transactions} loading={loading} page={page} onPage={setPage}/></section>
  <p className="dashboard-disclaimer"><strong>Anomalías, no fraudes confirmados.</strong> La puntuación es un percentil relativo a la referencia del modelo, no una probabilidad de fraude. Alto ≥99, medio ≥95, bajo &lt;95. Requiere revisión humana.</p><footer className="page-footer"><span>FraudGuard AI</span><span>ESCOM · IPN · Análisis académico</span></footer></main></>
}
