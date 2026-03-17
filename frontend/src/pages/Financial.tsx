import { useState, useEffect } from 'react'
import Topbar from '../components/layout/Topbar'
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell,
} from 'recharts'
import { TrendingUp, TrendingDown, DollarSign, FileText, Users, CheckCircle } from 'lucide-react'
import api from '../api/client'

interface MonthlyData { month: string; revenue: number; quotes: number }
interface TopClient { client_name: string; total: number; quotes_count: number }
interface FinancialData {
  revenue_total: number
  revenue_last_month: number
  quotes_confirmed: number
  quotes_done: number
  clients_active: number
  conversion_rate: number
  monthly: MonthlyData[]
  top_clients: TopClient[]
}

const BRAND = '#6366f1'
const EMERALD = '#10b981'

function pct(a: number, b: number) {
  if (!b) return 0
  return ((a - b) / b) * 100
}

function fmt(v: number) {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }).format(v)
}

interface StatCardProps {
  label: string
  value: string
  sub?: string
  positive?: boolean
  icon: React.ReactNode
  color?: string
}
function StatCard({ label, value, sub, positive, icon, color = 'bg-brand-600/15 text-brand-400' }: StatCardProps) {
  return (
    <div className="card p-5 flex items-start gap-4 animate-fade-in">
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${color}`}>
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-slate-400 text-xs font-medium mb-1">{label}</p>
        <p className="text-white text-2xl font-bold truncate">{value}</p>
        {sub !== undefined && (
          <p className={`text-xs mt-1 flex items-center gap-1 ${positive === undefined ? 'text-slate-500' : positive ? 'text-emerald-400' : 'text-red-400'}`}>
            {positive !== undefined && (positive ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />)}
            {sub}
          </p>
        )}
      </div>
    </div>
  )
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload?.length) {
    return (
      <div className="bg-surface-700 border border-surface-500 rounded-lg px-3 py-2 text-xs shadow-xl">
        <p className="text-slate-400 mb-1">{label}</p>
        {payload.map((p: any) => (
          <p key={p.name} style={{ color: p.color }} className="font-semibold">
            {p.name === 'revenue' ? fmt(p.value) : `${p.value} orçamentos`}
          </p>
        ))}
      </div>
    )
  }
  return null
}

export default function Financial() {
  const [data, setData] = useState<FinancialData | null>(null)
  const [loading, setLoading] = useState(true)
  const [period, setPeriod] = useState<6 | 12>(6)

  useEffect(() => {
    setLoading(true)
    api.get(`/dashboard/financial?months=${period}`)
      .then(r => setData(r.data))
      .catch(() => setData(null))
      .finally(() => setLoading(false))
  }, [period])

  const revGrowth = data ? pct(data.revenue_total, data.revenue_last_month) : 0
  const monthlySlice = data?.monthly.slice(-period) ?? []

  return (
    <div className="flex flex-col h-full bg-surface-900 animate-fade-in">
      <Topbar
        title="Relatório Financeiro"
        subtitle="Receitas, conversão e clientes ativos"
        breadcrumb="Análise"
        action={
          <div className="flex rounded-lg overflow-hidden border border-surface-500">
            {([6, 12] as const).map(p => (
              <button
                key={p}
                onClick={() => setPeriod(p)}
                className={`px-3 py-1.5 text-xs font-medium transition-colors ${period === p ? 'bg-brand-600 text-white' : 'text-slate-400 hover:text-white hover:bg-surface-600'}`}
              >
                {p}M
              </button>
            ))}
          </div>
        }
      />

      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : !data ? (
          <div className="card p-8 text-center">
            <p className="text-slate-400">Não foi possível carregar os dados financeiros.</p>
          </div>
        ) : (
          <>
            {/* KPI Cards */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              <StatCard
                label="Receita Total (período)"
                value={fmt(data.revenue_total)}
                sub={`${revGrowth >= 0 ? '+' : ''}${revGrowth.toFixed(1)}% vs mês anterior`}
                positive={revGrowth >= 0}
                icon={<DollarSign className="w-5 h-5" />}
                color="bg-brand-600/15 text-brand-400"
              />
              <StatCard
                label="Orçamentos Confirmados"
                value={String(data.quotes_confirmed)}
                sub={`${data.quotes_done} concluídos`}
                icon={<FileText className="w-5 h-5" />}
                color="bg-emerald-500/15 text-emerald-400"
              />
              <StatCard
                label="Clientes Ativos"
                value={String(data.clients_active)}
                sub="com orçamentos no período"
                icon={<Users className="w-5 h-5" />}
                color="bg-sky-500/15 text-sky-400"
              />
              <StatCard
                label="Taxa de Conversão"
                value={`${data.conversion_rate.toFixed(1)}%`}
                sub="leads → orçamentos confirmados"
                positive={data.conversion_rate > 50}
                icon={<CheckCircle className="w-5 h-5" />}
                color="bg-violet-500/15 text-violet-400"
              />
            </div>

            {/* Charts row */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              {/* Revenue area chart */}
              <div className="card p-5 lg:col-span-2">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <p className="text-white font-semibold text-sm">Receita Mensal</p>
                    <p className="text-slate-500 text-xs mt-0.5">Últimos {period} meses</p>
                  </div>
                </div>
                <ResponsiveContainer width="100%" height={220}>
                  <AreaChart data={monthlySlice} margin={{ top: 5, right: 5, left: 0, bottom: 0 }}>
                    <defs>
                      <linearGradient id="revenueGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor={BRAND} stopOpacity={0.25} />
                        <stop offset="95%" stopColor={BRAND} stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid stroke="#232d42" strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="month" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                    <YAxis
                      tick={{ fill: '#64748b', fontSize: 11 }}
                      axisLine={false}
                      tickLine={false}
                      tickFormatter={v => `R$${v >= 1000 ? `${(v/1000).toFixed(0)}k` : v}`}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Area type="monotone" dataKey="revenue" stroke={BRAND} strokeWidth={2} fill="url(#revenueGrad)" dot={{ fill: BRAND, r: 3, strokeWidth: 0 }} activeDot={{ r: 5, fill: BRAND }} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              {/* Quotes bar chart */}
              <div className="card p-5">
                <div className="mb-4">
                  <p className="text-white font-semibold text-sm">Orçamentos / Mês</p>
                  <p className="text-slate-500 text-xs mt-0.5">Volume gerado</p>
                </div>
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={monthlySlice} margin={{ top: 5, right: 5, left: 0, bottom: 0 }}>
                    <CartesianGrid stroke="#232d42" strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="month" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} allowDecimals={false} />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar dataKey="quotes" radius={[4,4,0,0]}>
                      {monthlySlice.map((_, i) => (
                        <Cell key={i} fill={i === monthlySlice.length - 1 ? BRAND : '#2a3654'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Top Clients */}
            <div className="card">
              <div className="flex items-center justify-between px-5 py-4 border-b border-surface-600">
                <div>
                  <p className="text-white font-semibold text-sm">Top Clientes por Receita</p>
                  <p className="text-slate-500 text-xs mt-0.5">Período selecionado</p>
                </div>
                <span className="badge bg-brand-600/15 text-brand-400">{data.top_clients.length} clientes</span>
              </div>
              {data.top_clients.length === 0 ? (
                <p className="text-slate-500 text-sm text-center py-8">Sem dados no período</p>
              ) : (
                <div className="divide-y divide-surface-700">
                  {data.top_clients.map((c, i) => {
                    const pctOfTotal = data.revenue_total ? (c.total / data.revenue_total) * 100 : 0
                    return (
                      <div key={c.client_name} className="flex items-center gap-4 px-5 py-3 hover:bg-surface-700/30 transition-colors">
                        <div className="w-6 h-6 rounded-full bg-surface-700 flex items-center justify-center text-slate-400 text-xs font-bold shrink-0">
                          {i + 1}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-white text-sm font-medium truncate">{c.client_name}</p>
                          <p className="text-slate-500 text-xs">{c.quotes_count} orçamento{c.quotes_count !== 1 ? 's' : ''}</p>
                        </div>
                        <div className="flex items-center gap-3">
                          <div className="w-24 h-1.5 bg-surface-600 rounded-full overflow-hidden">
                            <div className="h-full rounded-full bg-brand-500" style={{ width: `${pctOfTotal}%` }} />
                          </div>
                          <span className="text-slate-400 text-xs w-8 text-right">{pctOfTotal.toFixed(0)}%</span>
                          <span className="text-white text-sm font-semibold w-24 text-right">{fmt(c.total)}</span>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
