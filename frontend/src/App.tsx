import { Sidebar } from './components/Sidebar'
import { DashboardPage } from './pages/DashboardPage'

export default function App() {
  return (
    <div className="app-shell">
      <a className="skip-link" href="#inicio">Saltar al contenido</a>
      <Sidebar />
      <div className="workspace"><DashboardPage /></div>
    </div>
  )
}
