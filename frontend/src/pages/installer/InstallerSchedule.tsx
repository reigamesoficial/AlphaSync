import { useEffect, useState, useCallback } from 'react'
import {
  CalendarDays, Clock, MapPin, CheckCircle2, PlayCircle,
  Circle, RefreshCw, Ban, AlertCircle, ChevronRight,
} from 'lucide-react'
import api from '../../api/client'

interface Appointment {
  id: number
  client_id: number
  address_raw: string | null
  start_at: string
  end_at: string
  status: string
  service_type: string | null
  notes: string | null
  valor: number | null
  event_title: string | null
}

const STATUS_LABEL: Record<string, string> = {
  scheduled: 'Agendado',
  in_progress: 'Em andamento',
  completed: 'Concluído',
  rescheduled: 'Reagendado',
  cancelled: 'Cancelado',
}

const STATUS_STYLE: Record<string, string> = {
  scheduled: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  in_progress: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  completed: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  rescheduled: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
  cancelled: 'bg-red-500/10 text-red-400 border-red-500/20',
}

const STATUS_LEFT: Record<string, string> = {
  scheduled: 'bg-blue-400',
  in_progress: 'bg-amber-400',
  completed: 'bg-emerald-400',
  rescheduled: 'bg-orange-400',
  cancelled: 'bg-red-400',
}

const NEXT_ACTIONS: Record<string, { status: string; label: string; icon: React.ElementType; color: string }[]> = {
  scheduled: [{ status: 'in_progress', label: 'Iniciar atendimento', icon: PlayCircle, color: 'bg-amber-600 hover:bg-amber-700' }],
  in_progress: [{ status: 'completed', label: 'Concluir atendimento', icon: CheckCircle2, color: 'bg-emerald-600 hover:bg-emerald-700' }],
  rescheduled: [{ status: 'in_progress', label: 'Iniciar atendimento', icon: PlayCircle, color: 'bg-amber-600 hover:bg-amber-700' }],
  completed: [],
  cancelled: [],
}

const FILTER_TABS = [
  { key: '', label: 'Todos' },
  { key: 'scheduled', label: 'Agendados' },
  { key: 'in_progress', label: 'Em andamento' },
  { key: 'completed', label: 'Concluídos' },
]

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('pt-BR', { weekday: 'long', day: '2-digit', month: 'long' })
}
function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
}
function isToday(iso: string) {
  const d = new Date(iso)
  const now = new Date()
  return d.getDate() === now.getDate() && d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear()
}
function isFuture(iso: string) {
  return new Date(iso) > new Date()
}

interface Toast { type: 'success' | 'error'; msg: string }

export default function InstallerSchedule() {
  const [appointments, setAppointments] = useState<Appointment[]>([])
  const [loading, setLoading] = useState(true)
  const [updating, setUpdating] = useState<number | null>(null)
  const [activeTab, setActiveTab] = useState('')
  const [toast, setToast] = useState<Toast | null>(null)
  const [expanded, setExpanded] = useState<Set<number>>(new Set())

  const showToast = (type: Toast['type'], msg: string) => {
    setToast({ type, msg })
    setTimeout(() => setToast(null), 4000)
  }

  const load = useCallback(() => {
    setLoading(true)
    const params: Record<string, string> = {}
    if (activeTab) params.status = activeTab
    api.get<Appointment[]>('/installer/appointments', { params })
      .then(r => setAppointments(r.data))
      .catch(() => showToast('error', 'Erro ao carregar atendimentos.'))
      .finally(() => setLoading(false))
  }, [activeTab])

  useEffect(() => { load() }, [load])

  async function updateStatus(id: number, status: string) {
    setUpdating(id)
    try {
      await api.patch(`/installer/appointments/${id}/status`, { status })
      showToast('success', `Status atualizado: ${STATUS_LABEL[status] ?? status}`)
      load()
    } catch {
      showToast('error', 'Erro ao atualizar status.')
    } finally {
      setUpdating(null)
    }
  }

  function toggleExpand(id: number) {
    setExpanded(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  const todayList = appointments.filter(a => isToday(a.start_at))
  const upcomingList = appointments.filter(a => !isToday(a.start_at) && isFuture(a.start_at))
  const pendingCount = appointments.filter(a => a.status === 'scheduled').length
  const inProgressCount = appointments.filter(a => a.status === 'in_progress').length

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      <div className="p-6 border-b border-surface-700 bg-surface-800">
        <h1 className="text-xl font-bold text-white">Minha Agenda</h1>
        <p className="text-slate-400 text-sm mt-0.5">Seus atendimentos de instalação</p>
      </div>

      <main className="flex-1 overflow-y-auto">
        <div className="p-6 space-y-5">

          {toast && (
            <div className={`flex items-center gap-2.5 px-4 py-3 rounded-xl text-sm font-medium ${
              toast.type === 'success'
                ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400'
                : 'bg-red-500/10 border border-red-500/20 text-red-400'
            }`}>
              <AlertCircle className="w-4 h-4 shrink-0" />
              {toast.msg}
            </div>
          )}

          <div className="grid grid-cols-3 gap-4">
            <div className="card p-4 flex items-center gap-3">
              <div className="w-10 h-10 bg-brand-500/15 rounded-xl flex items-center justify-center shrink-0">
                <CalendarDays className="w-4.5 h-4.5 text-brand-400" />
              </div>
              <div>
                <p className="text-xl font-bold text-white tabular-nums">{todayList.length}</p>
                <p className="text-slate-500 text-xs">Hoje</p>
              </div>
            </div>
            <div className="card p-4 flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-500/15 rounded-xl flex items-center justify-center shrink-0">
                <Circle className="w-4.5 h-4.5 text-blue-400" />
              </div>
              <div>
                <p className="text-xl font-bold text-white tabular-nums">{pendingCount}</p>
                <p className="text-slate-500 text-xs">Pendentes</p>
              </div>
            </div>
            <div className="card p-4 flex items-center gap-3">
              <div className="w-10 h-10 bg-amber-500/15 rounded-xl flex items-center justify-center shrink-0">
                <RefreshCw className="w-4.5 h-4.5 text-amber-400" />
              </div>
              <div>
                <p className="text-xl font-bold text-white tabular-nums">{inProgressCount}</p>
                <p className="text-slate-500 text-xs">Em andamento</p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-1 bg-surface-800 border border-surface-600 rounded-xl p-1 w-fit">
            {FILTER_TABS.map(tab => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors whitespace-nowrap ${
                  activeTab === tab.key
                    ? 'bg-emerald-600 text-white'
                    : 'text-slate-400 hover:text-white hover:bg-surface-700'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-16">
              <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : appointments.length === 0 ? (
            <div className="card p-16 text-center">
              <div className="w-14 h-14 bg-surface-700 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <CalendarDays className="w-7 h-7 text-slate-500" />
              </div>
              <p className="text-white font-medium mb-1">Nenhum atendimento encontrado</p>
              <p className="text-slate-500 text-sm">
                {activeTab ? `Não há atendimentos "${STATUS_LABEL[activeTab]}".` : 'Seus próximos atendimentos aparecerão aqui.'}
              </p>
            </div>
          ) : (
            <div className="space-y-5">
              {todayList.length > 0 && (
                <section>
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-2 h-2 rounded-full bg-brand-400 animate-pulse" />
                    <h2 className="text-sm font-semibold text-brand-400 uppercase tracking-wide">Hoje</h2>
                    <span className="text-xs text-slate-500">— {todayList.length} atendimento{todayList.length !== 1 ? 's' : ''}</span>
                  </div>
                  <div className="space-y-3">
                    {todayList.map(a => (
                      <AppointmentCard
                        key={a.id}
                        appt={a}
                        expanded={expanded.has(a.id)}
                        onToggle={() => toggleExpand(a.id)}
                        onAction={(s) => updateStatus(a.id, s)}
                        updating={updating === a.id}
                        highlight
                      />
                    ))}
                  </div>
                </section>
              )}

              {upcomingList.length > 0 && !activeTab && (
                <section>
                  <div className="flex items-center gap-2 mb-3">
                    <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wide">Próximos</h2>
                    <span className="text-xs text-slate-600">— {upcomingList.length} atendimento{upcomingList.length !== 1 ? 's' : ''}</span>
                  </div>
                  <div className="space-y-3">
                    {upcomingList.map(a => (
                      <AppointmentCard
                        key={a.id}
                        appt={a}
                        expanded={expanded.has(a.id)}
                        onToggle={() => toggleExpand(a.id)}
                        onAction={(s) => updateStatus(a.id, s)}
                        updating={updating === a.id}
                      />
                    ))}
                  </div>
                </section>
              )}

              {activeTab && (
                <div className="space-y-3">
                  {appointments.map(a => (
                    <AppointmentCard
                      key={a.id}
                      appt={a}
                      expanded={expanded.has(a.id)}
                      onToggle={() => toggleExpand(a.id)}
                      onAction={(s) => updateStatus(a.id, s)}
                      updating={updating === a.id}
                      highlight={isToday(a.start_at)}
                    />
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

function AppointmentCard({
  appt, expanded, onToggle, onAction, updating, highlight,
}: {
  appt: Appointment
  expanded: boolean
  onToggle: () => void
  onAction: (status: string) => void
  updating: boolean
  highlight?: boolean
}) {
  const actions = NEXT_ACTIONS[appt.status] ?? []

  return (
    <div className={`card overflow-hidden border ${
      highlight ? 'border-brand-500/40' : 'border-surface-600'
    }`}>
      <div className="flex items-stretch">
        <div className={`w-1 shrink-0 ${STATUS_LEFT[appt.status] ?? 'bg-slate-600'}`} />
        <div className="flex-1 min-w-0">
          <div
            role="button"
            tabIndex={0}
            onClick={onToggle}
            onKeyDown={(e) => e.key === 'Enter' && onToggle()}
            className="flex items-center gap-3 p-4 cursor-pointer hover:bg-surface-700/30 transition-colors select-none"
          >
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-2">
                <span className={`inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full font-medium border ${STATUS_STYLE[appt.status] ?? ''}`}>
                  {appt.status === 'scheduled' && <Circle className="w-3 h-3" />}
                  {appt.status === 'in_progress' && <RefreshCw className="w-3 h-3" />}
                  {appt.status === 'completed' && <CheckCircle2 className="w-3 h-3" />}
                  {appt.status === 'rescheduled' && <CalendarDays className="w-3 h-3" />}
                  {appt.status === 'cancelled' && <Ban className="w-3 h-3" />}
                  {STATUS_LABEL[appt.status] ?? appt.status}
                </span>
                {appt.service_type && (
                  <span className="text-xs text-slate-500 bg-surface-700 px-2 py-0.5 rounded-full">{appt.service_type}</span>
                )}
              </div>

              <div className="flex items-center gap-2 text-white text-sm font-medium mb-1">
                <Clock className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                <span className="capitalize">{formatDate(appt.start_at)}</span>
                <span className="text-slate-400 font-normal">
                  {formatTime(appt.start_at)} – {formatTime(appt.end_at)}
                </span>
              </div>

              {appt.address_raw && (
                <div className="flex items-center gap-2 text-slate-400 text-sm">
                  <MapPin className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                  <span className="truncate">{appt.address_raw}</span>
                </div>
              )}
            </div>

            <ChevronRight className={`w-4 h-4 text-slate-500 shrink-0 transition-transform duration-200 ${expanded ? 'rotate-90' : ''}`} />
          </div>

          {expanded && (
            <div className="px-4 pb-4 border-t border-surface-700/50 pt-3 space-y-3">
              {appt.notes && (
                <p className="text-slate-400 text-sm leading-relaxed bg-surface-700/30 rounded-xl p-3">
                  {appt.notes}
                </p>
              )}
              {appt.valor && (
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-500">Valor do serviço</span>
                  <span className="text-emerald-400 font-bold tabular-nums">
                    {Number(appt.valor).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                  </span>
                </div>
              )}
              {appt.event_title && (
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-500">Título</span>
                  <span className="text-slate-300">{appt.event_title}</span>
                </div>
              )}
              {actions.length > 0 && (
                <div className="flex gap-2 pt-1">
                  {actions.map(({ status, label, icon: Icon, color }) => (
                    <button
                      key={status}
                      onClick={() => onAction(status)}
                      disabled={updating}
                      className={`flex items-center gap-2 px-4 py-2 ${color} disabled:opacity-50 text-white text-sm font-medium rounded-xl transition-colors`}
                    >
                      {updating
                        ? <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        : <Icon className="w-4 h-4" />
                      }
                      {label}
                    </button>
                  ))}
                </div>
              )}
              {actions.length === 0 && appt.status === 'completed' && (
                <div className="flex items-center gap-2 text-emerald-400 text-sm">
                  <CheckCircle2 className="w-4 h-4" />
                  Atendimento concluído
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
