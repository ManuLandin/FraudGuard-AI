import { Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { Summary } from '../types/dashboard'

function ChartEmpty() { return <div className="chart-empty">Importa un CSV para visualizar los datos.</div> }
export function DashboardCharts({ summary }: { summary: Summary | undefined }) {
  const hasData = Boolean(summary?.total)
  const charts = [
    {title: 'Actividad por fecha', note: 'Transacciones por día · UTC', content: <LineChart data={summary?.daily}><CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e7edf5"/><XAxis dataKey="date" tick={{fontSize: 10}} tickFormatter={v => String(v).slice(5)}/><YAxis allowDecimals={false} width={35} tick={{fontSize: 11}}/><Tooltip labelFormatter={v => `Fecha UTC: ${v}`} /><Line name="Transacciones" type="monotone" dataKey="count" stroke="#255ee8" strokeWidth={2} dot={false} isAnimationActive={false}/></LineChart>},
    {title: 'Distribución de montos', note: 'Rangos en MXN · Todas las operaciones', content: <BarChart data={summary?.amount_distribution}><CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e7edf5"/><XAxis dataKey="name" tick={{fontSize: 10}} interval={0}/><YAxis allowDecimals={false} width={30} tick={{fontSize: 11}}/><Tooltip/><Bar name="Transacciones" dataKey="count" fill="#7196e8" radius={[4,4,0,0]} isAnimationActive={false}/></BarChart>},
    {title: 'Nivel de anomalía', note: 'Alto: ≥99 · Medio: ≥95 · Bajo: <95', content: <BarChart data={summary?.distribution} layout="vertical"><CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e7edf5"/><XAxis type="number" allowDecimals={false} tick={{fontSize: 11}}/><YAxis type="category" dataKey="name" width={70} tick={{fontSize: 12}}/><Tooltip/><Bar name="Transacciones" dataKey="count" fill="#426aab" radius={[0,4,4,0]} isAnimationActive={false}/></BarChart>},
  ]
  return <section className="dashboard-charts" aria-label="Gráficas del lote completo">{charts.map(chart => <article key={chart.title} className="dashboard-panel"><h2>{chart.title}</h2><p>{chart.note}</p><div className="chart-box">{hasData ? <ResponsiveContainer width="100%" height={210} minWidth={0}>{chart.content}</ResponsiveContainer> : <ChartEmpty/>}</div><details><summary>Ver datos de la gráfica</summary><ul>{(chart.title === 'Actividad por fecha' ? summary?.daily.map(x => ({name: x.date,count:x.count})) : chart.title === 'Nivel de anomalía' ? summary?.distribution : summary?.amount_distribution)?.map(x => <li key={x.name}>{x.name}: {x.count}</li>)}</ul></details></article>)}</section>
}
