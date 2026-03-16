import { useEffect, useState, useCallback } from 'react'
import {
  Building2, Users, MessageSquare, FileText, Calendar,
  TrendingUp, RefreshCw, CheckCircle2, XCircle, BarChart3,
} from 'lucide-react'
import { getAdminMetrics } from '../../api/admin'

interface Metrics {
  companies: { total: number; active: number }
  users: { total: number }
  conversations: { total: number }
  quotes: { total: number }
  appointments: { total: number }
}

interface Toast { msg: string; type: 'success' | 'error' }

interface MetricCard {
  label: string
  value: number
  sub?: string
  color: string
  bg: string
  icon: React.ElementType
}

function KpiCard({ label, value, sub, color, bg, icon: Icon }: MetricCard) {
  return (
    <div className="card p-5 flex flex-col gap-3">
      <div className="flex items-start justify-between">
        <div className={`w-10 h-10 ${bg} rounded-xl flex items-center justify-center`}>
          <Icon className={`w-5 h-5 ${color}`} />
        </div>
        <TrendingUp className="w-3.5 h-3.5 text-slate-600" />
      </div>
      <div>
        <p className={`text-3xl font-bold tracking-tight ${color}`}>{value.toLocaleString('pt-BR')}</p>
        <p className="text-white text-sm font-medium mt-0.5">{label}</p>
        {sub && <p className="text-slate-500 text-xs mt-0.5">{sub}</p>}
      </div>
    </div>
  )
}

export default function AdminMetrics() {
  const [metrics, setMetrics] = useState<Metrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [toast, setToast] = useState<Toast | null>(null)
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null)

  function showToast(msg: string, type: Toast['type']) {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 3500)
  }

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const data = await getAdminMetrics() as Metrics
      setMetrics(data)
      setLastRefresh(new Date())
    } catch {
      showToast('Erro ao carregar métricas', 'error')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const cards: MetricCard[] = metrics ? [
    {
      label: 'Empresas',
      value: metrics.companies.total,
      sub: `${metrics.companies.active} ativas`,
      color: 'text-violet-400',
      bg: 'bg-violet-500/15',
      icon: Building2,
    },
    {
      label: 'Usuários',
      value: metrics.users.total,
      color: 'text-blue-400',
      bg: 'bg-blue-500/15',
      icon: Users,
    },
    {
      label: 'Conversas',
      value: metrics.conversations.total,
      color: 'text-emerald-400',
      bg: 'bg-emerald-500/15',
      icon: MessageSquare,
    },
    {
      label: 'Orçamentos',
      value: metrics.quotes.total,
      color: 'text-amber-400',
      bg: 'bg-amber-500/15',
      icon: FileText,
    },
    {
      label: 'Agendamentos',
      value: metrics.appointments.total,
      color: 'text-rose-400',
      bg: 'bg-rose-500/15',
      icon: Calendar,
    },
  ] : []

  const activeRate = metrics
    ? metrics.companies.total > 0
      ? Math.round((metrics.companies.active / metrics.companies.total) * 100)
      : 0
    : 0

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      {/* Toast */}
      {toast && (
        <div className={`fixed top-4 right-4 z-50 flex items-center gap-2 px-4 py-3 rounded-xl shadow-xl text-sm font-medium backdrop-blur border ${
          toast.type === 'error' ? 'bg-red-500/20 text-red-300 border-red-500/30' : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
        }`}>
          {toast.type === 'error' ? <XCircle className="w-4 h-4" /> : <CheckCircle2 className="w-4 h-4" />}
          {toast.msg}
        </div>
      )}

      {/* Sticky header */}
      <div className="sticky top-0 z-10 bg-surface-900/80 backdrop-blur border-b border-surface-700 px-6 py-4 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-violet-600/20 rounded-lg flex items-center justify-center">
            <BarChart3 className="w-4 h-4 text-violet-400" />
          </div>
          <div>
            <h1 className="text-white font-semibold text-base">Métricas da Plataforma</h1>
            <p className="text-slate-500 text-xs">
              {lastRefresh
                ? `Atualizado às ${lastRefresh.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}`
                : 'Visão geral de toda a plataforma'}
            </p>
          </div>
        </div>
        <button onClick={load} disabled={loading} className="btn-secondary flex items-center gap-2 text-sm">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Atualizar
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {loading ? (
          <div className="flex items-center justify-center h-48">
            <div className="w-8 h-8 border-2 border-violet-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : metrics ? (
          <>
            {/* KPI cards */}
            <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
              {cards.map(card => <KpiCard key={card.label} {...card} />)}
            </div>

            {/* Summary card */}
            <div className="card p-6">
              <h3 className="text-white font-semibold text-sm mb-5 flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-violet-400" /> Resumo Operacional
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {/* Active rate */}
                <div className="rounded-xl bg-surface-900 border border-surface-600 p-4">
                  <p className="text-slate-500 text-xs mb-2">Taxa de empresas ativas</p>
                  <div className="flex items-end gap-2">
                    <span className="text-2xl font-bold text-white">{activeRate}%</span>
                    <span className="text-slate-500 text-xs mb-0.5">{metrics.companies.active}/{metrics.companies.total}</span>
                  </div>
                  <div className="mt-3 h-1.5 bg-surface-700 rounded-full overflow-hidden">
                    <div className="h-full bg-violet-500 rounded-full transition-all" style={{ width: `${activeRate}%` }} />
                  </div>
                </div>

                {/* Quotes per company */}
                <div className="rounded-xl bg-surface-900 border border-surface-600 p-4">
                  <p className="text-slate-500 text-xs mb-2">Orçamentos por empresa</p>
                  <div className="flex items-end gap-2">
                    <span className="text-2xl font-bold text-white">
                      {metrics.companies.total > 0
                        ? (metrics.quotes.total / metrics.companies.total).toFixed(1)
                        : '—'}
                    </span>
                    <span className="text-slate-500 text-xs mb-0.5">média</span>
                  </div>
                  <p className="text-slate-600 text-xs mt-2">
                    {metrics.quotes.total.toLocaleString('pt-BR')} orçamentos no total
                  </p>
                </div>

                {/* Conversations per company */}
                <div className="rounded-xl bg-surface-900 border border-surface-600 p-4">
                  <p className="text-slate-500 text-xs mb-2">Conversas por empresa</p>
                  <div className="flex items-end gap-2">
                    <span className="text-2xl font-bold text-white">
                      {metrics.companies.total > 0
                        ? (metrics.conversations.total / metrics.companies.total).toFixed(1)
                        : '—'}
                    </span>
                    <span className="text-slate-500 text-xs mb-0.5">média</span>
                  </div>
                  <p className="text-slate-600 text-xs mt-2">
                    {metrics.conversations.total.toLocaleString('pt-BR')} conversas no total
                  </p>
                </div>
              </div>
            </div>

            {/* Data table */}
            <div className="card overflow-hidden">
              <div className="px-5 py-4 border-b border-surface-600">
                <p className="text-white font-semibold text-sm">Totais da plataforma</p>
              </div>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-surface-600 bg-surface-900/50">
                    <th className="text-left px-5 py-3 text-slate-400 text-xs font-medium">Entidade</th>
                    <th className="text-right px-5 py-3 text-slate-400 text-xs font-medium">Total</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-700">
                  {[
                    { label: 'Empresas cadastradas', value: metrics.companies.total, icon: Building2, color: 'text-violet-400' },
                    { label: 'Empresas ativas', value: metrics.companies.active, icon: CheckCircle2, color: 'text-emerald-400' },
                    { label: 'Usuários', value: metrics.users.total, icon: Users, color: 'text-blue-400' },
                    { label: 'Conversas WhatsApp', value: metrics.conversations.total, icon: MessageSquare, color: 'text-emerald-400' },
                    { label: 'Orçamentos gerados', value: metrics.quotes.total, icon: FileText, color: 'text-amber-400' },
                    { label: 'Agendamentos', value: metrics.appointments.total, icon: Calendar, color: 'text-rose-400' },
                  ].map(({ label, value, icon: Icon, color }) => (
                    <tr key={label} className="hover:bg-surface-700/30 transition-colors">
                      <td className="px-5 py-3.5">
                        <span className="flex items-center gap-2.5 text-slate-300">
                          <Icon className={`w-4 h-4 ${color}`} />
                          {label}
                        </span>
                      </td>
                      <td className="px-5 py-3.5 text-right">
                        <span className={`text-sm font-bold ${color}`}>{value.toLocaleString('pt-BR')}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        ) : (
          <div className="flex flex-col items-center justify-center h-40 gap-3">
            <BarChart3 className="w-8 h-8 text-slate-600" />
            <p className="text-slate-400 text-sm">Não foi possível carregar as métricas.</p>
            <button onClick={load} className="btn-secondary text-sm">Tentar novamente</button>
          </div>
        )}
      </div>
    </div>
  )
}
