import { useEffect, useState } from 'react'
import { Building2, Users, MessageSquare, FileText, CalendarDays, TrendingUp } from 'lucide-react'
import api from '../../api/client'

interface GlobalMetrics {
  companies: { total: number; active: number }
  users: { total: number }
  conversations: { total: number }
  quotes: { total: number }
  appointments: { total: number }
}

export default function AdminDashboard() {
  const [metrics, setMetrics] = useState<GlobalMetrics | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get<GlobalMetrics>('/admin/metrics')
      .then(r => setMetrics(r.data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const cards = metrics
    ? [
        { label: 'Empresas ativas', value: metrics.companies.active, total: metrics.companies.total, icon: Building2, color: 'text-violet-400', bg: 'bg-violet-600/10' },
        { label: 'Usuários',         value: metrics.users.total,         total: null, icon: Users,        color: 'text-blue-400',   bg: 'bg-blue-600/10' },
        { label: 'Conversas',        value: metrics.conversations.total, total: null, icon: MessageSquare, color: 'text-sky-400',    bg: 'bg-sky-600/10' },
        { label: 'Orçamentos',       value: metrics.quotes.total,        total: null, icon: FileText,      color: 'text-amber-400',  bg: 'bg-amber-600/10' },
        { label: 'Agendamentos',     value: metrics.appointments.total,  total: null, icon: CalendarDays,  color: 'text-emerald-400', bg: 'bg-emerald-600/10' },
      ]
    : []

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-white">Visão Geral da Plataforma</h1>
        <p className="text-slate-400 text-sm mt-1">Métricas globais do AlphaSync</p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-40">
          <div className="w-7 h-7 border-2 border-violet-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {cards.map(({ label, value, total, icon: Icon, color, bg }) => (
            <div key={label} className="card p-5">
              <div className="flex items-center justify-between mb-3">
                <p className="text-slate-400 text-sm">{label}</p>
                <div className={`w-8 h-8 rounded-lg ${bg} flex items-center justify-center`}>
                  <Icon className={`w-4 h-4 ${color}`} />
                </div>
              </div>
              <p className={`text-2xl font-bold ${color}`}>{value.toLocaleString('pt-BR')}</p>
              {total !== null && (
                <p className="text-slate-500 text-xs mt-1">de {total.toLocaleString('pt-BR')} total</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
