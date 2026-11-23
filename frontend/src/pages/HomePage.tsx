import { ArrowDownToLine, ArrowRight, Check, CheckCheck, FileSpreadsheet, FlaskConical, Info, ScanLine, ShieldCheck } from 'lucide-react'
import { ConnectionStatus } from '../components/ConnectionStatus'

const workflow = [
  { icon: FileSpreadsheet, title: 'Importa tus datos', description: 'Archivos CSV validados antes de cada análisis.' },
  { icon: ScanLine, title: 'Identifica anomalías', description: 'Isolation Forest encontrará patrones atípicos.' },
  { icon: ArrowDownToLine, title: 'Explora los resultados', description: 'Indicadores, gráficas y transacciones en un solo lugar.' },
]

export function HomePage() {
  return (
    <>
      <header className="topbar">
        <span className="topbar-location">Espacio de trabajo <span aria-hidden="true">/</span> <strong>Inicio</strong></span>
        <span className="local-label"><span aria-hidden="true" /> Entorno local</span>
      </header>
      <main id="inicio" tabIndex={-1} className="main-content">
        <div className="page-heading">
          <div><h1>Vista general</h1><p>Tu espacio para explorar anomalías en transacciones.</p></div>
          <span className="phase-label"><FlaskConical size={15} aria-hidden="true" /> Fase 1 · Base del proyecto</span>
        </div>

        <div className="overview-grid">
          <section className="welcome-panel" aria-labelledby="welcome-heading">
            <span className="welcome-symbol" aria-hidden="true"><ShieldCheck size={34} strokeWidth={1.5} /></span>
            <h2 id="welcome-heading">El análisis empieza<br />con una buena base.</h2>
            <p>Bienvenido a FraudGuard AI. Estamos construyendo una forma clara de explorar operaciones atípicas con Machine Learning.</p>
            <a className="button button-primary" href="#recorrido">Conoce el recorrido <ArrowRight size={17} aria-hidden="true" /></a>
            <div className="welcome-footer"><CheckCheck size={17} aria-hidden="true" /> Ejecución local <span aria-hidden="true">·</span> Sin servicios de pago</div>
          </section>
          <ConnectionStatus />
        </div>

        <section id="recorrido" className="workflow-section" aria-labelledby="workflow-heading">
          <div className="workflow-heading"><h2 id="workflow-heading">De tus datos a una mejor perspectiva</h2><span>Próximas fases</span></div>
          <p className="section-description">Este será el recorrido de análisis. La carga de archivos y el modelo aún no están disponibles.</p>
          <ol className="workflow-list">
            {workflow.map(({ icon: Icon, title, description }, index) => (
              <li key={title}>
                <div className="workflow-step"><Icon size={22} aria-hidden="true" /><span>Paso {index + 1}</span></div>
                <h3>{title}</h3><p>{description}</p>
              </li>
            ))}
          </ol>
        </section>

        <section className="scope-strip" aria-labelledby="scope-heading">
          <div className="scope-intro"><span className="scope-icon"><Check size={19} aria-hidden="true" /></span><div><h2 id="scope-heading">En esta primera fase</h2><p>El punto de partida del proyecto.</p></div></div>
          <ul><li>Estructura modular</li><li>API de estado</li><li>Interfaz conectada</li></ul>
        </section>

        <div className="responsible-note"><Info size={18} aria-hidden="true" /><p><strong>Anomalías, no fraudes confirmados.</strong> Una operación atípica requiere revisión. Las futuras puntuaciones no representarán probabilidades de fraude. Las demostraciones utilizarán datos sintéticos.</p></div>
        <footer className="page-footer"><span>FraudGuard AI</span><span>Ingeniería en Sistemas Computacionales · ESCOM-IPN</span></footer>
      </main>
    </>
  )
}
