import { useState, useEffect, useCallback } from 'react'
import Topbar from '../components/layout/Topbar'
import { GitBranch, Phone, MessageSquare, Calendar, ChevronRight, User, Search, RefreshCw } from 'lucide-react'
import api from '../api/client'

interface Client {
  id: number
  name: string
  phone: string
  stage: PipelineStage
  last_contact?: string
  quote_value?: number
  seller_name?: string
}

type PipelineStage = 'lead' | 'contacted' | 'visit' | 'quote_sent' | 'won' | 'lost'

interface Column {
  id: PipelineStage
  label: string
  color: string
  dot: string
}

const COLUMNS: Column[] = [
  { id: 'lead',        label: 'Lead',              color: 'bg-slate-500/15 text-slate-300',  dot: 'bg-slate-400' },
  { id: 'contacted',   label: 'Contactado',         color: 'bg-sky-500/15 text-sky-300',      dot: 'bg-sky-400' },
  { id: 'visit',       label: 'Visita Agendada',    color: 'bg-violet-500/15 text-violet-300',dot: 'bg-violet-400' },
  { id: 'quote_sent',  label: 'Orçamento Enviado',  color: 'bg-amber-500/15 text-amber-300',  dot: 'bg-amber-400' },
  { id: 'won',         label: 'Ganho',              color: 'bg-emerald-500/15 text-emerald-300', dot: 'bg-emerald-400' },
  { id: 'lost',        label: 'Perdido',            color: 'bg-red-500/15 text-red-400',      dot: 'bg-red-400' },
]

function fmt(v: number) {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }).format(v)
}

function fmtPhone(p: string) {
  const d = p.replace(/\D/g, '')
  if (d.length === 13) return `+${d.slice(0,2)} (${d.slice(2,4)}) ${d.slice(4,9)}-${d.slice(9)}`
  return p
}

// Stage is now computed server-side by GET /dashboard/crm


interface ClientCardProps {
  client: Client
  dotColor: string
}
function ClientCard({ client, dotColor }: ClientCardProps) {
  return (
    <div className="pipeline-card animate-fade-in">
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-center gap-2 min-w-0">
          <div className="w-7 h-7 rounded-full bg-brand-600/20 flex items-center justify-center text-brand-400 text-[10px] font-bold shrink-0">
            {client.name.split(' ').slice(0,2).map(w => w[0]).join('').toUpperCase()}
          </div>
          <p className="text-white text-xs font-semibold truncate">{client.name}</p>
        </div>
        <span className={`w-1.5 h-1.5 rounded-full shrink-0 mt-1.5 ${dotColor}`} />
      </div>
      <p className="text-slate-500 text-[10px] mb-2">{fmtPhone(client.phone)}</p>
      {client.quote_value !== undefined && client.quote_value > 0 && (
        <div className="flex items-center justify-between">
          <span className="text-[10px] text-slate-500">Valor</span>
          <span className="text-emerald-400 text-xs font-bold">{fmt(client.quote_value)}</span>
        </div>
      )}
      {client.seller_name && (
        <div className="flex items-center gap-1 mt-1.5">
          <User className="w-3 h-3 text-slate-600" />
          <span className="text-slate-500 text-[10px] truncate">{client.seller_name}</span>
        </div>
      )}
    </div>
  )
}

export default function CRM() {
  const [clients, setClients] = useState<Client[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')

  const load = useCallback(() => {
    setLoading(true)
    api.get('/dashboard/crm')
      .then(r => {
        const data: Client[] = (r.data.clients ?? []).map((c: any) => ({
          id: c.id,
          name: c.name,
          phone: c.phone ?? '',
          stage: c.stage as PipelineStage,
          quote_value: c.quote_value ?? 0,
          seller_name: undefined,
        }))
        setClients(data)
      })
      .catch(() => setClients([]))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => { load() }, [load])

  const filtered = clients.filter(c =>
    c.name.toLowerCase().includes(search.toLowerCase()) ||
    c.phone.includes(search)
  )

  const byStage = (stage: PipelineStage) => filtered.filter(c => c.stage === stage)

  const totalsByStage = COLUMNS.reduce((acc, col) => {
    acc[col.id] = clients.filter(c => c.stage === col.id).length
    return acc
  }, {} as Record<PipelineStage, number>)

  const totalClients = clients.length
  const wonCount = totalsByStage['won'] ?? 0
  const conversionRate = totalClients ? ((wonCount / totalClients) * 100).toFixed(1) : '0'

  return (
    <div className="flex flex-col h-full bg-surface-900 animate-fade-in">
      <Topbar
        title="CRM / Funil de Vendas"
        subtitle={`${totalClients} clientes • ${conversionRate}% conversão`}
        breadcrumb="Análise"
        action={
          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500" />
              <input
                className="input pl-8 py-1.5 text-xs w-44"
                placeholder="Buscar cliente..."
                value={search}
                onChange={e => setSearch(e.target.value)}
              />
            </div>
            <button onClick={load} className="btn-secondary py-1.5 px-2.5 flex items-center gap-1.5">
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>
        }
      />

      {/* Stage summary bar */}
      <div className="flex items-center gap-3 px-6 py-3 border-b border-surface-600 bg-surface-800 overflow-x-auto shrink-0">
        {COLUMNS.map((col, i) => (
          <div key={col.id} className="flex items-center gap-1.5 shrink-0">
            {i > 0 && <ChevronRight className="w-3 h-3 text-slate-600 mr-1" />}
            <span className={`badge ${col.color} gap-1`}>
              <span className={`w-1.5 h-1.5 rounded-full ${col.dot}`} />
              {col.label}
              <span className="font-bold ml-0.5">{totalsByStage[col.id] ?? 0}</span>
            </span>
          </div>
        ))}
      </div>

      {/* Kanban board */}
      <div className="flex-1 overflow-x-auto">
        <div className="flex gap-3 p-5 h-full min-w-max">
          {COLUMNS.map(col => {
            const cards = byStage(col.id)
            return (
              <div key={col.id} className="w-52 shrink-0 flex flex-col gap-2 h-full">
                {/* Column header */}
                <div className="flex items-center gap-2 px-1 mb-1 shrink-0">
                  <span className={`w-2 h-2 rounded-full ${col.dot}`} />
                  <span className="text-slate-300 text-xs font-semibold flex-1">{col.label}</span>
                  <span className="text-slate-500 text-xs">{cards.length}</span>
                </div>

                {/* Cards */}
                <div className="flex-1 overflow-y-auto space-y-2 pr-0.5">
                  {loading ? (
                    <div className="card p-4 flex items-center justify-center">
                      <div className="w-5 h-5 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
                    </div>
                  ) : cards.length === 0 ? (
                    <div className="card p-4 text-center">
                      <p className="text-slate-600 text-[10px]">Vazio</p>
                    </div>
                  ) : (
                    cards.map(c => (
                      <ClientCard key={c.id} client={c} dotColor={col.dot} />
                    ))
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Bottom: action shortcuts */}
      <div className="shrink-0 border-t border-surface-600 px-6 py-3 flex items-center gap-4 bg-surface-800">
        <span className="text-slate-500 text-xs">Ações rápidas:</span>
        <a href="tel:" className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors">
          <Phone className="w-3.5 h-3.5" />
          Ligar
        </a>
        <a href="/conversations" className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors">
          <MessageSquare className="w-3.5 h-3.5" />
          Conversar
        </a>
        <a href="/schedule" className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors">
          <Calendar className="w-3.5 h-3.5" />
          Agendar
        </a>
        <a href="/quotes" className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors">
          <GitBranch className="w-3.5 h-3.5" />
          Orçamentos
        </a>
      </div>
    </div>
  )
}
