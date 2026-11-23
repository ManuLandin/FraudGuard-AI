import { Check, CircleAlert, LoaderCircle, RefreshCw, Server } from 'lucide-react'
import { useHealth } from '../hooks/useHealth'

export function ConnectionStatus() {
  const { state, retry } = useHealth()
  const loading = state.status === 'loading'
  const title = loading ? 'Comprobando conexión…' : state.status === 'available' ? 'API disponible' : 'Sin conexión con la API'

  return (
    <section className="connection-panel" aria-labelledby="connection-heading" aria-busy={loading}>
      <div className="section-heading"><Server size={19} aria-hidden="true" /><h2 id="connection-heading">Estado del sistema</h2></div>
      <div className={`connection-state connection-${state.status}`} role="status" aria-live="polite" aria-atomic="true">
        <span className="connection-icon" aria-hidden="true">
          {loading ? <LoaderCircle size={24} className="spin" /> : state.status === 'available' ? <Check size={25} /> : <CircleAlert size={24} />}
        </span>
        <h3>{title}</h3>
        <p>{state.status === 'available'
          ? 'La aplicación se comunica correctamente con el backend local.'
          : state.status === 'error'
            ? state.message
            : 'Estamos verificando la disponibilidad del backend local.'}</p>
      </div>
      <dl className="connection-details">
        <div><dt>Servicio</dt><dd>FastAPI</dd></div>
        <div><dt>Comprobación</dt><dd>GET /health</dd></div>
        <div><dt>Versión de la API</dt><dd>{state.status === 'available' ? <span>Versión {state.data.version}</span> : 'Sin confirmar'}</dd></div>
      </dl>
      <button type="button" className="button button-secondary" onClick={retry} disabled={loading}>
        <RefreshCw size={16} className={loading ? 'spin' : ''} aria-hidden="true" />
        {loading ? 'Comprobando…' : 'Volver a comprobar'}
      </button>
      <p className="connection-note">Este estado comprueba la conexión. El modelo de IA aún no está implementado.</p>
    </section>
  )
}
