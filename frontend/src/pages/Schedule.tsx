import { useEffect, useState, useCallback } from 'react'
import {
  CalendarDays, Clock, MapPin, Plus, X, User, ChevronDown,
  AlertCircle, CheckCircle2, Circle, RefreshCw, Ban, Filter,
} from 'lucide-react'
import Topbar from '../components/layout/Topbar'
import { PageSpinner } from '../components/ui/Spinner'
import api from '../api/client'

interface Appointment {
  id: number
  client_id: number
  address_raw: string | null
  start_at: string
  end_at: string
  status: string
  service_type: string | null
  notes: string | null
  assigned_installer_id: number | null
  valor: number | null
  event_title: string | null
}

interface Client { id: number; name: string; phone: string | null }

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

const STATUS_DOT: Record<string, string> = {
  scheduled: 'bg-blue-400',
  in_progress: 'bg-amber-400',
  completed: 'bg-emerald-400',
  rescheduled: 'bg-orange-400',
  cancelled: 'bg-red-400',
}

const STATUS_ICON: Record<string, React.ReactNode> = {
  scheduled: <Circle className="w-3.5 h-3.5" />,
  in_progress: <RefreshCw className="w-3.5 h-3.5" />,
  completed: <CheckCircle2 className="w-3.5 h-3.5" />,
  rescheduled: <CalendarDays className="w-3.5 h-3.5" />,
  cancelled: <Ban className="w-3.5 h-3.5" />,
}

const FILTER_TABS = [
  { key: '', label: 'Todos' },
  { key: 'scheduled', label: 'Agendados' },
  { key: 'in_progress', label: 'Em andamento' },
  { key: 'completed', label: 'Concluídos' },
  { key: 'cancelled', label: 'Cancelados' },
]

interface NewApptForm {
  client_id: string
  start_at: string
  end_at: string
  service_type: string
  address_raw: string
  notes: string
}

const emptyForm: NewApptForm = {
  client_id: '', start_at: '', end_at: '', service_type: '', address_raw: '', notes: '',
}

interface Toast { type: 'success' | 'error'; msg: string }

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('pt-BR', { weekday: 'short', day: '2-digit', month: 'short' })
}
function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
}
function isToday(iso: string) {
  const d = new Date(iso)
  const now = new Date()
  return d.getDate() === now.getDate() && d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear()
}

export default function Schedule() {
  const [appointments, setAppointments] = useState<Appointment[]>([])
  const [clients, setClients] = useState<Client[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [form, setForm] = useState<NewApptForm>(emptyForm)
  const [saving, setSaving] = useState(false)
  const [toast, setToast] = useState<Toast | null>(null)

  const showToast = (type: Toast['type'], msg: string) => {
    setToast({ type, msg })
    setTimeout(() => setToast(null), 4000)
  }

  const load = useCallback(async () => {
    try {
      const params: Record<string, string> = {}
      if (activeTab) params.status = activeTab
      const res = await api.get<Appointment[]>('/appointments', { params })
      setAppointments(res.data)
    } catch {
      showToast('error', 'Erro ao carregar agendamentos.')
    } finally {
      setLoading(false)
    }
  }, [activeTab])

  useEffect(() => {
    setLoading(true)
    load()
  }, [load])

  useEffect(() => {
    api.get<Client[]>('/clients').then(r => setClients(r.data)).catch(() => {})
  }, [])

  async function handleCreate() {
    if (!form.client_id || !form.start_at || !form.end_at) return
    setSaving(true)
    try {
      await api.post('/appointments', {
        client_id: Number(form.client_id),
        start_at: form.start_at,
        end_at: form.end_at,
        service_type: form.service_type || undefined,
        address_raw: form.address_raw || undefined,
        notes: form.notes || undefined,
      })
      setShowModal(false)
      setForm(emptyForm)
      showToast('success', 'Agendamento criado com sucesso.')
      load()
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      showToast('error', msg || 'Erro ao criar agendamento.')
    } finally {
      setSaving(false)
    }
  }

  const todayCount = appointments.filter(a => isToday(a.start_at)).length
  const pendingCount = appointments.filter(a => a.status === 'scheduled').length
  const inProgressCount = appointments.filter(a => a.status === 'in_progress').length

  const clientMap = Object.fromEntries(clients.map(c => [c.id, c]))

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      <Topbar title="Agenda" subtitle="Agendamentos de instalação" />

      <main className="flex-1 overflow-y-auto p-6">
        <div className="max-w-5xl space-y-5">

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
            <div className="card p-5 flex items-center gap-4">
              <div className="w-11 h-11 bg-brand-500/15 rounded-xl flex items-center justify-center shrink-0">
                <CalendarDays className="w-5 h-5 text-brand-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white tabular-nums">{todayCount}</p>
                <p className="text-slate-400 text-sm">Hoje</p>
              </div>
            </div>
            <div className="card p-5 flex items-center gap-4">
              <div className="w-11 h-11 bg-blue-500/15 rounded-xl flex items-center justify-center shrink-0">
                <Circle className="w-5 h-5 text-blue-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white tabular-nums">{pendingCount}</p>
                <p className="text-slate-400 text-sm">Pendentes</p>
              </div>
            </div>
            <div className="card p-5 flex items-center gap-4">
              <div className="w-11 h-11 bg-amber-500/15 rounded-xl flex items-center justify-center shrink-0">
                <RefreshCw className="w-5 h-5 text-amber-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white tabular-nums">{inProgressCount}</p>
                <p className="text-slate-400 text-sm">Em andamento</p>
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-1 bg-surface-800 border border-surface-600 rounded-xl p-1">
              {FILTER_TABS.map(tab => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors whitespace-nowrap ${
                    activeTab === tab.key
                      ? 'bg-brand-600 text-white'
                      : 'text-slate-400 hover:text-white hover:bg-surface-700'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
            <button
              onClick={() => setShowModal(true)}
              className="btn-primary flex items-center gap-2 whitespace-nowrap"
            >
              <Plus className="w-4 h-4" />
              Novo agendamento
            </button>
          </div>

          {loading ? (
            <div className="flex justify-center py-16"><PageSpinner /></div>
          ) : appointments.length === 0 ? (
            <div className="card p-16 text-center">
              <div className="w-14 h-14 bg-surface-700 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <CalendarDays className="w-7 h-7 text-slate-500" />
              </div>
              <p className="text-white font-medium mb-1">Nenhum agendamento encontrado</p>
              <p className="text-slate-500 text-sm">
                {activeTab ? `Não há agendamentos com status "${STATUS_LABEL[activeTab]}".` : 'Clique em "Novo agendamento" para começar.'}
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {appointments.map(a => {
                const client = clientMap[a.client_id]
                const today = isToday(a.start_at)
                return (
                  <div key={a.id} className={`card p-0 overflow-hidden border ${today ? 'border-brand-500/30' : 'border-surface-600'}`}>
                    <div className="flex items-stretch">
                      <div className={`w-1 shrink-0 ${STATUS_DOT[a.status] ?? 'bg-slate-600'}`} />
                      <div className="flex-1 p-4 min-w-0">
                        <div className="flex items-start justify-between gap-3 mb-3">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className={`inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full font-medium border ${STATUS_STYLE[a.status] ?? 'bg-slate-700 text-slate-400 border-slate-600'}`}>
                              {STATUS_ICON[a.status]}
                              {STATUS_LABEL[a.status] ?? a.status}
                            </span>
                            {today && (
                              <span className="text-xs px-2 py-0.5 rounded-full bg-brand-500/15 text-brand-400 font-medium border border-brand-500/20">
                                Hoje
                              </span>
                            )}
                            {a.service_type && (
                              <span className="text-xs text-slate-500 bg-surface-700 px-2 py-0.5 rounded-full">
                                {a.service_type}
                              </span>
                            )}
                          </div>
                          <span className="text-slate-600 text-xs shrink-0">#{a.id}</span>
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-1.5">
                          <div className="flex items-center gap-2 text-slate-300 text-sm">
                            <Clock className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                            <span className="font-medium text-white">{formatDate(a.start_at)}</span>
                            <span className="text-slate-500">
                              {formatTime(a.start_at)} – {formatTime(a.end_at)}
                            </span>
                          </div>
                          {client && (
                            <div className="flex items-center gap-2 text-slate-300 text-sm">
                              <User className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                              <span>{client.name}</span>
                              {client.phone && <span className="text-slate-600 text-xs">{client.phone}</span>}
                            </div>
                          )}
                          {a.address_raw && (
                            <div className="flex items-center gap-2 text-slate-400 text-sm sm:col-span-2">
                              <MapPin className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                              <span className="truncate">{a.address_raw}</span>
                            </div>
                          )}
                        </div>

                        {a.notes && (
                          <p className="mt-2.5 pt-2.5 border-t border-surface-700 text-slate-500 text-xs leading-relaxed">
                            {a.notes}
                          </p>
                        )}
                      </div>

                      {a.valor && (
                        <div className="shrink-0 flex flex-col items-end justify-center px-4 border-l border-surface-700">
                          <p className="text-xs text-slate-500 mb-0.5">Valor</p>
                          <p className="text-white font-bold text-sm tabular-nums">
                            {Number(a.valor).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </main>

      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setShowModal(false)} />
          <div className="relative bg-surface-800 rounded-2xl border border-surface-600 w-full max-w-lg shadow-2xl">
            <div className="flex items-center justify-between p-5 border-b border-surface-600">
              <h3 className="text-white font-semibold">Novo agendamento</h3>
              <button onClick={() => setShowModal(false)} className="text-slate-500 hover:text-white transition-colors p-1 rounded-lg hover:bg-surface-700">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-5 space-y-4">
              <div>
                <label className="block text-slate-400 text-sm font-medium mb-1.5">Cliente *</label>
                <div className="relative">
                  <select
                    className="input appearance-none pr-8"
                    value={form.client_id}
                    onChange={(e) => setForm({ ...form, client_id: e.target.value })}
                  >
                    <option value="">Selecione o cliente</option>
                    {clients.map(c => (
                      <option key={c.id} value={String(c.id)}>{c.name}{c.phone ? ` — ${c.phone}` : ''}</option>
                    ))}
                  </select>
                  <ChevronDown className="w-4 h-4 text-slate-500 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 text-sm font-medium mb-1.5">Início *</label>
                  <input type="datetime-local" className="input" value={form.start_at} onChange={(e) => setForm({ ...form, start_at: e.target.value })} />
                </div>
                <div>
                  <label className="block text-slate-400 text-sm font-medium mb-1.5">Fim *</label>
                  <input type="datetime-local" className="input" value={form.end_at} onChange={(e) => setForm({ ...form, end_at: e.target.value })} />
                </div>
              </div>
              <div>
                <label className="block text-slate-400 text-sm font-medium mb-1.5">Tipo de serviço</label>
                <input className="input" placeholder="Ex: Instalação, Visita técnica..." value={form.service_type} onChange={(e) => setForm({ ...form, service_type: e.target.value })} />
              </div>
              <div>
                <label className="block text-slate-400 text-sm font-medium mb-1.5">Endereço</label>
                <input className="input" placeholder="Rua, número, bairro..." value={form.address_raw} onChange={(e) => setForm({ ...form, address_raw: e.target.value })} />
              </div>
              <div>
                <label className="block text-slate-400 text-sm font-medium mb-1.5">Observações</label>
                <textarea className="input min-h-[70px] resize-none" placeholder="Detalhes adicionais..." value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
              </div>
              <div className="flex gap-3 pt-1">
                <button onClick={() => setShowModal(false)} className="btn-secondary flex-1">Cancelar</button>
                <button
                  onClick={handleCreate}
                  disabled={saving || !form.client_id || !form.start_at || !form.end_at}
                  className="btn-primary flex-1 flex items-center justify-center gap-2"
                >
                  {saving ? <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : null}
                  {saving ? 'Salvando...' : 'Criar agendamento'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
