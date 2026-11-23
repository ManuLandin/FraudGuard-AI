import { ArrowUpRight, BookOpen, BrainCircuit, ChartNoAxesCombined, FileUp, House, ShieldCheck } from 'lucide-react'
import { API_BASE_URL } from '../services/health'

const upcoming = [
  { icon: FileUp, label: 'Importar CSV', href: '#importar' },
  { icon: ChartNoAxesCombined, label: 'Transacciones', href: '#transacciones' },
  { icon: BrainCircuit, label: 'Modelo de IA', href: '#modelo' },
]

export function Sidebar() {
  return (
    <aside className="sidebar" aria-label="Barra lateral">
      <a href="#inicio" className="brand" aria-label="FraudGuard AI, inicio">
        <span className="brand-mark"><ShieldCheck size={25} aria-hidden="true" /></span>
        <span>FraudGuard <span className="brand-ai">AI</span></span>
      </a>
      <nav aria-label="Navegación principal" className="main-nav">
        <a href="#inicio" aria-current="page" className="nav-active"><House size={19} aria-hidden="true" /> Dashboard</a>
        {upcoming.map(({ icon: Icon, label, href }) => (
          <a key={label} href={href} className="nav-pending">
            <Icon size={19} aria-hidden="true" />
            <span>{label}</span>

          </a>
        ))}
      </nav>
      <p className="nav-caption">Análisis local con Isolation Forest. Los resultados requieren revisión humana.</p>
      <div className="sidebar-bottom">
        <a href={`${API_BASE_URL}/docs`} target="_blank" rel="noopener noreferrer" className="docs-link">
          <BookOpen size={18} aria-hidden="true" /> Documentación API <ArrowUpRight size={15} aria-hidden="true" />
          <span className="sr-only"> (se abre en otra pestaña)</span>
        </a>
        <div className="academic-label">
          <span className="academic-avatar" aria-hidden="true">FG</span>
          <div><strong>Proyecto académico</strong><span>ESCOM · IPN</span></div>
        </div>
      </div>
    </aside>
  )
}
