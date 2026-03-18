import { useEffect, useState, useCallback } from 'react'
import {
  CalendarDays, Clock, MapPin, CheckCircle2, PlayCircle,
  Circle, RefreshCw, Ban, AlertCircle, ChevronDown, ChevronUp,
  ShieldCheck, Download, Phone, User,
} from 'lucide-react'
import api from '../../api/client'

interface Appointment {
  id: number
  client_id: number
  client_name: string | null
  client_phone: string | null
  client_address: string | null
  address_raw: string | null
  start_at: string
  end_at: string
  status: string
  service_type: string | null
  notes: string | null
  valor: number | null
  event_title: string | null
  has_warranty: boolean
  warranty_id: number | null
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
  scheduled: [{ status: 'in_progress', label: 'Iniciar', icon: PlayCircle, color: 'bg-amber-600 hover:bg-amber-700 active:bg-amber-800' }],
  in_progress: [{ status: 'completed', label: 'Concluir', icon: CheckCircle2, color: 'bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800' }],
  rescheduled: [{ status: 'in_progress', label: 'Iniciar', icon: PlayCircle, color: 'bg-amber-600 hover:bg-amber-700 active:bg-amber-800' }],
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
  const [generatingWarranty, setGeneratingWarranty] = useState<number | null>(null)

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

  async function updateStatus(id: number, newStatus: string) {
    setUpdating(id)
    try {
      await api.patch(`/installer/appointments/${id}/status`, { status: newStatus })
      showToast('success', `Status: ${STATUS_LABEL[newStatus] ?? newStatus}`)
      load()
    } catch {
      showToast('error', 'Erro ao atualizar status.')
    } finally {
      setUpdating(null)
    }
  }

  async function generateWarranty(id: number) {
    setGeneratingWarranty(id)
    try {
      await api.post(`/installer/appointments/${id}/warranty`)
      showToast('success', 'Garantia gerada! Faça o download abaixo.')
      load()
    } catch (err: any) {
      const detail = err?.response?.data?.detail ?? 'Erro ao gerar garantia.'
      showToast('error', detail)
    } finally {
      setGeneratingWarranty(null)
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
    <div className="flex flex-col h-full overflow-hidden">
      {/* Page header */}
      <div className="px-4 py-4 sm:px-6 sm:py-5 border-b border-surface-700 bg-surface-800 shrink-0">
        <h1 className="text-lg sm:text-xl font-bold text-white">Minha Agenda</h1>
        <p className="text-slate-400 text-xs sm:text-sm mt-0.5">Seus atendimentos de instalação</p>
      </div>

      <main className="flex-1 overflow-y-auto">
        <div className="p-4 sm:p-6 space-y-4">

          {/* Toast */}
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

          {/* Stats */}
          <div className="grid grid-cols-3 gap-2 sm:gap-4">
            <div className="card p-3 sm:p-4 flex items-center gap-2 sm:gap-3">
              <div className="w-8 h-8 sm:w-10 sm:h-10 bg-brand-500/15 rounded-xl flex items-center justify-center shrink-0">
                <CalendarDays className="w-4 h-4 text-brand-400" />
              </div>
              <div className="min-w-0">
                <p className="text-lg sm:text-xl font-bold text-white tabular-nums">{todayList.length}</p>
                <p className="text-slate-500 text-[10px] sm:text-xs">Hoje</p>
              </div>
            </div>
            <div className="card p-3 sm:p-4 flex items-center gap-2 sm:gap-3">
              <div className="w-8 h-8 sm:w-10 sm:h-10 bg-blue-500/15 rounded-xl flex items-center justify-center shrink-0">
                <Circle className="w-4 h-4 text-blue-400" />
              </div>
              <div className="min-w-0">
                <p className="text-lg sm:text-xl font-bold text-white tabular-nums">{pendingCount}</p>
                <p className="text-slate-500 text-[10px] sm:text-xs">Pendentes</p>
              </div>
            </div>
            <div className="card p-3 sm:p-4 flex items-center gap-2 sm:gap-3">
              <div className="w-8 h-8 sm:w-10 sm:h-10 bg-amber-500/15 rounded-xl flex items-center justify-center shrink-0">
                <RefreshCw className="w-4 h-4 text-amber-400" />
              </div>
              <div className="min-w-0">
                <p className="text-lg sm:text-xl font-bold text-white tabular-nums">{inProgressCount}</p>
                <p className="text-slate-500 text-[10px] sm:text-xs">Andamento</p>
              </div>
            </div>
          </div>

          {/* Filter tabs — scrollable on mobile */}
          <div className="flex items-center gap-1 bg-surface-800 border border-surface-600 rounded-xl p-1 overflow-x-auto no-scrollbar">
            {FILTER_TABS.map(tab => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`px-3 py-2 rounded-lg text-xs sm:text-sm font-medium transition-colors whitespace-nowrap flex-shrink-0 ${
                  activeTab === tab.key
                    ? 'bg-emerald-600 text-white'
                    : 'text-slate-400 hover:text-white hover:bg-surface-700'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Content */}
          {loading ? (
            <div className="flex items-center justify-center py-16">
              <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : appointments.length === 0 ? (
            <div className="card p-12 text-center">
              <div className="w-14 h-14 bg-surface-700 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <CalendarDays className="w-7 h-7 text-slate-500" />
              </div>
              <p className="text-white font-medium mb-1">Nenhum atendimento</p>
              <p className="text-slate-500 text-sm">
                {activeTab ? `Sem atendimentos "${STATUS_LABEL[activeTab]}".` : 'Seus próximos atendimentos aparecerão aqui.'}
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {todayList.length > 0 && (
                <section>
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-2 h-2 rounded-full bg-brand-400 animate-pulse" />
                    <h2 className="text-xs font-semibold text-brand-400 uppercase tracking-wide">Hoje</h2>
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
                        onGenerateWarranty={() => generateWarranty(a.id)}
                        updating={updating === a.id}
                        generatingWarranty={generatingWarranty === a.id}
                        highlight
                      />
                    ))}
                  </div>
                </section>
              )}

              {upcomingList.length > 0 && !activeTab && (
                <section>
                  <div className="flex items-center gap-2 mb-3">
                    <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wide">Próximos</h2>
                    <span className="text-xs text-slate-600">— {upcomingList.length}</span>
                  </div>
                  <div className="space-y-3">
                    {upcomingList.map(a => (
                      <AppointmentCard
                        key={a.id}
                        appt={a}
                        expanded={expanded.has(a.id)}
                        onToggle={() => toggleExpand(a.id)}
                        onAction={(s) => updateStatus(a.id, s)}
                        onGenerateWarranty={() => generateWarranty(a.id)}
                        updating={updating === a.id}
                        generatingWarranty={generatingWarranty === a.id}
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
                      onGenerateWarranty={() => generateWarranty(a.id)}
                      updating={updating === a.id}
                      generatingWarranty={generatingWarranty === a.id}
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
  appt, expanded, onToggle, onAction, onGenerateWarranty, updating, generatingWarranty, highlight,
}: {
  appt: Appointment
  expanded: boolean
  onToggle: () => void
  onAction: (status: string) => void
  onGenerateWarranty: () => void
  updating: boolean
  generatingWarranty: boolean
  highlight?: boolean
}) {
  const actions = NEXT_ACTIONS[appt.status] ?? []
  const address = appt.address_raw || appt.client_address

  function downloadPdf(e: React.MouseEvent) {
    e.stopPropagation()
    const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token') || ''
    const url = `/api/v1/installer/appointments/${appt.id}/warranty/pdf`
    const a = document.createElement('a')
    a.href = url
    a.download = `garantia-${appt.id}.pdf`
    // We rely on the cookie/bearer header set by the api client globally
    // Use fetch + blob to download with auth header
    fetch(url, { headers: token ? { Authorization: `Bearer ${token}` } : {} })
      .then(r => r.blob())
      .then(blob => {
        const blobUrl = URL.createObjectURL(blob)
        a.href = blobUrl
        a.click()
        URL.revokeObjectURL(blobUrl)
      })
  }

  return (
    <div className={`card overflow-hidden border ${highlight ? 'border-brand-500/40' : 'border-surface-600'}`}>
      <div className="flex items-stretch">
        {/* Status bar */}
        <div className={`w-1 shrink-0 ${STATUS_LEFT[appt.status] ?? 'bg-slate-600'}`} />

        <div className="flex-1 min-w-0">
          {/* Card header — tappable */}
          <div
            role="button"
            tabIndex={0}
            onClick={onToggle}
            onKeyDown={(e) => e.key === 'Enter' && onToggle()}
            className="flex items-center gap-3 p-4 cursor-pointer hover:bg-surface-700/30 active:bg-surface-700/50 transition-colors select-none"
          >
            <div className="flex-1 min-w-0">
              {/* Status badge + type */}
              <div className="flex items-center gap-2 mb-2 flex-wrap">
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
                {appt.has_warranty && (
                  <span className="inline-flex items-center gap-1 text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full">
                    <ShieldCheck className="w-3 h-3" />
                    Garantia
                  </span>
                )}
              </div>

              {/* Client name — most important for mobile */}
              {appt.client_name && (
                <div className="flex items-center gap-2 text-white text-sm font-semibold mb-1">
                  <User className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                  <span className="truncate">{appt.client_name}</span>
                </div>
              )}

              {/* Time */}
              <div className="flex items-center gap-2 text-slate-300 text-sm mb-1">
                <Clock className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                <span className="capitalize truncate">{formatDate(appt.start_at)}</span>
                <span className="text-slate-500 font-normal shrink-0">
                  {formatTime(appt.start_at)}–{formatTime(appt.end_at)}
                </span>
              </div>

              {/* Address */}
              {address && (
                <div className="flex items-center gap-2 text-slate-400 text-sm">
                  <MapPin className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                  <span className="truncate">{address}</span>
                </div>
              )}
            </div>

            {expanded
              ? <ChevronUp className="w-5 h-5 text-slate-500 shrink-0" />
              : <ChevronDown className="w-5 h-5 text-slate-500 shrink-0" />
            }
          </div>

          {/* Expanded detail */}
          {expanded && (
            <div className="px-4 pb-5 border-t border-surface-700/50 pt-4 space-y-4">

              {/* Client info */}
              {(appt.client_name || appt.client_phone) && (
                <div className="bg-surface-700/30 rounded-xl p-3 space-y-2">
                  <p className="text-slate-500 text-[10px] font-semibold uppercase tracking-wider">Cliente</p>
                  {appt.client_name && (
                    <div className="flex items-center gap-2">
                      <User className="w-4 h-4 text-slate-400 shrink-0" />
                      <span className="text-white text-sm font-medium">{appt.client_name}</span>
                    </div>
                  )}
                  {appt.client_phone && (
                    <a
                      href={`tel:${appt.client_phone}`}
                      className="flex items-center gap-2 text-brand-400 text-sm hover:text-brand-300 transition-colors"
                    >
                      <Phone className="w-4 h-4 shrink-0" />
                      {appt.client_phone}
                    </a>
                  )}
                  {address && (
                    <div className="flex items-start gap-2">
                      <MapPin className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
                      <span className="text-slate-300 text-sm">{address}</span>
                    </div>
                  )}
                </div>
              )}

              {/* Notes */}
              {appt.notes && (
                <p className="text-slate-400 text-sm leading-relaxed bg-surface-700/30 rounded-xl p-3">
                  {appt.notes}
                </p>
              )}

              {/* Valor */}
              {appt.valor && (
                <div className="flex items-center justify-between text-sm bg-surface-700/30 rounded-xl px-3 py-2.5">
                  <span className="text-slate-400">Valor do serviço</span>
                  <span className="text-emerald-400 font-bold tabular-nums">
                    {Number(appt.valor).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                  </span>
                </div>
              )}

              {/* Status actions — big buttons for mobile */}
              {actions.length > 0 && (
                <div className="flex flex-col sm:flex-row gap-2">
                  {actions.map(({ status, label, icon: Icon, color }) => (
                    <button
                      key={status}
                      onClick={() => onAction(status)}
                      disabled={updating}
                      className={`flex items-center justify-center gap-2 w-full px-4 py-3 sm:py-2.5 ${color} disabled:opacity-50 text-white text-sm font-semibold rounded-xl transition-colors`}
                    >
                      {updating
                        ? <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        : <Icon className="w-5 h-5" />
                      }
                      {label} atendimento
                    </button>
                  ))}
                </div>
              )}

              {/* Completed — warranty section */}
              {appt.status === 'completed' && (
                <div className="space-y-2 pt-1">
                  <div className="flex items-center gap-2 text-emerald-400 text-sm font-medium">
                    <CheckCircle2 className="w-4 h-4 shrink-0" />
                    Atendimento concluído
                  </div>

                  {appt.has_warranty ? (
                    <button
                      onClick={downloadPdf}
                      className="flex items-center justify-center gap-2 w-full px-4 py-3 bg-surface-700 hover:bg-surface-600 text-emerald-400 border border-emerald-500/30 text-sm font-semibold rounded-xl transition-colors"
                    >
                      <Download className="w-4 h-4" />
                      Baixar Certificado de Garantia
                    </button>
                  ) : (
                    <button
                      onClick={(e) => { e.stopPropagation(); onGenerateWarranty() }}
                      disabled={generatingWarranty}
                      className="flex items-center justify-center gap-2 w-full px-4 py-3 bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800 disabled:opacity-50 text-white text-sm font-semibold rounded-xl transition-colors"
                    >
                      {generatingWarranty
                        ? <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        : <ShieldCheck className="w-5 h-5" />
                      }
                      Gerar Garantia
                    </button>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
