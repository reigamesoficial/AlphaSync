import { useEffect, useState } from 'react'
import { MessageSquare, Users, FileText, TrendingUp, Loader2 } from 'lucide-react'
import Topbar from '../components/layout/Topbar'
import StatCard from '../components/ui/StatCard'
import { PageSpinner } from '../components/ui/Spinner'
import { getDashboardSummary } from '../api/dashboard'
import type { DashboardSummary } from '../types'

const STATUS_LABELS: Record<string, string> = {
  open: 'Abertas', bot: 'Bot', assumed: 'Assumidas', closed: 'Fechadas', archived: 'Arquivadas',
  lead: 'Leads', qualified: 'Qualificados', customer: 'Clientes', inactive: 'Inativos',
  draft: 'Rascunho', confirmed: 'Confirmado', cancelled: 'Cancelado', done: 'Concluído', expired: 'Expirado',
}

function StatusBar({ data, colors }: { data: Record<string, number>; colors: Record<string, string> }) {
  const total = Object.values(data).reduce((a, b) => a + b, 0)
  if (total === 0) return <p className="text-slate-600 text-xs">Sem dados ainda</p>

  return (
    <div className="space-y-2.5 mt-3">
      {Object.entries(data)
        .filter(([, v]) => v > 0)
        .sort(([, a], [, b]) => b - a)
        .map(([key, val]) => (
          <div key={key} className="flex items-center gap-3">
            <span className="text-slate-400 text-xs w-24 shrink-0">{STATUS_LABELS[key] ?? key}</span>
            <div className="flex-1 bg-surface-700 rounded-full h-1.5 overflow-hidden">
              <div
                className={`h-full rounded-full ${colors[key] ?? 'bg-slate-500'}`}
                style={{ width: `${Math.round((val / total) * 100)}%` }}
              />
            </div>
            <span className="text-white text-xs font-medium w-6 text-right">{val}</span>
          </div>
        ))}
    </div>
  )
}

export default function Dashboard() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getDashboardSummary()
      .then(setSummary)
      .catch(() => setError('Erro ao carregar o dashboard.'))
      .finally(() => setLoading(false))
  }, [])

  const convColors: Record<string, string> = {
    open: 'bg-emerald-500', bot: 'bg-blue-500', assumed: 'bg-violet-500',
    closed: 'bg-slate-500', archived: 'bg-slate-700',
  }
  const clientColors: Record<string, string> = {
    lead: 'bg-amber-500', qualified: 'bg-sky-500', customer: 'bg-emerald-500', inactive: 'bg-slate-500',
  }
  const quoteColors: Record<string, string> = {
    draft: 'bg-amber-500', confirmed: 'bg-emerald-500', cancelled: 'bg-red-500',
    done: 'bg-sky-500', expired: 'bg-slate-500',
  }

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      <Topbar title="Dashboard" subtitle="Visão geral do sistema" />
      <main className="flex-1 overflow-y-auto p-6">
        {loading && <PageSpinner />}
        {error && (
          <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 text-red-400 text-sm">
            {error}
          </div>
        )}
        {summary && (
          <div className="space-y-6 max-w-6xl">
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              <StatCard
                label="Conversas abertas"
                value={summary.conversations.open}
                sub={`${summary.conversations.total} total`}
                icon={<MessageSquare className="w-5 h-5" />}
                accent="emerald"
              />
              <StatCard
                label="Total de clientes"
                value={summary.clients.total}
                sub={`${summary.clients.by_status.lead ?? 0} leads novos`}
                icon={<Users className="w-5 h-5" />}
                accent="sky"
              />
              <StatCard
                label="Orçamentos"
                value={summary.quotes.total}
                sub={`${summary.quotes.by_status.draft ?? 0} em rascunho`}
                icon={<FileText className="w-5 h-5" />}
                accent="amber"
              />
              <StatCard
                label="Convertidos"
                value={summary.quotes.by_status.confirmed ?? 0}
                sub="orçamentos confirmados"
                icon={<TrendingUp className="w-5 h-5" />}
                accent="brand"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="card p-5">
                <p className="text-slate-300 text-sm font-semibold">Conversas por status</p>
                <StatusBar data={summary.conversations.by_status} colors={convColors} />
              </div>
              <div className="card p-5">
                <p className="text-slate-300 text-sm font-semibold">Clientes por status</p>
                <StatusBar data={summary.clients.by_status} colors={clientColors} />
              </div>
              <div className="card p-5">
                <p className="text-slate-300 text-sm font-semibold">Orçamentos por status</p>
                <StatusBar data={summary.quotes.by_status} colors={quoteColors} />
              </div>
            </div>

            {summary.conversations.total === 0 && summary.clients.total === 0 && (
              <div className="card p-8 text-center">
                <div className="w-12 h-12 bg-surface-700 rounded-xl flex items-center justify-center mx-auto mb-4">
                  <Loader2 className="w-6 h-6 text-slate-500" />
                </div>
                <p className="text-slate-400 font-medium">Sistema pronto para operar</p>
                <p className="text-slate-600 text-sm mt-1">
                  Os dados aparecerão aqui conforme o sistema for utilizado.
                </p>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  )
}
