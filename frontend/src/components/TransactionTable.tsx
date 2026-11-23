import type { TransactionPage } from '../types/dashboard'
export function money(cents: number | string) {
  const value = BigInt(cents)
  const absolute = value < 0n ? -value : value
  const fraction = (absolute % 100n).toString().padStart(2, '0')
  const parts = new Intl.NumberFormat('es-MX', {style:'currency', currency:'MXN', minimumFractionDigits:2, maximumFractionDigits:2}).formatToParts(absolute / 100n)
  return (value < 0n ? '-' : '') + parts.map(part => part.type === 'fraction' ? fraction : part.value).join('')
}
export function TransactionTable({data, loading, page, onPage}: {data?: TransactionPage; loading: boolean; page: number; onPage: (page: number) => void}) {
  const pages = Math.max(1, Math.ceil((data?.total ?? 0)/10))
  return <><div className="table-scroll"><table><caption className="sr-only">Transacciones importadas y sus resultados de anomalía</caption><thead><tr><th scope="col">Transacción</th><th scope="col">Fecha · UTC</th><th scope="col">Monto · MXN</th><th scope="col">Puntuación</th><th scope="col">Nivel</th></tr></thead><tbody>{loading ? <tr><td colSpan={5} className="table-empty">Cargando transacciones…</td></tr> : !data?.items.length ? <tr><td colSpan={5} className="table-empty">No hay transacciones para esta selección.</td></tr> : data.items.map(t => <tr key={t.id}><td><strong>{t.transaction_id}</strong><small>Lote {t.batch_id} · {t.account_id || 'Sin cuenta'}</small></td><td>{new Date(t.timestamp).toLocaleString('es-MX',{timeZone:'UTC', dateStyle:'short',timeStyle:'short'})}</td><td className="number-cell">{money(t.amount_cents)}</td><td title={t.model_created_at ? `Modelo: ${t.model_created_at}` : undefined}>{t.anomaly_score === null ? 'Sin analizar' : `${t.anomaly_score.toFixed(1)} / 100`}</td><td><span className={`risk-badge risk-${t.risk_level || 'pendiente'}`}>{t.risk_level || 'pendiente'}</span></td></tr>)}</tbody></table></div><div className="table-pagination"><span>{data?.total ?? '—'} resultados · Página {page} de {pages}</span><div><button className="button button-secondary" disabled={loading || page <= 1} onClick={() => onPage(page-1)}>Anterior</button><button className="button button-secondary" disabled={loading || page >= pages} onClick={() => onPage(page+1)}>Siguiente</button></div></div></>
}
